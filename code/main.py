"""
AlphaLens: Buy or Wait? — AI-Powered Financial Agent
HackerRank Orchestrate (September 2026)

Phase 2 Entrypoint: Financial State Reconstruction & 90-Day Cash-Flow Engine.
In Phase 2, deterministic daily cash-flow simulations over the 90-day horizon,
recurrence detection, message-derived amendments, and baseline forecasts are established.
Affordability optimization & plan selection will be implemented in Phase 3.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from alphalens.evaluation.cash_flow_evaluator import CashFlowEvaluator


def main():
    print("=" * 65)
    print("AlphaLens — HackerRank Orchestrate (September 2026)")
    print("Phase 2: Financial State Reconstruction & 90-Day Cash Flow Engine")
    print("=" * 65)
    print("Running cash flow & state evaluation...\n")
    evaluator = CashFlowEvaluator(dataset_dir="dataset")
    results = evaluator.evaluate()
    print(f"Requests Simulated:       {results['requests_simulated']}")
    print(f"Baseline Forecasts:       {results['baseline_forecasts_generated']}")
    print(f"Simulation Failures:      {results['forecast_failures']}")
    print(f"Projected Cash Flows:     {results['total_projected_flows']}")
    print(f"Confirmed Income Flows:   {results['total_confirmed_income_flows']}")
    print(f"Pending Credits Excluded: {results['total_pending_income_excluded']}")
    print(f"Invariant Violations:     {results['invariant_violations']}")
    print("\nFor full diagnostics, run: python3 code/evaluation/main.py")
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
