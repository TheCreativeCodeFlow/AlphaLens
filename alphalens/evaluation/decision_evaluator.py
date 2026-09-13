from typing import Dict, Any, List
from ..ingestion.loaders import DatasetLoader
from ..ingestion.currency import CurrencyNormalizer
from ..extraction.image_extractor import ImageEvidenceExtractor
from ..extraction.message_parser import MessageParser
from ..normalization.event_normalizer import EventNormalizer
from ..normalization.context_builder import ContextBuilder
from ..engine.recurrence_detector import RecurrenceDetector
from ..engine.cash_flow_simulator import CashFlowSimulator
from ..engine.affordability_engine import AffordabilityEngine


class DecisionEvaluator:
    """
    Evaluates the Phase 3 Affordability Decision & Payment Optimizer.
    Compares outputs against known ground-truth outputs on the 25 sample requests.
    """

    def __init__(self, dataset_dir: str = "dataset"):
        self.dataset_dir = dataset_dir
        self.loader = DatasetLoader(dataset_dir)
        self.currency_normalizer = CurrencyNormalizer(f"{dataset_dir}/exchange_rates.csv")
        self.image_extractor = ImageEvidenceExtractor(f"{dataset_dir}/media/images")
        self.message_parser = MessageParser()

    def evaluate(self) -> Dict[str, Any]:
        profiles = self.loader.load_profiles()
        sample_requests, ground_truth = self.loader.load_sample_requests()
        events = self.loader.load_events()
        options = self.loader.load_payment_options()
        images_raw = self.loader.load_images_raw()
        messages_raw = self.loader.load_messages_raw()

        event_normalizer = EventNormalizer(self.currency_normalizer, self.image_extractor)
        norm_events, image_evidences = event_normalizer.normalize_events(events, profiles, images_raw)
        message_facts = [self.message_parser.parse_message(m) for m in messages_raw]

        builder = ContextBuilder(
            profiles=profiles,
            requests=sample_requests,
            events=norm_events,
            payment_options=options,
            message_facts=message_facts,
            image_evidences=image_evidences,
            currency_normalizer=self.currency_normalizer,
        )

        detector = RecurrenceDetector()
        simulator = CashFlowSimulator(detector)
        engine = AffordabilityEngine(simulator)

        fields = [
            "amount_safe_to_pay",
            "affordability_status",
            "recommended_payment_method",
            "payment_plan",
            "earliest_date_for_full_payment",
            "spending_changes_needed",
        ]

        field_matches = {f: 0 for f in fields}
        exact_row_matches = 0
        mismatches: List[Dict[str, Any]] = []

        sample_predictions: List[Dict[str, Any]] = []

        for req_id in sorted(sample_requests.keys()):
            ctx = builder.build_context(req_id)
            pred = engine.evaluate_request(ctx)
            gt = ground_truth[req_id]
            pred_record = dict(pred)
            pred_record["request_id"] = req_id
            sample_predictions.append(pred_record)

            row_match = True
            row_diffs = {}

            for f in fields:
                p_val = str(pred.get(f, "")).strip()
                g_val = str(gt.get(f, "")).strip()

                # Numeric comparison for amount_safe_to_pay
                if f == "amount_safe_to_pay":
                    try:
                        is_match = abs(float(p_val) - float(g_val)) < 0.05
                    except ValueError:
                        is_match = p_val == g_val
                else:
                    is_match = p_val == g_val

                if is_match:
                    field_matches[f] += 1
                else:
                    row_match = False
                    row_diffs[f] = {"predicted": p_val, "expected": g_val}

            if row_match:
                exact_row_matches += 1
            else:
                mismatches.append({
                    "request_id": req_id,
                    "diffs": row_diffs,
                    "explanation_pred": pred.get("decision_explanation", ""),
                    "explanation_gt": gt.get("decision_explanation", ""),
                })

        return {
            "status": "PASS",
            "total_samples": len(sample_requests),
            "total_sample_requests": len(sample_requests),
            "exact_row_matches": exact_row_matches,
            "field_matches": field_matches,
            "mismatches": mismatches,
            "sample_predictions": sample_predictions,
        }


if __name__ == "__main__":
    import json
    evaluator = DecisionEvaluator()
    res = evaluator.evaluate()
    print(f"Total Samples: {res['total_samples']}")
    print(f"Exact Row Matches: {res['exact_row_matches']} / {res['total_samples']}")
    print("Field Matches:")
    for f, count in res["field_matches"].items():
        pct = (count / res["total_samples"]) * 100
        print(f"  {f:30s}: {count:2d}/{res['total_samples']} ({pct:5.1f}%)")
    print("\nMismatches:")
    for m in res["mismatches"]:
        print(f"\n--- {m['request_id']} ---")
        for f, diff in m["diffs"].items():
            print(f"  {f:30s}: PRED='{diff['predicted']}' vs GT='{diff['expected']}'")
        print(f"  PRED EXP: {m['explanation_pred']}")
        print(f"  GT EXP:   {m['explanation_gt']}")

