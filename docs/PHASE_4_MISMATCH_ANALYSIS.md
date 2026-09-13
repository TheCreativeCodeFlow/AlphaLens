# AlphaLens: Phase 4 Benchmark Mismatch Analysis

This document details the exact diagnostic breakdown and generalized root causes for every benchmark mismatch observed across the 25 public sample requests.

---

## Request: `request_02` (user_02)
- **Requested Amount:** `46,018,000.00` IDR
- **Request Date:** `2025-08-05` | **Desired Completion Date:** `2025-10-10`
- **Current Balance:** `60,383,889.20` | **Minimum to Keep:** `29,158,400.00`
- **Payment Options Available:** `['payment_option_05', 'payment_option_06', 'payment_option_07']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `17229139.2`
- **Predicted:** `18005438.52`
- **Candidate Selected:** `installments`
- **Baseline Minimum Balance:** `47,163,838.52` on `2025-08-13`
- **Candidate Minimum Balance:** `31210931.85`
- **Earliest Safe Full Date Calculated:** `2025-09-15`
- **Desired Completion Date:** `2025-10-10`
- **Payment Options Considered:** `['payment_option_05', 'payment_option_06', 'payment_option_07']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary living expenses: omission of regular interval dining/groceries created a 776,299 IDR surplus margin in simulated cash flow before salary arrival on 2025-08-15.

---

## Request: `request_03` (user_03)
- **Requested Amount:** `5,491,000.00` IDR
- **Request Date:** `2019-09-03` | **Desired Completion Date:** `2019-11-15`
- **Current Balance:** `5,810,300.00` | **Minimum to Keep:** `2,668,700.00`
- **Payment Options Available:** `['payment_option_08', 'payment_option_09', 'payment_option_10']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `873000`
- **Predicted:** `1265316.86`
- **Candidate Selected:** `wait`
- **Baseline Minimum Balance:** `3,934,016.86` on `2019-09-14`
- **Candidate Minimum Balance:** `2668700.0`
- **Earliest Safe Full Date Calculated:** `2019-11-15`
- **Desired Completion Date:** `2019-11-15`
- **Payment Options Considered:** `['payment_option_08', 'payment_option_09', 'payment_option_10']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Discretionary category omission: excluding regular interval debits before next salary inflated pre-salary margin by 392,316 IDR above conservative capacity.

---

## Request: `request_04` (user_04)
- **Requested Amount:** `12,693,000.00` IDR
- **Request Date:** `2024-06-04` | **Desired Completion Date:** `2024-06-19`
- **Current Balance:** `52,206,950.00` | **Minimum to Keep:** `30,686,600.00`
- **Payment Options Available:** `['payment_option_11', 'payment_option_12']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `8401800`
- **Predicted:** `12693000`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `44,292,403.38` on `2024-06-12`
- **Candidate Minimum Balance:** `31599403.38`
- **Earliest Safe Full Date Calculated:** `2024-06-04`
- **Desired Completion Date:** `2024-06-19`
- **Payment Options Considered:** `['payment_option_11', 'payment_option_12']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Missing pre-salary commitments: excluding monthly entertainment tickets and recurring food delivery on the 13th led the model to underestimate pre-salary outflows by 4.29M IDR, falsely qualifying full payment today instead of waiting for salary on 2024-06-15.

### Field Mismatch: `affordability_status`
- **Expected:** `affordable_later`
- **Predicted:** `affordable_now`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `44,292,403.38` on `2024-06-12`
- **Candidate Minimum Balance:** `31599403.38`
- **Earliest Safe Full Date Calculated:** `2024-06-04`
- **Desired Completion Date:** `2024-06-19`
- **Payment Options Considered:** `['payment_option_11', 'payment_option_12']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Missing pre-salary commitments: excluding monthly entertainment tickets and recurring food delivery on the 13th led the model to underestimate pre-salary outflows by 4.29M IDR, falsely qualifying full payment today instead of waiting for salary on 2024-06-15.

### Field Mismatch: `recommended_payment_method`
- **Expected:** `wait`
- **Predicted:** `full_payment`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `44,292,403.38` on `2024-06-12`
- **Candidate Minimum Balance:** `31599403.38`
- **Earliest Safe Full Date Calculated:** `2024-06-04`
- **Desired Completion Date:** `2024-06-19`
- **Payment Options Considered:** `['payment_option_11', 'payment_option_12']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Missing pre-salary commitments: excluding monthly entertainment tickets and recurring food delivery on the 13th led the model to underestimate pre-salary outflows by 4.29M IDR, falsely qualifying full payment today instead of waiting for salary on 2024-06-15.

### Field Mismatch: `payment_plan`
- **Expected:** `2024-06-15:12693000`
- **Predicted:** `2024-06-04:12693000`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `44,292,403.38` on `2024-06-12`
- **Candidate Minimum Balance:** `31599403.38`
- **Earliest Safe Full Date Calculated:** `2024-06-04`
- **Desired Completion Date:** `2024-06-19`
- **Payment Options Considered:** `['payment_option_11', 'payment_option_12']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Missing pre-salary commitments: excluding monthly entertainment tickets and recurring food delivery on the 13th led the model to underestimate pre-salary outflows by 4.29M IDR, falsely qualifying full payment today instead of waiting for salary on 2024-06-15.

### Field Mismatch: `earliest_date_for_full_payment`
- **Expected:** `2024-06-15`
- **Predicted:** `2024-06-04`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `44,292,403.38` on `2024-06-12`
- **Candidate Minimum Balance:** `31599403.38`
- **Earliest Safe Full Date Calculated:** `2024-06-04`
- **Desired Completion Date:** `2024-06-19`
- **Payment Options Considered:** `['payment_option_11', 'payment_option_12']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Missing pre-salary commitments: excluding monthly entertainment tickets and recurring food delivery on the 13th led the model to underestimate pre-salary outflows by 4.29M IDR, falsely qualifying full payment today instead of waiting for salary on 2024-06-15.

---

## Request: `request_05` (user_05)
- **Requested Amount:** `15,488.00` ZAR
- **Request Date:** `2025-11-06` | **Desired Completion Date:** `2026-01-12`
- **Current Balance:** `46,475.10` | **Minimum to Keep:** `13,100.00`
- **Payment Options Available:** `['payment_option_13', 'payment_option_14', 'payment_option_15']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `737`
- **Predicted:** `0`
- **Candidate Selected:** `not_recommended`
- **Baseline Minimum Balance:** `9,773.93` on `2026-02-04`
- **Candidate Minimum Balance:** `0.0`
- **Earliest Safe Full Date Calculated:** ``
- **Desired Completion Date:** `2026-01-12`
- **Payment Options Considered:** `['payment_option_13', 'payment_option_14', 'payment_option_15']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Baseline breach handling: user experiences an unavoidable baseline deficit on day 88; simulator treated pre-salary safe amount as zero instead of the conservative 5% salary liquidity margin safe today.

---

## Request: `request_06` (user_06)
- **Requested Amount:** `620.40` EUR
- **Request Date:** `2026-01-03` | **Desired Completion Date:** `2026-01-14`
- **Current Balance:** `1,942.40` | **Minimum to Keep:** `800.00`
- **Payment Options Available:** `['payment_option_16', 'payment_option_17', 'payment_option_18']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `603.3`
- **Predicted:** `620.40`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `1,459.94` on `2026-01-13`
- **Candidate Minimum Balance:** `839.54`
- **Earliest Safe Full Date Calculated:** `2026-01-03`
- **Desired Completion Date:** `2026-01-14`
- **Payment Options Considered:** `['payment_option_16', 'payment_option_17', 'payment_option_18']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary cash margin & spending changes: missing regular Sunday dining outflows caused amount_safe_to_pay to be overestimated as 620.40 (instead of 603.30), bypassing the need to stop family streaming plan (event_476).

### Field Mismatch: `affordability_status`
- **Expected:** `affordable_with_plan`
- **Predicted:** `affordable_now`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `1,459.94` on `2026-01-13`
- **Candidate Minimum Balance:** `839.54`
- **Earliest Safe Full Date Calculated:** `2026-01-03`
- **Desired Completion Date:** `2026-01-14`
- **Payment Options Considered:** `['payment_option_16', 'payment_option_17', 'payment_option_18']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary cash margin & spending changes: missing regular Sunday dining outflows caused amount_safe_to_pay to be overestimated as 620.40 (instead of 603.30), bypassing the need to stop family streaming plan (event_476).

### Field Mismatch: `earliest_date_for_full_payment`
- **Expected:** `2026-01-15`
- **Predicted:** `2026-01-03`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `1,459.94` on `2026-01-13`
- **Candidate Minimum Balance:** `839.54`
- **Earliest Safe Full Date Calculated:** `2026-01-03`
- **Desired Completion Date:** `2026-01-14`
- **Payment Options Considered:** `['payment_option_16', 'payment_option_17', 'payment_option_18']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary cash margin & spending changes: missing regular Sunday dining outflows caused amount_safe_to_pay to be overestimated as 620.40 (instead of 603.30), bypassing the need to stop family streaming plan (event_476).

### Field Mismatch: `spending_changes_needed`
- **Expected:** `stop:event_476`
- **Predicted:** `none`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `1,459.94` on `2026-01-13`
- **Candidate Minimum Balance:** `839.54`
- **Earliest Safe Full Date Calculated:** `2026-01-03`
- **Desired Completion Date:** `2026-01-14`
- **Payment Options Considered:** `['payment_option_16', 'payment_option_17', 'payment_option_18']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary cash margin & spending changes: missing regular Sunday dining outflows caused amount_safe_to_pay to be overestimated as 620.40 (instead of 603.30), bypassing the need to stop family streaming plan (event_476).

---

## Request: `request_07` (user_07)
- **Requested Amount:** `197,400.00` INR
- **Request Date:** `2024-09-05` | **Desired Completion Date:** `2024-11-14`
- **Current Balance:** `218,945.56` | **Minimum to Keep:** `93,000.00`
- **Payment Options Available:** `['payment_option_19', 'payment_option_20', 'payment_option_21']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `87170.56`
- **Predicted:** `92870.95`
- **Candidate Selected:** `installments`
- **Baseline Minimum Balance:** `185,870.95` on `2024-09-20`
- **Candidate Minimum Balance:** `117438.96`
- **Earliest Safe Full Date Calculated:** `2024-10-23`
- **Desired Completion Date:** `2024-11-14`
- **Payment Options Considered:** `['payment_option_19', 'payment_option_20', 'payment_option_21']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Interval grocery and transport cadence: slight variation in interval projection dates shifted safe cash valley by 5,700 ZAR.

---

## Request: `request_08` (user_08)
- **Requested Amount:** `996.60` EUR
- **Request Date:** `2025-02-07` | **Desired Completion Date:** `2025-04-15`
- **Current Balance:** `1,536.57` | **Minimum to Keep:** `800.00`
- **Payment Options Available:** `['payment_option_22', 'payment_option_23']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `284.57`
- **Predicted:** `347.35`
- **Candidate Selected:** `wait`
- **Baseline Minimum Balance:** `1,147.35` on `2025-02-12`
- **Candidate Minimum Balance:** `800.0`
- **Earliest Safe Full Date Calculated:** `2025-04-15`
- **Desired Completion Date:** `2025-04-15`
- **Payment Options Considered:** `['payment_option_22', 'payment_option_23']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Discretionary projection vs temporary salary drop: single-payslip salary reduction combined with interval expenses produced a 62.78 EUR difference in safe margin.

---

## Request: `request_10` (user_10)
- **Requested Amount:** `266,700.00` INR
- **Request Date:** `2024-12-06` | **Desired Completion Date:** `2025-02-10`
- **Current Balance:** `750,155.00` | **Minimum to Keep:** `225,400.00`
- **Payment Options Available:** `['payment_option_27', 'payment_option_28']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `12700`
- **Predicted:** `39095.33`
- **Candidate Selected:** `not_recommended`
- **Baseline Minimum Balance:** `264,495.33` on `2025-03-06`
- **Candidate Minimum Balance:** `0.0`
- **Earliest Safe Full Date Calculated:** ``
- **Desired Completion Date:** `2025-02-10`
- **Payment Options Considered:** `['payment_option_27', 'payment_option_28']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Gig income cadence: driver payout was halted due to pending message, but conservative 5% liquidity allowance was not recognized for amount_safe_to_pay.

---

## Request: `request_11` (user_11)
- **Requested Amount:** `13,110,000.00` IDR
- **Request Date:** `2025-05-03` | **Desired Completion Date:** `2025-06-12`
- **Current Balance:** `63,531,795.00` | **Minimum to Keep:** `34,140,600.00`
- **Payment Options Available:** `['payment_option_29', 'payment_option_30', 'payment_option_31', 'payment_option_32']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `12510645`
- **Predicted:** `13110000`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `47,695,265.50` on `2025-05-14`
- **Candidate Minimum Balance:** `34585265.5`
- **Earliest Safe Full Date Calculated:** `2025-05-03`
- **Desired Completion Date:** `2025-06-12`
- **Payment Options Considered:** `['payment_option_29', 'payment_option_30', 'payment_option_31', 'payment_option_32']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Discretionary dining exclusion: event_989 was classified under dining, which was completely excluded from recurrence detection, preventing the engine from recommending reduce_to:event_989:665950.

### Field Mismatch: `affordability_status`
- **Expected:** `affordable_with_plan`
- **Predicted:** `affordable_now`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `47,695,265.50` on `2025-05-14`
- **Candidate Minimum Balance:** `34585265.5`
- **Earliest Safe Full Date Calculated:** `2025-05-03`
- **Desired Completion Date:** `2025-06-12`
- **Payment Options Considered:** `['payment_option_29', 'payment_option_30', 'payment_option_31', 'payment_option_32']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Discretionary dining exclusion: event_989 was classified under dining, which was completely excluded from recurrence detection, preventing the engine from recommending reduce_to:event_989:665950.

### Field Mismatch: `earliest_date_for_full_payment`
- **Expected:** `2025-07-15`
- **Predicted:** `2025-05-03`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `47,695,265.50` on `2025-05-14`
- **Candidate Minimum Balance:** `34585265.5`
- **Earliest Safe Full Date Calculated:** `2025-05-03`
- **Desired Completion Date:** `2025-06-12`
- **Payment Options Considered:** `['payment_option_29', 'payment_option_30', 'payment_option_31', 'payment_option_32']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Discretionary dining exclusion: event_989 was classified under dining, which was completely excluded from recurrence detection, preventing the engine from recommending reduce_to:event_989:665950.

### Field Mismatch: `spending_changes_needed`
- **Expected:** `reduce_to:event_989:665950`
- **Predicted:** `none`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `47,695,265.50` on `2025-05-14`
- **Candidate Minimum Balance:** `34585265.5`
- **Earliest Safe Full Date Calculated:** `2025-05-03`
- **Desired Completion Date:** `2025-06-12`
- **Payment Options Considered:** `['payment_option_29', 'payment_option_30', 'payment_option_31', 'payment_option_32']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Discretionary dining exclusion: event_989 was classified under dining, which was completely excluded from recurrence detection, preventing the engine from recommending reduce_to:event_989:665950.

---

## Request: `request_13` (user_13)
- **Requested Amount:** `941.60` EUR
- **Request Date:** `2024-03-07` | **Desired Completion Date:** `2024-05-15`
- **Current Balance:** `2,789.52` | **Minimum to Keep:** `1,300.00`
- **Payment Options Available:** `['payment_option_36', 'payment_option_37', 'payment_option_38']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `433.4`
- **Predicted:** `941.60`
- **Candidate Selected:** `wait`
- **Baseline Minimum Balance:** `2,204.79` on `2024-05-14`
- **Candidate Minimum Balance:** `1350.19`
- **Earliest Safe Full Date Calculated:** `2024-05-15`
- **Desired Completion Date:** `2024-05-15`
- **Payment Options Considered:** `['payment_option_36', 'payment_option_37', 'payment_option_38']`
- **Spending Changes Considered:** `stop:event_1090`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary living expense cadence: regular weekly dining and transport debits before 2024-03-15 salary were not deducted, inflating amount_safe_to_pay by 508.20 EUR.

---

## Request: `request_14` (user_14)
- **Requested Amount:** `5,414.20` EUR
- **Request Date:** `2025-08-04` | **Desired Completion Date:** `2025-10-04`
- **Current Balance:** `3,931.74` | **Minimum to Keep:** `2,200.00`
- **Payment Options Available:** `['payment_option_39', 'payment_option_40']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `597.74`
- **Predicted:** `748.63`
- **Candidate Selected:** `not_recommended`
- **Baseline Minimum Balance:** `2,948.63` on `2025-08-14`
- **Candidate Minimum Balance:** `0.0`
- **Earliest Safe Full Date Calculated:** ``
- **Desired Completion Date:** `2025-10-04`
- **Payment Options Considered:** `['payment_option_39', 'payment_option_40']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Affordability baseline evaluation: simulator computed available margin without capping at the 22% conservative discretionary debt capacity.

---

## Request: `request_15` (user_15)
- **Requested Amount:** `3,685.00` EUR
- **Request Date:** `2026-01-06` | **Desired Completion Date:** `2026-02-01`
- **Current Balance:** `1,770.05` | **Minimum to Keep:** `1,200.00`
- **Payment Options Available:** `['payment_option_41', 'payment_option_42', 'payment_option_43']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `83.05`
- **Predicted:** `47.56`
- **Candidate Selected:** `not_recommended`
- **Baseline Minimum Balance:** `1,247.56` on `2026-01-14`
- **Candidate Minimum Balance:** `0.0`
- **Earliest Safe Full Date Calculated:** ``
- **Desired Completion Date:** `2026-02-01`
- **Payment Options Considered:** `['payment_option_41', 'payment_option_42', 'payment_option_43']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Baseline deficit vs conservative capacity: baseline breach in month 3 caused amount_safe_to_pay to drop below the 5% monthly income baseline allowance.

---

## Request: `request_17` (user_17)
- **Requested Amount:** `274,600.00` INR
- **Request Date:** `2026-03-01` | **Desired Completion Date:** `2026-05-04`
- **Current Balance:** `550,379.58` | **Minimum to Keep:** `166,100.00`
- **Payment Options Available:** `['payment_option_47', 'payment_option_48', 'payment_option_49']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `243849.58`
- **Predicted:** `246230.49`
- **Candidate Selected:** `installments`
- **Baseline Minimum Balance:** `412,330.49` on `2026-03-14`
- **Candidate Minimum Balance:** `226143.18`
- **Earliest Safe Full Date Calculated:** `2026-03-15`
- **Desired Completion Date:** `2026-05-04`
- **Payment Options Considered:** `['payment_option_47', 'payment_option_48', 'payment_option_49']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Minor rounding and interval shift: 2,380 INR difference due to interval spacing on weekly produce market purchases before salary.

---

## Request: `request_18` (user_18)
- **Requested Amount:** `3,246.10` EUR
- **Request Date:** `2026-07-07` | **Desired Completion Date:** `2026-09-15`
- **Current Balance:** `2,486.00` | **Minimum to Keep:** `1,400.00`
- **Payment Options Available:** `['payment_option_50', 'payment_option_51']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `462`
- **Predicted:** `552.35`
- **Candidate Selected:** `wait`
- **Baseline Minimum Balance:** `1,952.35` on `2026-07-14`
- **Candidate Minimum Balance:** `1400.0`
- **Earliest Safe Full Date Calculated:** `2026-08-15`
- **Desired Completion Date:** `2026-09-15`
- **Payment Options Considered:** `['payment_option_50', 'payment_option_51']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Earliest full payment date scan: simulation evaluated August 15 salary as sufficient for full payment, whereas cumulative expenses require the September 15 salary cycle to keep minimum balance protected across the full 90 days.

### Field Mismatch: `payment_plan`
- **Expected:** `2026-09-15:3246.10`
- **Predicted:** `2026-08-15:3246.10`
- **Candidate Selected:** `wait`
- **Baseline Minimum Balance:** `1,952.35` on `2026-07-14`
- **Candidate Minimum Balance:** `1400.0`
- **Earliest Safe Full Date Calculated:** `2026-08-15`
- **Desired Completion Date:** `2026-09-15`
- **Payment Options Considered:** `['payment_option_50', 'payment_option_51']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Earliest full payment date scan: simulation evaluated August 15 salary as sufficient for full payment, whereas cumulative expenses require the September 15 salary cycle to keep minimum balance protected across the full 90 days.

### Field Mismatch: `earliest_date_for_full_payment`
- **Expected:** `2026-09-15`
- **Predicted:** `2026-08-15`
- **Candidate Selected:** `wait`
- **Baseline Minimum Balance:** `1,952.35` on `2026-07-14`
- **Candidate Minimum Balance:** `1400.0`
- **Earliest Safe Full Date Calculated:** `2026-08-15`
- **Desired Completion Date:** `2026-09-15`
- **Payment Options Considered:** `['payment_option_50', 'payment_option_51']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Earliest full payment date scan: simulation evaluated August 15 salary as sufficient for full payment, whereas cumulative expenses require the September 15 salary cycle to keep minimum balance protected across the full 90 days.

---

## Request: `request_19` (user_19)
- **Requested Amount:** `39,660.00` INR
- **Request Date:** `2024-09-04` | **Desired Completion Date:** `2024-10-04`
- **Current Balance:** `199,545.00` | **Minimum to Keep:** `92,800.00`
- **Payment Options Available:** `['payment_option_52', 'payment_option_53', 'payment_option_54']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `28820`
- **Predicted:** `36481.55`
- **Candidate Selected:** `partial_payment`
- **Baseline Minimum Balance:** `129,281.55` on `2024-09-14`
- **Candidate Minimum Balance:** `108658.36`
- **Earliest Safe Full Date Calculated:** `2024-09-15`
- **Desired Completion Date:** `2024-10-04`
- **Payment Options Considered:** `['payment_option_52', 'payment_option_53', 'payment_option_54']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Partial payment first installment amount: partial payment structure correctly identified, but first installment amount equaled predicted amount_safe_to_pay (36,481.55 instead of 28,820), shifting the remainder payment.

### Field Mismatch: `payment_plan`
- **Expected:** `2024-09-04:28820|2024-09-15:10840`
- **Predicted:** `2024-09-04:36481.55|2024-09-15:3178.45`
- **Candidate Selected:** `partial_payment`
- **Baseline Minimum Balance:** `129,281.55` on `2024-09-14`
- **Candidate Minimum Balance:** `108658.36`
- **Earliest Safe Full Date Calculated:** `2024-09-15`
- **Desired Completion Date:** `2024-10-04`
- **Payment Options Considered:** `['payment_option_52', 'payment_option_53', 'payment_option_54']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Partial payment first installment amount: partial payment structure correctly identified, but first installment amount equaled predicted amount_safe_to_pay (36,481.55 instead of 28,820), shifting the remainder payment.

---

## Request: `request_20` (user_20)
- **Requested Amount:** `303,700.00` INR
- **Request Date:** `2026-02-07` | **Desired Completion Date:** `2026-02-22`
- **Current Balance:** `102,609.05` | **Minimum to Keep:** `64,500.00`
- **Payment Options Available:** `['payment_option_55', 'payment_option_56']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `5400`
- **Predicted:** `10604.99`
- **Candidate Selected:** `not_recommended`
- **Baseline Minimum Balance:** `75,104.99` on `2026-02-12`
- **Candidate Minimum Balance:** `0.0`
- **Earliest Safe Full Date Calculated:** ``
- **Desired Completion Date:** `2026-02-22`
- **Payment Options Considered:** `['payment_option_55', 'payment_option_56']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary pending debits and dining: omission of recurring weekend dining before Feb 15 inflated amount_safe_to_pay beyond the 5,400 INR liquidity boundary.

---

## Request: `request_21` (user_21)
- **Requested Amount:** `1,574.40` USD
- **Request Date:** `2026-04-03` | **Desired Completion Date:** `2026-04-14`
- **Current Balance:** `3,911.35` | **Minimum to Keep:** `1,800.00`
- **Payment Options Available:** `['payment_option_57', 'payment_option_58', 'payment_option_59', 'payment_option_60']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `1543.35`
- **Predicted:** `1574.40`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `3,603.22` on `2026-04-12`
- **Candidate Minimum Balance:** `2028.81`
- **Earliest Safe Full Date Calculated:** `2026-04-03`
- **Desired Completion Date:** `2026-04-14`
- **Payment Options Considered:** `['payment_option_57', 'payment_option_58', 'payment_option_59', 'payment_option_60']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary margin & multi-action spending changes: missing pre-salary entertainment spend caused safe amount to appear as 1574.40 today, bypassing stop:event_1815 and reduce_to:event_1816.

### Field Mismatch: `affordability_status`
- **Expected:** `affordable_with_plan`
- **Predicted:** `affordable_now`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `3,603.22` on `2026-04-12`
- **Candidate Minimum Balance:** `2028.81`
- **Earliest Safe Full Date Calculated:** `2026-04-03`
- **Desired Completion Date:** `2026-04-14`
- **Payment Options Considered:** `['payment_option_57', 'payment_option_58', 'payment_option_59', 'payment_option_60']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary margin & multi-action spending changes: missing pre-salary entertainment spend caused safe amount to appear as 1574.40 today, bypassing stop:event_1815 and reduce_to:event_1816.

### Field Mismatch: `earliest_date_for_full_payment`
- **Expected:** `2026-04-15`
- **Predicted:** `2026-04-03`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `3,603.22` on `2026-04-12`
- **Candidate Minimum Balance:** `2028.81`
- **Earliest Safe Full Date Calculated:** `2026-04-03`
- **Desired Completion Date:** `2026-04-14`
- **Payment Options Considered:** `['payment_option_57', 'payment_option_58', 'payment_option_59', 'payment_option_60']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary margin & multi-action spending changes: missing pre-salary entertainment spend caused safe amount to appear as 1574.40 today, bypassing stop:event_1815 and reduce_to:event_1816.

### Field Mismatch: `spending_changes_needed`
- **Expected:** `stop:event_1815|reduce_to:event_1816:23.50`
- **Predicted:** `none`
- **Candidate Selected:** `full_payment`
- **Baseline Minimum Balance:** `3,603.22` on `2026-04-12`
- **Candidate Minimum Balance:** `2028.81`
- **Earliest Safe Full Date Calculated:** `2026-04-03`
- **Desired Completion Date:** `2026-04-14`
- **Payment Options Considered:** `['payment_option_57', 'payment_option_58', 'payment_option_59', 'payment_option_60']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary margin & multi-action spending changes: missing pre-salary entertainment spend caused safe amount to appear as 1574.40 today, bypassing stop:event_1815 and reduce_to:event_1816.

---

## Request: `request_22` (user_22)
- **Requested Amount:** `731.50` EUR
- **Request Date:** `2024-12-05` | **Desired Completion Date:** `2025-02-10`
- **Current Balance:** `1,132.46` | **Minimum to Keep:** `500.00`
- **Payment Options Available:** `['payment_option_61', 'payment_option_62', 'payment_option_63']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `475.46`
- **Predicted:** `476.07`
- **Candidate Selected:** `installments`
- **Baseline Minimum Balance:** `976.07` on `2024-12-14`
- **Candidate Minimum Balance:** `629.48`
- **Earliest Safe Full Date Calculated:** `2025-01-15`
- **Desired Completion Date:** `2025-02-10`
- **Payment Options Considered:** `['payment_option_61', 'payment_option_62', 'payment_option_63']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Interval transport rounding: minor 0.61 EUR discrepancy due to median vs average fuel refill calculation.

---

## Request: `request_23` (user_23)
- **Requested Amount:** `38,016.00` ZAR
- **Request Date:** `2025-05-07` | **Desired Completion Date:** `2025-07-15`
- **Current Balance:** `51,957.90` | **Minimum to Keep:** `27,000.00`
- **Payment Options Available:** `['payment_option_64', 'payment_option_65', 'payment_option_66']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `9152`
- **Predicted:** `9770.04`
- **Candidate Selected:** `wait`
- **Baseline Minimum Balance:** `36,770.04` on `2025-05-14`
- **Candidate Minimum Balance:** `27000.0`
- **Earliest Safe Full Date Calculated:** `2025-07-15`
- **Desired Completion Date:** `2025-07-15`
- **Payment Options Considered:** `['payment_option_64', 'payment_option_65', 'payment_option_66']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Pre-salary weekly groceries cadence: slight date offset in bi-weekly groceries projection created 618 ZAR difference.

---

## Request: `request_24` (user_24)
- **Requested Amount:** `109,600.00` INR
- **Request Date:** `2026-01-04` | **Desired Completion Date:** `2026-02-08`
- **Current Balance:** `85,045.00` | **Minimum to Keep:** `51,000.00`
- **Payment Options Available:** `['payment_option_67', 'payment_option_68']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `13420`
- **Predicted:** `19692.70`
- **Candidate Selected:** `not_recommended`
- **Baseline Minimum Balance:** `70,692.70` on `2026-01-12`
- **Candidate Minimum Balance:** `0.0`
- **Earliest Safe Full Date Calculated:** ``
- **Desired Completion Date:** `2026-02-08`
- **Payment Options Considered:** `['payment_option_67', 'payment_option_68']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Long-term forecast deficit: terminal deficit in month 3 depressed safe amount calculation below the 22% salary allowance.

---

## Request: `request_25` (user_25)
- **Requested Amount:** `60,496,000.00` IDR
- **Request Date:** `2024-03-06` | **Desired Completion Date:** `2024-04-17`
- **Current Balance:** `32,063,050.00` | **Minimum to Keep:** `23,379,100.00`
- **Payment Options Available:** `['payment_option_69', 'payment_option_70', 'payment_option_71']`

### Field Mismatch: `amount_safe_to_pay`
- **Expected:** `1425000`
- **Predicted:** `3819564.61`
- **Candidate Selected:** `not_recommended`
- **Baseline Minimum Balance:** `27,198,664.61` on `2024-03-12`
- **Candidate Minimum Balance:** `0.0`
- **Earliest Safe Full Date Calculated:** ``
- **Desired Completion Date:** `2024-04-17`
- **Payment Options Considered:** `['payment_option_69', 'payment_option_70', 'payment_option_71']`
- **Spending Changes Considered:** `none`
- **Reason Candidate Won:** Ranked #1 by deterministic tie-breaker (deadline compliance -> no spending changes -> lowest payment total -> earlier start -> fewer payments -> option_id).
- **Root Cause:** Foreign currency conversion and terminal deficit: next confirmed salary in USD required proper conversion to evaluate pre-salary liquidity.

---
