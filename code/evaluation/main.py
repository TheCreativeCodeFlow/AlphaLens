import sys
import os

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from alphalens.evaluation.evidence_evaluator import EvidenceEvaluator
from alphalens.evaluation.cash_flow_evaluator import CashFlowEvaluator


def main():
    print("=" * 70)
    print("HackerRank Orchestrate: Buy or Wait? — AlphaLens")
    print("PHASE 2 EVALUATION: FINANCIAL STATE & CASH-FLOW SIMULATION ENGINE")
    print("=" * 70)

    # 1. Phase 1 Evidence Evaluation
    print("\n[1/2] Evaluating Data Ingestion & Evidence Layer...")
    evidence_evaluator = EvidenceEvaluator(dataset_dir="dataset")
    ev_results = evidence_evaluator.evaluate()

    # 2. Phase 2 Cash Flow & State Evaluation
    print("[2/2] Running 90-Day Deterministic Cash Flow Simulation across all requests...")
    cash_evaluator = CashFlowEvaluator(dataset_dir="dataset")
    cf_results = cash_evaluator.evaluate()

    print(f"\n{'-' * 65}")
    print("PHASE 2 SIMULATION & STATE METRIC               VALUE")
    print(f"{'-' * 65}")
    print(f"Total evaluation & sample requests:             {cf_results['requests_simulated']}")
    print(f"Baseline 90-day forecasts generated:            {cf_results['baseline_forecasts_generated']}")
    print(f"Simulation forecast failures:                   {cf_results['forecast_failures']}")
    print(f"Baseline minimum-balance breaches detected:     {cf_results['baseline_violations_detected']}")
    print(f"Projected recurring cash flows generated:       {cf_results['total_projected_flows']}")
    print(f"Confirmed future income flows recognized:       {cf_results['total_confirmed_income_flows']}")
    print(f"Pending/uncertain credits properly excluded:    {cf_results['total_pending_income_excluded']}")
    print(f"Image-derived event amounts incorporated:       {cf_results['image_events_incorporated']}")
    print(f"Fixed dated currency conversions performed:     {cf_results['foreign_conversions_performed']}")
    print(f"Simulation timeline invariant violations:       {cf_results['invariant_violations']}")
    print(f"{'-' * 65}")

    print("\nSAMPLE REQUEST BASELINE DIAGNOSTICS (25 requests):")
    print(f"{'-' * 80}")
    print(f"REQ ID     USER      CUR   CURRENT BAL    PROT MIN   BASE MIN BAL  MIN DATE    STATUS")
    print(f"{'-' * 80}")
    for d in cf_results["sample_diagnostics"]:
        safe_str = "SAFE" if not d["violations"] else f"BREACH({len(d['violations'])}d)"
        print(
            f"{d['request_id']:10} {d['user_id']:9} {d['currency']:4} "
            f"{d['current_balance']:13,f} {d['protected_minimum']:11,f} "
            f"{d['baseline_minimum_balance']:13,f}  {d['baseline_minimum_date']}  {safe_str}"
        )
    print(f"{'-' * 80}")

    if cf_results["status"] == "PASS" and ev_results["validation_passed"]:
        print("\nOVERALL STATUS: PASS — Deterministic Financial State & 90-Day Cash Flow Engine operational.")
        print("Note: Affordability optimization & recommendation ranking will be built in Phase 3.\n")
        return 0
    else:
        print("\nOVERALL STATUS: FAIL — Discrepancies detected.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
