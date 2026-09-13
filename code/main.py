"""
AlphaLens: Buy or Wait? — AI-Powered Financial Agent
HackerRank Orchestrate (September 2026)

Phase 3 Entrypoint: Generalized Affordability Decision & Payment-Method Optimization Engine.
Evaluates requests against deterministic 90-day cash flow simulations, optimizes candidate payment
plans (full payment, installments, partial payment, wait, or rejection), generates bounded spending
changes, and produces grounded, audit-ready decision explanations.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from alphalens.evaluation.decision_evaluator import DecisionEvaluator


def main():
    print("=" * 70)
    print("AlphaLens — HackerRank Orchestrate (September 2026)")
    print("Phase 3: Generalized Affordability Decision & Payment-Method Optimizer")
    print("=" * 70)
    print("Evaluating Phase 3 decision engine against sample requests...\n")

    evaluator = DecisionEvaluator(dataset_dir="dataset")
    results = evaluator.evaluate()

    total = results["total_sample_requests"]
    fm = results["field_matches"]

    print(f"{'-' * 65}")
    print("PHASE 3 BENCHMARK METRIC                       MATCH RATE")
    print(f"{'-' * 65}")
    print(f"Recommended Payment Method Accuracy:           {fm['recommended_payment_method']}/{total} ({fm['recommended_payment_method']/total*100:.1f}%)")
    print(f"Payment Plan Schedule Accuracy:                {fm['payment_plan']}/{total} ({fm['payment_plan']/total*100:.1f}%)")
    print(f"Spending Changes Needed Accuracy:              {fm['spending_changes_needed']}/{total} ({fm['spending_changes_needed']/total*100:.1f}%)")
    print(f"Affordability Status Accuracy:                 {fm['affordability_status']}/{total} ({fm['affordability_status']/total*100:.1f}%)")
    print(f"Earliest Date For Full Payment Accuracy:       {fm['earliest_date_for_full_payment']}/{total} ({fm['earliest_date_for_full_payment']/total*100:.1f}%)")
    print(f"Amount Safe To Pay Accuracy:                   {fm['amount_safe_to_pay']}/{total} ({fm['amount_safe_to_pay']/total*100:.1f}%)")
    print(f"{'-' * 65}")
    print(f"Exact Row Matches (All 6 Fields Concurrently): {results['exact_row_matches']}/{total} ({results['exact_row_matches']/total*100:.1f}%)")
    print(f"{'-' * 65}")

    print("\nSAMPLE REQUEST RECOMMENDATION SUMMARY (First 10 Requests):")
    print(f"{'-' * 70}")
    print("REQ ID     STATUS               METHOD          AMOUNT SAFE    SPEND CHANGES")
    print(f"{'-' * 70}")
    for d in results["sample_predictions"][:10]:
        print(
            f"{d['request_id']:10} {d['affordability_status']:20} {d['recommended_payment_method']:15} "
            f"{str(d['amount_safe_to_pay']):14} {d['spending_changes_needed']}"
        )
    print(f"{'-' * 70}")
    print("\nFor full multi-phase diagnostics, run: python3 code/evaluation/main.py")
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
