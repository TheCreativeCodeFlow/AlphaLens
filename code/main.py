"""
AlphaLens: Buy or Wait? — AI-Powered Financial Agent
HackerRank Orchestrate (September 2026)

Production Entrypoint: Executes the complete end-to-end AlphaLens financial decision pipeline
for all 250 evaluation requests in dataset/requests.csv, validates the results against the strict
HackerRank output contract, and generates dataset/output.csv.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from alphalens.pipeline.production_runner import ProductionRunner


def main():
    print("=" * 70)
    print("AlphaLens — HackerRank Orchestrate (September 2026)")
    print("Production Pipeline: Financial Decision Agent & Output Generator")
    print("=" * 70)
    print("Executing full 250-request evaluation run against dataset/requests.csv...\n")

    runner = ProductionRunner(dataset_dir="dataset")
    count, md5_hash, is_valid, errors = runner.run(validate=True)

    print(f"\n{'-' * 70}")
    print("PRODUCTION RUN SUMMARY")
    print(f"{'-' * 70}")
    print(f"Total Requests Processed:     {count}")
    print(f"Output File:                  dataset/output.csv")
    print(f"Output SHA-256 / MD5 Hash:    {md5_hash}")
    print(f"Output Schema Compliance:     {'100% VALID' if is_valid else 'FAILED'}")
    print(f"{'-' * 70}")

    if not is_valid:
        print(f"\nERROR: Output validation failed with {len(errors)} error(s):")
        for err in errors[:10]:
            print(f"  - {err}")
        return 1

    print("\nAlphaLens production run completed successfully. output.csv is ready.")
    print("For multi-phase benchmark diagnostics, run: python3 code/evaluation/main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

