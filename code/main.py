"""
AlphaLens: Buy or Wait? — AI-Powered Financial Agent
HackerRank Orchestrate (September 2026)

Phase 1 Entrypoint: Data + Evidence Intelligence Layer.
In Phase 1, data ingestion, foreign exchange normalization, layout-aware OCR extraction,
multilingual message parsing, and request context hydration are established.
Affordability decision engine will be implemented in Phase 2.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from alphalens.evaluation.evidence_evaluator import EvidenceEvaluator


def main():
    print("=" * 60)
    print("AlphaLens — HackerRank Orchestrate (September 2026)")
    print("Phase 1: Data + Evidence Intelligence Layer")
    print("=" * 60)
    print("Running evidence intelligence evaluation...\n")
    evaluator = EvidenceEvaluator(dataset_dir="dataset")
    results = evaluator.evaluate()
    print(f"Total Financial Events:   {results["financial_events_loaded"]}")
    print(f"Extracted Image Amounts:  {results["missing_amounts_extracted"]}/16")
    print(f"Parsed Structured Facts:  {results["structured_financial_facts_extracted"]}/215")
    print(f"Hydrated Request Context: {results["requests_successfully_hydrated"]}/{results["total_requests"]}")
    print("\nFor full metrics, run: python3 code/evaluation/main.py")
    return 0 if results["validation_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
