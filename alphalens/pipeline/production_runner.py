import csv
import hashlib
import os
import time
from typing import Dict, List, Any, Tuple, Optional
from ..ingestion.loaders import DatasetLoader
from ..ingestion.currency import CurrencyNormalizer
from ..extraction.image_extractor import ImageEvidenceExtractor
from ..extraction.message_parser import MessageParser
from ..normalization.event_normalizer import EventNormalizer
from ..normalization.context_builder import ContextBuilder
from ..engine.recurrence_detector import RecurrenceDetector
from ..engine.cash_flow_simulator import CashFlowSimulator
from ..engine.affordability_engine import AffordabilityEngine
from ..validation.output_validator import OutputValidator, REQUIRED_COLUMNS, OutputValidationError


class ProductionRunner:
    """
    End-to-end production runner for AlphaLens.
    Processes all 250 evaluation requests in dataset/requests.csv,
    determines optimal financial recommendations, writes dataset/output.csv,
    and runs the strict OutputValidator.
    """

    def __init__(self, dataset_dir: str = "dataset"):
        self.dataset_dir = dataset_dir
        self.loader = DatasetLoader(dataset_dir)
        self.currency_normalizer = CurrencyNormalizer(os.path.join(dataset_dir, "exchange_rates.csv"))
        self.image_extractor = ImageEvidenceExtractor(os.path.join(dataset_dir, "media", "images"))
        self.message_parser = MessageParser()

    def run(
        self, output_path: Optional[str] = None, validate: bool = True
    ) -> Tuple[int, str, bool, List[OutputValidationError]]:
        start_time = time.time()
        out_file = output_path or os.path.join(self.dataset_dir, "output.csv")

        # 1. Load data
        profiles = self.loader.load_profiles()
        requests = self.loader.load_requests()
        events = self.loader.load_events()
        options = self.loader.load_payment_options()
        images_raw = self.loader.load_images_raw()
        messages_raw = self.loader.load_messages_raw()

        # 2. Normalize and extract evidence
        event_normalizer = EventNormalizer(self.currency_normalizer, self.image_extractor)
        norm_events, image_evidences = event_normalizer.normalize_events(events, profiles, images_raw)
        message_facts = [self.message_parser.parse_message(m) for m in messages_raw]

        # 3. Build context builder
        builder = ContextBuilder(
            profiles=profiles,
            requests=requests,
            events=norm_events,
            payment_options=options,
            message_facts=message_facts,
            image_evidences=image_evidences,
            currency_normalizer=self.currency_normalizer,
        )

        # 4. Initialize engines
        detector = RecurrenceDetector()
        simulator = CashFlowSimulator(detector)
        engine = AffordabilityEngine(simulator)

        # 5. Evaluate all requests
        results: List[Dict[str, str]] = []
        for req_id in requests.keys():
            context = builder.build_context(req_id)
            eval_res = engine.evaluate_request(context)

            # Format amount_safe_to_pay to 2 decimal places if non-integer, else format clean
            amt_safe = eval_res["amount_safe_to_pay"]
            if isinstance(amt_safe, (int, float)):
                if float(amt_safe).is_integer():
                    amt_safe_str = str(int(amt_safe))
                else:
                    amt_safe_str = f"{amt_safe:.2f}".rstrip("0").rstrip(".") if f"{amt_safe:.2f}".endswith(".00") else f"{amt_safe:.2f}"
            else:
                amt_safe_str = str(amt_safe)

            row = {
                "request_id": eval_res["request_id"],
                "amount_safe_to_pay": amt_safe_str,
                "affordability_status": eval_res["affordability_status"],
                "recommended_payment_method": eval_res["recommended_payment_method"],
                "payment_plan": eval_res["payment_plan"],
                "earliest_date_for_full_payment": eval_res["earliest_date_for_full_payment"],
                "spending_changes_needed": eval_res["spending_changes_needed"],
                "decision_explanation": eval_res["decision_explanation"],
            }
            results.append(row)

        # 6. Write output.csv
        with open(out_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerows(results)

        # Synchronize root-level output.csv if writing to dataset/output.csv
        root_out_file = "output.csv"
        if os.path.abspath(out_file) != os.path.abspath(root_out_file):
            with open(root_out_file, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerows(results)

        # 7. Compute file hash
        with open(out_file, mode="rb") as f:
            md5_hash = hashlib.md5(f.read()).hexdigest()

        # 8. Validate output
        is_valid = True
        errors: List[OutputValidationError] = []
        if validate:
            validator = OutputValidator(
                profiles=profiles,
                requests=requests,
                events=norm_events,
                payment_options=options,
            )
            is_valid, errors = validator.validate_file(out_file, expected_count=len(requests))

        elapsed = time.time() - start_time
        print(f"Production pipeline finished: {len(results)} requests written to {out_file} in {elapsed:.2f}s (MD5: {md5_hash})")
        if not is_valid:
            print(f"Validation FAILED with {len(errors)} errors:")
            for err in errors[:10]:
                print(f"  {err}")
        else:
            print(f"Validation PASSED: 100% compliance with output schema and business logic.")

        return len(results), md5_hash, is_valid, errors


if __name__ == "__main__":
    runner = ProductionRunner()
    count, md5, valid, errors = runner.run()
    if not valid:
        exit(1)
