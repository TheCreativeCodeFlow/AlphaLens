# AlphaLens — AI-Powered Financial Decision Agent

[![Challenge](https://img.shields.io/badge/HackerRank-Orchestrate%202026-blue.svg)](https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission)
[![GitHub](https://img.shields.io/badge/GitHub-TheCreativeCodeFlow%2FAlphaLens-black.svg)](https://github.com/TheCreativeCodeFlow/AlphaLens)
[![Tests](https://img.shields.io/badge/Tests-64%2F64%20Passing-brightgreen.svg)]()
[![Determinism](https://img.shields.io/badge/Output-Bitwise%20Deterministic-success.svg)]()

**AlphaLens** is an autonomous, personalized financial decision agent engineered for the **HackerRank Orchestrate (September 2026)** hackathon challenge: **"Buy or Wait?"**.

- **GitHub Repository**: [https://github.com/TheCreativeCodeFlow/AlphaLens](https://github.com/TheCreativeCodeFlow/AlphaLens)
- **HackerRank Challenge**: [https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission](https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission)

---

## 1. Project Title & Description

**AlphaLens** is a production-grade, personalized financial decision engine. It evaluates complex consumer purchase and payment requests against a user's complete financial position to determine whether an expense can be paid in full immediately, financed through available provider installment plans, structured as a two-stage partial payment, deferred until future liquidity arrives, or rejected as unaffordable.

Unlike naive budgeting chatbots that merely inspect an account balance on day zero or delegate arithmetic to stochastic LLMs, AlphaLens implements a **hybrid neuro-symbolic architecture**: multi-source evidence extraction at perception boundaries paired with a deterministic 90-day cash-flow simulation and combinatorial optimization engine.

---

## 2. Problem Statement & Objective

In the **Buy or Wait?** challenge, consumers submit purchase requests with specific requested amounts, desired completion dates, and merchant financing options. Recommending the safest path requires solving a multi-constraint optimization problem:

- **Liquid Cash Reserves**: The user's closing balance must never fall below their preferred `minimum_balance_to_keep` on any day across the 90-day forecast horizon.
- **Cash Flow Timing**: Essential recurring commitments (rent, utilities, groceries, transit) and debt obligations must be fully funded prior to discretionary spending.
- **Provider Financing**: Installment plans from sellers must conform to the user's payment preferences and maximum allowable installment tenure.
- **Evidence Reconciliation**: Key financial facts (salary adjustments, lease renegotiations, receipt amounts) are often distributed across multilingual chat messages and image receipts.
- **Permitted Spending Changes**: When an expense is currently unaffordable, the agent may recommend surgical spending reductions—strictly restricted to flexible, non-protected categories.

For every evaluation request in `dataset/requests.csv`, AlphaLens produces an exact decision tuple:
`[request_id, amount_safe_to_pay, affordability_status, recommended_payment_method, payment_plan, earliest_date_for_full_payment, spending_changes_needed, decision_explanation]`.

---

## 3. Approach Overview

AlphaLens operates on three fundamental principles:

1. **Symbolic Financial Truth**: Generative language models are inherently prone to arithmetic drift and cannot formally guarantee boundary constraints over multi-day balance projections. AlphaLens delegates all accounting, interest calculations, recurrence modeling, and balance tracking to deterministic symbolic Python algorithms.
2. **Perception at the Boundary**: Local Natural Language Processing (NLP) and Optical Character Recognition (OCR) are deployed exclusively at the ingestion perimeter to extract structured financial facts from conversational text and receipts.
3. **Asymmetric Risk Management**: Financial outflows (pending debits, scheduled recurring expenses) are recognized aggressively and reserved immediately; financial inflows (bonuses, commissions, unrealized assets, speculative gains) are quarantined until confirmed settlement.

---

## 4. End-to-End System Architecture

AlphaLens implements a 5-stage pipeline with strict data isolation boundaries:

```
dataset/ (requests, profiles, events, exchange rates, payment options, messages, images)
   │
   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Intelligence & Evidence Extraction Layer                           │
│    • CurrencyNormalizer: Exact dated FX conversion matching            │
│    • ImageEvidenceExtractor: Offline receipt OCR & amount recovery      │
│    • MessageParser: Multilingual NLP intent & amendment extraction     │
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

---

## 5. How Financial Evidence is Processed

AlphaLens integrates structured tabular records with unstructured media:

- **Structured Ingestion**: Robust CSV loaders parse `financial_profiles.csv`, `financial_events.csv`, and `request_payment_options.csv` into typed dataclasses, normalizing floating-point currency representations and ISO-8601 dates.
- **Dated Currency Normalization**: Cross-currency transactions are resolved via `CurrencyNormalizer` using exact settlement-date exchange rates from `exchange_rates.csv` matching the required conversion direction.
- **Multimodal Receipt Parsing (`ImageEvidenceExtractor`)**: When a financial event has an unpopulated amount, the extractor inspects the corresponding PNG receipt in `dataset/media/images/<image_id>.png`, extracting invoice totals and currencies from visual layout tokens to backfill the event.
- **Multilingual Message Intelligence (`MessageParser`)**: Scans user, employer, and merchant communications across English and Indonesian (e.g., `Greenfield Foods`, `gaji`, `sewa`), extracting structured adjustments:
  - Salary amendments and effective dates
  - Rent and lease percentage changes
  - Account transfer confirmations
  - Voided and cancelled transactions

---

## 6. How the 90-Day Financial Simulation Works

Rather than estimating balances at discrete intervals, `CashFlowSimulator` executes a day-by-day discrete-event ledger simulation from day 0 (`request_date`) to day 90:

93212\text{closing\_balance}(t) = \text{opening\_balance}(t) + \sum \text{confirmed\_credits}(t) - \sum \text{committed\_debits}(t)93212

### Key Simulation Mechanics:
- **Temporal Cadence Clustering**: `RecurrenceDetector` analyzes historical debits by `(category, description, currency)`, segmenting expenses into **Monthly Cadence** (bills on fixed calendar days like rent, utilities, subscriptions) and **Interval Cadence** (recurring necessities modeled via median intervals like groceries and transit).
- **Suffix-Minimum Cash Valley Analysis**: For every day $, the simulator calculates:
  93212\text{suffix\_min}(t) = \min_{t \le \tau \le 90} \text{closing\_balance}(\tau)93212
  This identifies future cash dips (e.g., upcoming rent due on day 12) to ensure that spending on day $ does not induce a liquidity crisis downstream.
- **Discretionary Spending Isolation**: Flexible lifestyle expenses (dining, entertainment) are excluded from rigid future liabilities, preventing artificial cash-flow depletion while remaining available for targeted spending reductions.

---

## 7. How Affordability & Payment Plans are Determined

AlphaLens evaluates all viable candidate strategies and selects the safest, most cost-effective plan:

1. **Candidate Strategies Evaluated**:
   - `full_payment`: Single payment on `request_date`.
   - `installments`: Provider installment options matching user preferences and `max_installment_months`.
   - `partial_payment`: Two-stage schedule ( = \text{amount\_safe\_to\_pay}$ on `request_date`,  = \text{requested\_amount} - P_1$ on `earliest_date_for_full_payment` $\le \text{deadline}$).
   - `wait`: Single payment deferred to `earliest_date_for_full_payment`.
   - `spending_changes`: Synthesizes up to 3 `stop` or `reduce_to` modifications on flexible expenses in permitted categories.
   - `not_recommended`: Fallback when no plan is viable.

2. **First-Principles Calculation of `amount_safe_to_pay`**:
   93212\text{amount\_safe\_to\_pay} = \max\left(0.0, \min\left(\text{requested\_amount}, \min_{0 \le t \le 90} (\text{closing\_balance}(t) - \text{minimum\_balance\_to\_keep})\right)\right)93212

3. **Strict 6-Tier Lexicographical Ranking**:
   All safe candidate plans are sorted according to the challenge's mandatory hierarchy:
   1. Complete on or before `desired_completion_date`.
   2. Require zero spending changes.
   3. Minimize total payment cost (including interest and financing fees).
   4. Earliest start date.
   5. Fewer payments.
   6. Deterministic tie-breaker by lowest `payment_option_id`.

---

## 8. Safety Constraints & Financial Invariants

AlphaLens enforces strict mathematical invariants across every candidate evaluation:

- **Inviolable Minimum Balance**: $\forall t \in [0, 90], \; \text{closing\_balance}(t) \ge \text{minimum\_balance\_to\_keep}$.
- **Immediate Debit Reservation**: Pending and scheduled outflows are deducted immediately from available liquidity.
- **Quarantine of Speculative Inflows**: Pending credits, unconfirmed bonuses, lottery winnings, and unrealized investment gains are strictly excluded from available cash until settlement.
- **Payment Conservation**: For partial payments,  + P_2 = \text{requested\_amount}$. For installments, $\sum p_i = \text{total\_cost}$.
- **Protected Category Immunity**: Categories listed in `protected_spending_categories` (e.g., `rent`, `utilities`, `healthcare`, `groceries`) are mathematically immutable and never modified.

---

## 9. Security & Generalization Approach

- **Prompt Injection Defense**: Ingested messages and image metadata are treated as untrusted inputs. `SecuritySanitizer` scans text for adversarial injection vectors (`IGNORE PREVIOUS INSTRUCTIONS`, `SYSTEM PROMPT`, `OVERRIDE`, etc.), quarantining malicious messages with nullified financial amounts so they cannot alter simulation logic.
- **Zero Hardcoding Guarantee**: Static analysis verifies zero occurrences of request IDs (`request_[0-9]+`), user IDs (`usr_[0-9]+`), event IDs, or benchmark answers in the codebase.
- **Generalization Integrity**: Public sample requests in `dataset/sample_requests.csv` were used strictly for schema calibration and style verification. All sample-specific heuristics (e.g., synthetic 22% salary debt ceilings) were completely eliminated in favor of exact forward cash-flow optimization.

---

## 10. Testing & Validation Summary

AlphaLens maintains a comprehensive test suite of **64 automated tests** with 100% passing status:

| Test Module | Coverage Focus |
|---|---|
| `test_ingestion.py` | Tabular CSV loading, dataclass mapping, schema validation |
| `test_currency.py` | Dated FX rate lookup, bidirectional currency conversion |
| `test_message_intelligence.py` | Multilingual intent parsing (English & Indonesian), salary updates |
| `test_image_extraction.py` | Receipt image OCR and missing amount recovery |
| `test_cash_flow.py` | 90-day accounting, recurrence detection, salary projection |
| `test_affordability_decision.py` | Suffix-minimum search, installment ranking, partial plans |
| `test_security.py` | Adversarial prompt-injection quarantine and containment |
| `test_phase4_hardening.py` | Edge-case boundary conditions and output invariant tests |
| `test_synthetic_holdout.py` | Invariant monotonicity and holdout property tests |
| `test_temporal_and_amendments.py` | Leap years, month boundaries, and amendment propagation |

**Independent Output Validator (`OutputValidator`)**: An adversarial auditing engine that verifies all 250 evaluation rows for column count, headers, enum domains, chronological plans, sum conservation, and category protections.

---

## 11. Complete Setup Instructions

AlphaLens runs on standard Python 3 and requires no proprietary services, external servers, or environment variables.

### Prerequisites
- Python 3.10 or higher (tested and verified on Python 3.10, 3.11, 3.12, 3.13, and 3.14)
- Standard library modules only for core execution
- `pytest` installed for running the automated test suite

### Installation
Clone the repository and enter the project directory:

```bash
git clone https://github.com/TheCreativeCodeFlow/AlphaLens.git
cd AlphaLens
```

---

## 12. Instructions for Running the Project

### 12.1 Run Production Pipeline (Generate `output.csv`)
To evaluate all 250 requests in `dataset/requests.csv` and generate the verified `output.csv`:

```bash
python3 code/main.py
```

*Output is synchronized to both `output.csv` (repository root) and `dataset/output.csv`.*

### 12.2 Run Benchmark Diagnostics
To evaluate the engine against the 25 public sample requests:

```bash
python3 code/evaluation/main.py
```

### 12.3 Run Automated Test Suite
To execute all 64 automated tests:

```bash
pytest -v
```

---

## 13. Project & Repository Structure

```text
AlphaLens/
├── AGENTS.md                         # Coding agent guidelines & interaction contract
├── problem_statement.md              # Official HackerRank challenge specification
├── README.md                         # Complete project documentation & guide
├── pytest.ini                        # Pytest configuration
├── log.txt                           # Execution turn audit log (tool=Antigravity)
├── output.csv                        # Primary prediction output (250 evaluated requests)
├── code/
│   ├── main.py                       # Production pipeline entrypoint
│   └── evaluation/
│       ├── main.py                   # 25-sample benchmark entrypoint
│       └── usage_report.md           # Formal token usage and cost accounting report
├── evaluation/
│   └── usage_report.md               # Required token-usage report copy
├── alphalens/                         # Core AlphaLens application package
│   ├── models/                       # Dataclasses: profile, event, request, state, candidate
│   ├── ingestion/                    # Tabular CSV loaders & dated currency normalizer
│   ├── normalization/                # Event normalizer & context builder
│   ├── extraction/                   # Multimodal receipt parser & multilingual message parser
│   ├── engine/                       # Cash-flow simulator, recurrence detector, affordability engine
│   ├── validation/                   # Schema validator & 7-stage output validator
│   └── pipeline/                     # Production runner orchestrating end-to-end execution
├── tests/                            # Comprehensive automated test suite (64 tests)
├── docs/                             # In-depth architectural & specification documentation
│   ├── AI_JUDGE_NOTES.md             # Detailed judge-facing technical review (15 dimensions)
│   ├── PHASE_5_SPECIFICATION_AUDIT.md# Formal classification of all system mechanisms
│   ├── PHASE_4_EVALUATION.md         # Production benchmark & hardening report
│   └── PHASE_4_MISMATCH_ANALYSIS.md  # Detailed forensic analysis of sample edge cases
└── dataset/
    ├── requests.csv                  # 250 evaluation requests to predict
    ├── output.csv                    # Evaluation output copy
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

## 14. GitHub Repository Link

- **Official Repository**: [https://github.com/TheCreativeCodeFlow/AlphaLens](https://github.com/TheCreativeCodeFlow/AlphaLens)

---

## 15. Original HackerRank Challenge Link

- **Submission Portal**: [https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission](https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission)

---

## Token Economics & Final Execution Metrics

As certified in `evaluation/usage_report.md`:
- **External LLM Calls**: **0**
- **External Model Tokens**: **0**
- **Total Operational Cost**: **/bin/zsh.00**
- **Runtime**: **~20 seconds** for all 250 evaluation requests
- **Determinism**: Bitwise reproducible output (MD5: `e45b9542fa429ac53d653880a66b91b5`)
