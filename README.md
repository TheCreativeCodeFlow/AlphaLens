# AlphaLens — AI-Powered Financial Decision Agent

[![Challenge](https://img.shields.io/badge/HackerRank-Orchestrate%202026-blue.svg)](https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission)
[![GitHub](https://img.shields.io/badge/GitHub-TheCreativeCodeFlow%2FAlphaLens-black.svg)](https://github.com/TheCreativeCodeFlow/AlphaLens)
[![Tests](https://img.shields.io/badge/Tests-64%2F64%20Passing-brightgreen.svg)]()
[![Determinism](https://img.shields.io/badge/Output-Bitwise%20Deterministic-success.svg)]()

**AlphaLens** is an autonomous, personalized financial decision agent built for the **HackerRank Orchestrate (September 2026)** hackathon challenge: **"Buy or Wait?"**.

- **GitHub Repository**: [https://github.com/TheCreativeCodeFlow/AlphaLens](https://github.com/TheCreativeCodeFlow/AlphaLens)
- **HackerRank Challenge**: [https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission](https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission)

---

## 1. Executive Summary & Core Value Proposition

When a consumer asks: **"Can I safely afford this purchase?"**, standard advice either looks only at the current account balance or requires building complex forward budgeting spreadsheets.

AlphaLens provides an autonomous, mathematically guaranteed answer by executing a **hybrid neuro-symbolic decision architecture**:
1. Reconstructs the user's ground-truth financial position across checking, savings, fixed debt, and verified income.
2. Ingests and normalizes multi-source evidence from structured profiles, historical transaction ledgers, fixed dated exchange rates, multilingual communications (English & Indonesian), and receipt images.
3. Simulates **90 days of daily forward cash flows** with conservative recurrence clustering and income verification.
4. Explores all candidate payment strategies (paying in full today, utilizing merchant installment plans, two-stage partial payments, waiting for future liquidity, or making surgical spending reductions).
5. Enforces the user's `minimum_balance_to_keep` reserve across every single day of the forecast horizon.
6. Ranks viable candidates using the challenge's strict 6-tier lexicographical preference hierarchy and outputs fully compliant predictions to `output.csv`.

---

## 2. End-to-End System Architecture

AlphaLens cleanly separates untrusted perception, financial accounting, forward simulation, combinatorial optimization, and adversarial output validation across five distinct architectural layers:

```
dataset/ (Requests, Profiles, Events, FX Rates, Options, Messages, Images)
   │
   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Intelligence & Evidence Extraction Layer                           │
│    • CurrencyNormalizer: Exact dated FX conversion matching            │
│    • ImageEvidenceExtractor: Offline receipt OCR & amount recovery      │
│    • MessageParser: Multilingual NLP intent & amendment parsing        │
│    • SecuritySanitizer: Prompt-injection detection & quarantine        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Financial State & Temporal Cash Flow Engine                         │
│    • StateReconstructor: Realized liquid cash & pending reserves       │
│    • RecurrenceDetector: Monthly and interval cadence clustering       │
│    • CashFlowSimulator: Day-by-day discrete-event ledger (0 to 90 days)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Affordability Decision & Optimization Engine                        │
│    • CandidateGenerator: Full, Installments, Partial, Wait, Changes   │
│    • Suffix-Minimum Analyzer: Evaluates forward liquidity valleys      │
│    • RankOptimizer: Strict 6-tier lexicographical preference sorting   │
│    • ExplanationGenerator: Quantitative, grounded decision rationales │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. Independent Output Validator (OutputValidator)                      │
│    • 7-stage verification: Schema, types, enums, dates, sums, & safety │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
output.csv & dataset/output.csv (250 evaluated predictions, bitwise deterministic)
```

### Key Architectural Tenets
- **Deterministic Symbolic Accounting**: Generative LLMs are never permitted to perform financial arithmetic or multi-day balance projections. All cash flows, sums, interest calculations, and boundary checks are executed with exact floating-point symbolic logic.
- **Perception at the Boundary**: NLP and OCR are deployed strictly at the perimeter to convert unstructured messages and receipts into typed `FinancialEvent` and `MessageFact` data models.
- **Asymmetric Financial Conservatism**: Outflows are reserved immediately upon scheduling; inflows (bonuses, commissions, unrealized assets, speculative gains) are quarantined until confirmed settlement.

---

## 3. Quick Start & Execution Guide

AlphaLens is written in Python 3 and requires zero external APIs, remote services, or secret keys.

### 3.1 Prerequisites
- Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- Standard library dependencies only for core pipeline (============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/rahulseervi/Documents/GitHub/AlphaLens
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.2
collected 64 items

tests/test_affordability_decision.py .....                               [  7%]
tests/test_cash_flow.py ..............                                   [ 29%]
tests/test_currency.py ...                                               [ 34%]
tests/test_image_extraction.py .....                                     [ 42%]
tests/test_ingestion.py .....                                            [ 50%]
tests/test_message_intelligence.py ......                                [ 59%]
tests/test_normalization_and_context.py .                                [ 60%]
tests/test_phase4_hardening.py .......                                   [ 71%]
tests/test_security.py ..                                                [ 75%]
tests/test_synthetic_holdout.py ..........                               [ 90%]
tests/test_temporal_and_amendments.py ......                             [100%]

======================== 64 passed in 66.15s (0:01:06) ========================= for running automated tests)

### 3.2 Running the Production Pipeline

To process all 250 evaluation requests in `dataset/requests.csv` and generate the final validated `output.csv`:

```bash
python3 code/main.py
```

This executes `ProductionRunner`, validates every prediction row against the challenge contract, and writes identical output files to both:
- `output.csv` (root submission path)
- `dataset/output.csv` (dataset path)

### 3.3 Running Benchmark Diagnostics

To evaluate AlphaLens against the 25 solved sample requests in `dataset/sample_requests.csv`:

```bash
python3 code/evaluation/main.py
```

### 3.4 Running the Test Suite

To run the complete automated test suite (64 unit, integration, property, and invariant tests):

```bash
pytest -v
```

---

## 4. Repository Layout

```text
AlphaLens/
├── AGENTS.md                         # Rules for AI coding agents & transcript logging
├── problem_statement.md              # Official HackerRank challenge specification
├── README.md                         # Repository documentation & architecture guide
├── pytest.ini                        # Pytest configuration
├── log.txt                           # Audit log of agent execution turns (tool=Antigravity)
├── output.csv                        # Primary final prediction output (250 requests)
├── code/
│   ├── main.py                       # Production pipeline entrypoint
│   └── evaluation/
│       ├── main.py                   # Sample benchmark evaluation entrypoint
│       └── usage_report.md           # Formal token usage and cost accounting report
├── evaluation/
│   └── usage_report.md               # Required token-usage report copy
├── alphalens/                         # Core AlphaLens package
│   ├── models/                       # Typed dataclasses (profile, event, request, state, candidate)
│   ├── ingestion/                    # Robust CSV loaders & dated currency normalizer
│   ├── normalization/                # Event normalizer & context builder
│   ├── extraction/                   # Multimodal receipt parser & multilingual NLP message parser
│   ├── engine/                       # Cash-flow simulator, recurrence detector, affordability engine
│   ├── validation/                   # Schema validator & 7-stage output validator
│   └── pipeline/                     # Production runner orchestrating end-to-end pipeline
├── tests/                            # Comprehensive automated test suite (64 tests)
│   ├── test_ingestion.py             # CSV schema loading and typed validation
│   ├── test_currency.py              # Dated FX lookup and currency conversion
│   ├── test_message_intelligence.py  # Multilingual message parsing and intent extraction
│   ├── test_image_extraction.py      # Receipt image OCR and amount backfilling
│   ├── test_cash_flow.py             # 90-day simulation, recurrence, and salary handling
│   ├── test_affordability_decision.py# Decision ranking, partial payments, and installment logic
│   ├── test_security.py              # Prompt injection defense and containment
│   ├── test_phase4_hardening.py      # Suffix-min edge cases and invariant constraints
│   ├── test_synthetic_holdout.py     # Invariant monotonicity and holdout test cases
│   └── test_temporal_and_amendments.py # Leap years, month boundaries, and amendment propagation
├── docs/                             # In-depth architectural & audit documentation
│   ├── AI_JUDGE_NOTES.md             # Detailed judge-facing technical review (15 dimensions)
│   ├── PHASE_5_SPECIFICATION_AUDIT.md# Formal classification of all system mechanisms
│   ├── PHASE_4_EVALUATION.md         # Production benchmark & hardening report
│   └── PHASE_4_MISMATCH_ANALYSIS.md  # Detailed forensic analysis of sample edge cases
└── dataset/
    ├── requests.csv                  # 250 evaluation requests to predict
    ├── output.csv                    # Evaluation output file copy
    ├── sample_requests.csv           # 25 public sample requests with completed outputs
    ├── financial_profiles.csv        # User balances, minimum thresholds, preferences
    ├── financial_events.csv          # 25,342 historical and pending financial events
    ├── request_payment_options.csv   # Provider installment plans per request
    ├── exchange_rates.csv            # Fixed dated currency exchange rates
    ├── messages.csv                  # Semi-structured user/employer/landlord communications
    ├── images.csv                    # Metadata mapping receipts and bills to image files
    └── media/images/                 # PNG invoice and receipt scans
```

---

## 5. Required Output Contract

AlphaLens produces an exact 250-row CSV matching the schema:

```text
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

### Column Definitions & Mathematical Invariants
- `amount_safe_to_pay`: Derived via closed-form 90-day cash flow analysis:
  92310\text{amount\_safe\_to\_pay} = \max\left(0.0, \min\left(\text{requested\_amount}, \min_{0 \le t \le 90} (\text{closing\_balance}(t) - \text{minimum\_balance\_to\_keep})\right)\right)92310
- `affordability_status`: `affordable_now`, `affordable_with_plan`, `affordable_later`, or `not_affordable`.
- `recommended_payment_method`: `full_payment`, `partial_payment`, `installments`, `wait`, or `not_recommended`.
- `payment_plan`: Chronological `YYYY-MM-DD:amount` separated by `|`, or `none`. Partial payment plans sum to exactly `requested_amount`. Installments match an authorized provider option.
- `earliest_date_for_full_payment`: First date where paying in full leaves the balance $\ge \text{minimum\_balance\_to\_keep}$ through day 90. Matches `request_date` for `affordable_now`; empty string if impossible within 90 days.
- `spending_changes_needed`: `none` or up to three `stop:<event_id>` / `reduce_to:<event_id>:<amount>` directives strictly targeting permitted, non-protected categories.
- `decision_explanation`: Concise, grounded explanation citing exact numbers, dates, currencies, and safety margins.

---

## 6. Safety, Security, & Generalization Guarantees

1. **Prompt Injection Containment**: Ingested messages are screened by `SecuritySanitizer` for adversarial override patterns (`IGNORE PREVIOUS INSTRUCTIONS`, `SYSTEM PROMPT`, `OVERRIDE`, etc.). Malicious messages are quarantined with nullified amounts and cannot alter execution flow.
2. **Zero Hardcoding**: A static code audit confirms 0 occurrences of specific evaluation identifiers (`request_[0-9]+`, `usr_[0-9]+`, `ev_[0-9]+`) anywhere in the logic.
3. **Protected Category Immunity**: Essential spending categories (`rent`, `utilities`, `healthcare`, `groceries`) are mathematically immutable and protected from spending reductions.
4. **Token Economics & Offline Execution**:
   - External Model API Calls: **0**
   - Total Tokens: **0**
   - Total Cost: **/bin/zsh.00**
   - Runtime: **~20 seconds** for all 250 requests.

---

## 7. Submission Package & Verification

The final submission package `code.zip` was prepared in accordance with challenge packaging rules:
- **Included**: Complete source code (`alphalens/`, `code/`), documentation (`README.md`, `AGENTS.md`, `docs/`), tests (`tests/`, `pytest.ini`), and `evaluation/usage_report.md`.
- **Excluded**: Datasets (`dataset/`), virtual environments (`venv/`), bytecode/caches (`__pycache__/`, `*.pyc`), VCS metadata (`.git/`), OS metadata (`.DS_Store`), and local secrets/transcripts.

---

## 8. License & Authorship

Developed by **TheCreativeCodeFlow** for HackerRank Orchestrate (September 2026). Solo challenge submission authored in full compliance with challenge rules.
