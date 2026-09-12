import sys
import os

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from alphalens.evaluation.evidence_evaluator import EvidenceEvaluator


def main():
    print("=" * 60)
    print("HackerRank Orchestrate: Buy or Wait? — AlphaLens")
    print("PHASE 1 EVALUATION: DATA & EVIDENCE INTELLIGENCE LAYER")
    print("=" * 60)

    evaluator = EvidenceEvaluator(dataset_dir="dataset")
    results = evaluator.evaluate()

    print(f"\n{'-' * 45}")
    print("METRIC                                  VALUE")
    print(f"{'-' * 45}")
    print(f"Financial events loaded:                {results['financial_events_loaded']}")
    print(f"Events with missing amounts:            {results['events_with_missing_amounts']}")
    print(f"Missing amounts successfully extracted: {results['missing_amounts_extracted']}")
    print(f"Messages parsed:                        {results['messages_parsed']}")
    print(f"Structured financial facts extracted:   {results['structured_financial_facts_extracted']}")
    print(f"Requests successfully hydrated:         {results['requests_successfully_hydrated']}/{results['total_requests']}")
    print(f"Broken relationships:                   {results['broken_relationships']}")
    print(f"Unresolved evidence items:              {results['unresolved_evidence_items']}")
    print(f"Extraction failures:                    {results['extraction_failures']}")
    print(f"Validation failures:                    {results['validation_failures']}")
    print(f"Hydration failures:                     {results['hydration_failures']}")
    print(f"{'-' * 45}")

    if results["validation_passed"] and results["unresolved_evidence_items"] == 0:
        print("\nSTATUS: PASS — Data & evidence layer is fully normalized, verified, and traceable.")
        print("Note: Affordability decision engine will be built in Phase 2.\n")
        return 0
    else:
        print("\nSTATUS: FAIL — Discrepancies detected in evidence layer.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
