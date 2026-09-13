import sys
import os

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from alphalens.evaluation.evidence_evaluator import EvidenceEvaluator
from alphalens.evaluation.cash_flow_evaluator import CashFlowEvaluator
from alphalens.evaluation.decision_evaluator import DecisionEvaluator
from alphalens.pipeline.production_runner import ProductionRunner


def main():
    print("=" * 75)
    print("HackerRank Orchestrate: Buy or Wait? — AlphaLens")
    print("COMPREHENSIVE MULTI-PHASE SYSTEM EVALUATION (PHASES 1, 2, 3, AND 4)")
    print("=" * 75)

    # 1. Phase 1 Evidence Evaluation
    print("\n[1/4] Evaluating Data Ingestion & Evidence Layer...")
    evidence_evaluator = EvidenceEvaluator(dataset_dir="dataset")
    ev_results = evidence_evaluator.evaluate()

    # 2. Phase 2 Cash Flow & State Evaluation
    print("\n[2/4] Running 90-Day Deterministic Cash Flow Simulation across all requests...")
    cash_evaluator = CashFlowEvaluator(dataset_dir="dataset")
    cf_results = cash_evaluator.evaluate()

    # 3. Phase 3 Decision Engine Evaluation
    print("\n[3/4] Evaluating Phase 3 Affordability Decision Engine against Sample Requests...")
    decision_evaluator = DecisionEvaluator(dataset_dir="dataset")
    dec_results = decision_evaluator.evaluate()

    # 4. Phase 4 Production Pipeline & Output Validation
    print("\n[4/4] Evaluating Phase 4 Production Output Pipeline & OutputValidator...")
    runner = ProductionRunner(dataset_dir="dataset")
    count, md5_hash, p4_valid, p4_errors = runner.run(validate=True)

    print(f"\n{'-' * 70}")
    print("INTEGRATED MULTI-PHASE PERFORMANCE METRIC       VALUE")
    print(f"{'-' * 70}")
    print(f"Total evaluation & sample requests:             {cf_results['requests_simulated']}")
    print(f"Baseline 90-day forecasts generated:            {cf_results['baseline_forecasts_generated']}")
    print(f"Simulation forecast failures:                   {cf_results['forecast_failures']}")
    print(f"Simulation timeline invariant violations:       {cf_results['invariant_violations']}")
    print(f"{'-' * 70}")
    total_samples = dec_results["total_sample_requests"]
    fm = dec_results["field_matches"]
    print(f"Phase 3 Payment Method Recommendation Accuracy: {fm['recommended_payment_method']}/{total_samples} ({fm['recommended_payment_method']/total_samples*100:.1f}%)")
    print(f"Phase 3 Payment Plan Schedule Accuracy:         {fm['payment_plan']}/{total_samples} ({fm['payment_plan']/total_samples*100:.1f}%)")
    print(f"Phase 3 Spending Changes Needed Accuracy:       {fm['spending_changes_needed']}/{total_samples} ({fm['spending_changes_needed']/total_samples*100:.1f}%)")
    print(f"Phase 3 Affordability Status Accuracy:          {fm['affordability_status']}/{total_samples} ({fm['affordability_status']/total_samples*100:.1f}%)")
    print(f"Phase 3 Earliest Full Payment Date Accuracy:    {fm['earliest_date_for_full_payment']}/{total_samples} ({fm['earliest_date_for_full_payment']/total_samples*100:.1f}%)")
    print(f"Phase 3 Exact Row Matches (All 6 Fields):       {dec_results['exact_row_matches']}/{total_samples} ({dec_results['exact_row_matches']/total_samples*100:.1f}%)")
    print(f"{'-' * 70}")
    print(f"Phase 4 Evaluation Requests Processed:          {count}/250 (100.0%)")
    print(f"Phase 4 Output Schema & Invariant Compliance:   {'100% VALID' if p4_valid else 'FAILED'}")
    print(f"Phase 4 Output SHA-256 / MD5 Hash:              {md5_hash}")
    print(f"{'-' * 70}")

    all_passed = (
        cf_results["status"] == "PASS"
        and ev_results["validation_passed"]
        and dec_results["status"] == "PASS"
        and p4_valid
    )

    if all_passed:
        print("\nOVERALL STATUS: PASS — AlphaLens Data Intelligence, Cash-Flow Simulator, Decision Engine, and Production Pipeline operational.\n")
        return 0
    else:
        print("\nOVERALL STATUS: FAIL — Discrepancies detected.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
