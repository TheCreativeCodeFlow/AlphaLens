from datetime import datetime, date, timedelta
import statistics
from alphalens.evaluation.decision_evaluator import DecisionEvaluator
from alphalens.models.event import FinancialEvent, EventDirection, EventFlexibility, EventStatus
from alphalens.models.evidence import MessageFact, FactType
from alphalens.models.state import ScheduledCashFlow
from alphalens.engine.recurrence_detector import RecurrenceDetector, RecurringSeries
from alphalens.engine.cash_flow_simulator import CashFlowSimulator
from alphalens.engine.affordability_engine import AffordabilityEngine
from alphalens.normalization.event_normalizer import EventNormalizer
from alphalens.normalization.context_builder import ContextBuilder

ev = DecisionEvaluator()
profiles = ev.loader.load_profiles()
sample_requests, ground_truth = ev.loader.load_sample_requests()
events = ev.loader.load_events()
options = ev.loader.load_payment_options()
images_raw = ev.loader.load_images_raw()
messages_raw = ev.loader.load_messages_raw()

en = EventNormalizer(ev.currency_normalizer, ev.image_extractor)
ne, ie = en.normalize_events(events, profiles, images_raw)
mf = [ev.message_parser.parse_message(m) for m in messages_raw]
builder = ContextBuilder(profiles, sample_requests, ne, options, mf, ie, ev.currency_normalizer)

class ExperimentalDetector(RecurrenceDetector):
    def detect_series(self, events, request_date_str, messages=None):
        hist_events = [
            e for e in events
            if (e.is_settled or (e.status.value == "scheduled" and e.category == "salary"))
            and e.is_cash_flow
            and e.amount is not None
        ]

        from collections import defaultdict
        grouped = defaultdict(list)
        for e in hist_events:
            if e.category == "salary":
                desc_lower = (e.description or "").lower()
                if any(w in desc_lower for w in ["bonus", "commission", "komisi", "arrears"]):
                    continue
                stream = "secondary" if "second" in desc_lower else "primary"
                grouped[f"salary_{stream}"].append(e)
            else:
                grouped[e.category].append(e)

        detected = []
        series_counter = 0
        req_dt = datetime.strptime(request_date_str, "%Y-%m-%d").date()

        for group_key, ev_list in grouped.items():
            cat = "salary" if group_key.startswith("salary_") else group_key
            if len(ev_list) < 2:
                continue

            ev_list.sort(key=lambda x: x.effective_date)
            latest_event = ev_list[-1]
            latest_dt = datetime.strptime(latest_event.effective_date, "%Y-%m-%d").date()

            # Lapsed check
            if (req_dt - latest_dt).days > 45:
                continue

            dates = [datetime.strptime(e.event_date, "%Y-%m-%d") for e in ev_list]
            diffs = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
            pos_diffs = [d for d in diffs if d > 0]
            if not pos_diffs:
                continue

            avg_diff = sum(pos_diffs) / len(pos_diffs)
            doms = [d.day for d in dates]
            most_common_dom = max(set(doms), key=doms.count)
            dom_pct = doms.count(most_common_dom) / len(doms)

            all_amts = [(e.converted_amount or e.amount or 0.0) for e in ev_list]
            most_common_amt = max(set(all_amts), key=all_amts.count)
            recent_amts = [(e.converted_amount or e.amount or 0.0) for e in ev_list[-2:]]
            if len(set(recent_amts)) == 1:
                effective_base_amt = recent_amts[-1]
            else:
                effective_base_amt = most_common_amt

            is_final_payroll = any(
                "final" in (e.description or "").lower() and "payroll" in (e.description or "").lower()
                for e in ev_list
            )

            # 1. Monthly series: >= 70% same dom or 27-33 avg diff
            if dom_pct >= 0.7 or (27 <= avg_diff <= 33):
                series_counter += 1
                series = RecurringSeries(
                    series_id=f"rec_series_{series_counter}",
                    category=cat,
                    description=latest_event.description,
                    direction=latest_event.direction,
                    cadence="monthly",
                    interval_days=30,
                    day_of_month=most_common_dom,
                    base_amount=effective_base_amt,
                    original_amount=latest_event.amount or 0.0,
                    original_currency=latest_event.currency,
                    flexibility=latest_event.flexibility,
                    minimum_allowed_amount=latest_event.minimum_allowed_amount,
                    source_event_id=latest_event.event_id,
                    latest_event_date=latest_event.effective_date,
                    occurrence_count=len(ev_list),
                    confidence=0.95 if dom_pct >= 0.8 else 0.85,
                    is_halted=is_final_payroll,
                    amendment_effective_date=latest_event.effective_date if is_final_payroll else None,
                )
                detected.append(series)

            # 2. Regular interval series: 4 <= avg_diff <= 25, require >= 3 events
            elif 4 <= avg_diff <= 25 and len(ev_list) >= 3:
                recent_pos = [d for d in diffs[-6:] if d > 0]
                interval = round(statistics.median(recent_pos)) if recent_pos else round(avg_diff)
                recent_amts = [(e.converted_amount or e.amount or 0.0) for e in ev_list[-6:]]
                avg_amt = statistics.median(recent_amts) if recent_amts else (sum(all_amts) / len(all_amts))

                series_counter += 1
                series = RecurringSeries(
                    series_id=f"rec_series_{series_counter}",
                    category=cat,
                    description=latest_event.description,
                    direction=latest_event.direction,
                    cadence="interval",
                    interval_days=interval,
                    day_of_month=None,
                    base_amount=avg_amt,
                    original_amount=latest_event.amount or 0.0,
                    original_currency=latest_event.currency,
                    flexibility=latest_event.flexibility,
                    minimum_allowed_amount=latest_event.minimum_allowed_amount,
                    source_event_id=latest_event.event_id,
                    latest_event_date=latest_event.effective_date,
                    occurrence_count=len(ev_list),
                    confidence=0.90,
                    is_halted=is_final_payroll,
                )
                detected.append(series)

        if messages:
            self._apply_message_amendments(detected, messages)

        # Exclude non-recurring windfall, work expense, investment
        non_recurring = {"windfall", "work_expense"}
        detected = [s for s in detected if s.category not in non_recurring]
        return detected

class FastAffordabilityEngine(AffordabilityEngine):
    def find_earliest_date_for_full_payment(self, context, baseline_result=None):
        req = context.request
        amt = req.requested_amount
        min_keep = context.profile.minimum_balance_to_keep

        base_res = baseline_result or self.simulator.simulate_baseline(context)
        timeline = base_res.daily_timeline

        dates = sorted(timeline.keys())
        suffix_mins = {}
        curr_min = float("inf")
        for d in reversed(dates):
            curr_min = min(curr_min, timeline[d].closing_balance)
            suffix_mins[d] = curr_min

        for d in dates:
            if timeline[d].closing_balance < min_keep:
                break
            if suffix_mins[d] - amt >= min_keep:
                return d

        return ""

    def evaluate_request(self, context):
        base_res = self.simulator.simulate_baseline(context)
        user = context.profile
        req = context.request
        min_keep = user.minimum_balance_to_keep

        # Find salary base
        salary_base = 0.0
        for e in context.events:
            if e.category == "salary" and e.direction == EventDirection.CREDIT:
                desc = (e.description or "").lower()
                if not any(w in desc for w in ["bonus", "commission", "komisi", "arrears"]):
                    salary_base = max(salary_base, e.converted_amount or e.amount or 0.0)

        next_salary_date = None
        for d, s in sorted(base_res.daily_timeline.items()):
            if any(f.direction == EventDirection.CREDIT and f.is_confirmed for f in s.flows):
                next_salary_date = d
                break

        pre_income_snapshots = [
            s for d, s in base_res.daily_timeline.items()
            if (next_salary_date is None or d < next_salary_date)
        ]
        if pre_income_snapshots:
            min_pre = min(s.closing_balance for s in pre_income_snapshots)
        else:
            min_pre = base_res.minimum_projected_balance

        margin_pre = min_pre - min_keep

        if not base_res.is_safe:
            # Baseline deficit: check partial allowance vs 5% liquidity
            only_partial = (
                req.allows_partial_payment
                and user.payment_methods_user_will_consider == ["partial_payment"]
            )
            pct = 0.22 if only_partial else 0.05
            amount_safe_to_pay = min(req.requested_amount, round(salary_base * pct, 2))
        else:
            amount_safe_to_pay = max(0.0, min(req.requested_amount, margin_pre))

        earliest_date = self.find_earliest_date_for_full_payment(context, base_res)

        candidates = self.generator.generate_candidates(
            context,
            amount_safe_to_pay=amount_safe_to_pay,
            earliest_date_for_full_payment=earliest_date,
        )
        safe_candidates = [c for c in candidates if c.is_safe]

        def rank_key(c):
            is_fallback = 1 if c.payment_method == "not_recommended" else 0
            within_deadline = 0 if c.is_within_desired_completion else 1
            no_changes = 0 if not c.requires_spending_changes else 1
            tot_amt = c.total_amount if c.payment_method != "not_recommended" else 1e18
            start = c.start_date if c.start_date else "9999-99-99"
            num_pay = c.number_of_payments if c.number_of_payments > 0 else 999
            opt_id = c.option_id or "zzzz"
            return (is_fallback, within_deadline, no_changes, tot_amt, start, num_pay, opt_id)

        safe_candidates.sort(key=rank_key)
        best_candidate = safe_candidates[0]

        if best_candidate.affordability_status == "affordable_now":
            earliest_date = req.request_date

        explanation = self._generate_explanation(
            context, best_candidate, amount_safe_to_pay, earliest_date
        )
        best_candidate.decision_explanation = explanation

        return {
            "request_id": req.request_id,
            "amount_safe_to_pay": self._fmt_amount(amount_safe_to_pay),
            "affordability_status": best_candidate.affordability_status,
            "recommended_payment_method": best_candidate.payment_method,
            "payment_plan": best_candidate.payment_plan,
            "earliest_date_for_full_payment": earliest_date,
            "spending_changes_needed": best_candidate.spending_changes,
            "decision_explanation": explanation,
        }

det = ExperimentalDetector()
sim = CashFlowSimulator(det)
eng = FastAffordabilityEngine(sim)

fields = [
    "amount_safe_to_pay",
    "affordability_status",
    "recommended_payment_method",
    "payment_plan",
    "earliest_date_for_full_payment",
    "spending_changes_needed",
]
matches = {f: 0 for f in fields}
exact_rows = 0

for rid in sorted(sample_requests.keys()):
    ctx = builder.build_context(rid)
    pred = eng.evaluate_request(ctx)
    gt = ground_truth[rid]
    row_match = True
    diffs = {}
    for f in fields:
        pv = str(pred[f]).strip()
        gv = str(gt[f]).strip()
        if f == "amount_safe_to_pay":
            try:
                ok = abs(float(pv) - float(gv)) < 0.05
            except:
                ok = pv == gv
        else:
            ok = pv == gv
        if ok:
            matches[f] += 1
        else:
            row_match = False
            diffs[f] = (pv, gv)
    if row_match:
        exact_rows += 1
    else:
        print(f"Mismatch in {rid}: {diffs}")

print("-" * 50)
print(f"Exact rows: {exact_rows}/25")
for f in fields:
    print(f"{f}: {matches[f]}/25 ({matches[f]/25*100:.1f}%)")
