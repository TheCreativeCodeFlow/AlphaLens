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

det = ExperimentalDetector()
sim = CashFlowSimulator(det)

class HardenedAffordabilityEngine(AffordabilityEngine):
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

        # Salary base
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

        earliest_date = self.find_earliest_date_for_full_payment(context, base_res)

        # Preliminary candidate generation to check affordability
        init_safe = max(0.0, min(req.requested_amount, margin_pre))
        candidates = self.generator.generate_candidates(
            context,
            amount_safe_to_pay=init_safe,
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

        # Refine amount_safe_to_pay
        if best_candidate.affordability_status == "not_affordable":
            only_partial = (
                req.allows_partial_payment
                and user.payment_methods_user_will_consider == ["partial_payment"]
            )
            pct = 0.22 if only_partial else 0.05
            amount_safe_to_pay = min(req.requested_amount, round(salary_base * pct, 2))
        else:
            amount_safe_to_pay = init_safe

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

eng = HardenedAffordabilityEngine(sim)

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
