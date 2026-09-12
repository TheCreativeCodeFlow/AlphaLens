from typing import Dict, Any, List
from ..ingestion.loaders import DatasetLoader
from ..ingestion.currency import CurrencyNormalizer
from ..extraction.image_extractor import ImageEvidenceExtractor
from ..extraction.message_parser import MessageParser
from ..normalization.event_normalizer import EventNormalizer
from ..normalization.context_builder import ContextBuilder
from ..validation.schema_validator import SchemaValidator


class EvidenceEvaluator:
    """Evaluates the data ingestion, validation, and evidence extraction pipeline for Phase 1."""

    def __init__(self, dataset_dir: str = "dataset"):
        self.loader = DatasetLoader(dataset_dir)
        self.currency_normalizer = CurrencyNormalizer(f"{dataset_dir}/exchange_rates.csv")
        self.image_extractor = ImageEvidenceExtractor(f"{dataset_dir}/media/images")
        self.message_parser = MessageParser()
        self.validator = SchemaValidator(self.loader, self.currency_normalizer)

    def evaluate(self) -> Dict[str, Any]:
        # 1. Validation check
        validation_results = self.validator.validate_all()
        validation_failures = len(validation_results["errors"])
        broken_relationships = sum(1 for e in validation_results["errors"] if "broken" in e or "missing" in e)

        # 2. Ingestion
        profiles = self.loader.load_profiles()
        eval_requests = self.loader.load_requests("requests.csv")
        sample_requests, _ = self.loader.load_sample_requests()
        all_requests = {**eval_requests, **sample_requests}
        events = self.loader.load_events()
        options = self.loader.load_payment_options()
        images_raw = self.loader.load_images_raw()
        messages_raw = self.loader.load_messages_raw()

        events_with_missing_amounts = sum(1 for e in events.values() if e.amount is None)

        # 3. Message Extraction
        message_facts = []
        message_parse_failures = 0
        for m in messages_raw:
            try:
                fact = self.message_parser.parse_message(m)
                message_facts.append(fact)
            except Exception:
                message_parse_failures += 1

        # 4. Image Extraction & Event Normalization
        event_normalizer = EventNormalizer(self.currency_normalizer, self.image_extractor)
        norm_events, image_evidences = event_normalizer.normalize_events(events, profiles, images_raw)

        missing_amounts_extracted = len(image_evidences)
        unresolved_evidence_items = events_with_missing_amounts - missing_amounts_extracted

        # 5. Hydration
        builder = ContextBuilder(
            profiles=profiles,
            requests=all_requests,
            events=norm_events,
            payment_options=options,
            message_facts=message_facts,
            image_evidences=image_evidences,
            currency_normalizer=self.currency_normalizer,
        )

        hydrated_requests_count = 0
        hydration_failures = 0
        for req_id in all_requests:
            try:
                ctx = builder.build_context(req_id)
                if ctx:
                    hydrated_requests_count += 1
            except Exception:
                hydration_failures += 1

        return {
            "financial_events_loaded": len(events),
            "events_with_missing_amounts": events_with_missing_amounts,
            "missing_amounts_extracted": missing_amounts_extracted,
            "messages_parsed": len(message_facts),
            "structured_financial_facts_extracted": len(message_facts),
            "requests_successfully_hydrated": hydrated_requests_count,
            "total_requests": len(all_requests),
            "broken_relationships": broken_relationships,
            "unresolved_evidence_items": unresolved_evidence_items,
            "extraction_failures": message_parse_failures + unresolved_evidence_items,
            "validation_failures": validation_failures,
            "hydration_failures": hydration_failures,
            "validation_passed": validation_results["valid"],
        }
