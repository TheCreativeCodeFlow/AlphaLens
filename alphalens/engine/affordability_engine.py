from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from ..models.context import RequestContext
from ..models.candidate import CandidatePlan
from ..models.state import ScheduledCashFlow
from ..models.event import EventDirection
from .cash_flow_simulator import CashFlowSimulator
from .candidate_generator import CandidateGenerator


class AffordabilityEngine:
    """
    Generalized Affordability Decision and Payment-Method Optimization Engine.
    Evaluates requests deterministically against the 90-day cash flow simulator,
    finds safe capacity, ranks strategies strictly by problem rules, and generates
    grounded decision explanations.
    """

    def __init__(self, simulator: CashFlowSimulator):
        self.simulator = simulator
        self.generator = CandidateGenerator(simulator)

    def evaluate_request(self, context: RequestContext) -> Dict[str, Any]:
        # 1. Baseline simulation
        base_res = self.simulator.simulate_baseline(context)
        user = context.profile
        req = context.request
        min_keep = user.minimum_balance_to_keep
        home_curr = user.home_currency

        # 2. amount_safe_to_pay
        # Largest amount user can safely pay today before spending changes while keeping minimum balance
        # If there is upcoming confirmed income, safe capacity is constrained by the pre-income cash valley
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
        if margin_pre <= 0.0 or not base_res.is_safe:
            amount_safe_to_pay = 0.0
        else:
            amount_safe_to_pay = min(req.requested_amount, margin_pre)

        # 3. earliest_date_for_full_payment
        earliest_date = self.find_earliest_date_for_full_payment(context)

        # 4. Generate candidate strategies
        candidates = self.generator.generate_candidates(
            context,
            amount_safe_to_pay=amount_safe_to_pay,
            earliest_date_for_full_payment=earliest_date,
        )

        # 5. Filter valid & safe candidates
        safe_candidates = [c for c in candidates if c.is_safe]

        # 6. Rank candidates
        # Problem statement ranking:
        # 1. Complete full request by desired_completion_date
        # 2. Require no spending changes
        # 3. Minimize total amount paid
        # 4. Start payment earlier
        # 5. Use fewer payments
        # 6. Lowest payment_option_id
        def rank_key(c: CandidatePlan):
            # not_recommended is fallback
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

        # Invariant checks
        if best_candidate.affordability_status == "affordable_now":
            earliest_date = req.request_date

        # Generate grounded explanation
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
            "candidate_plan": best_candidate,
            "baseline_result": base_res,
        }

    def find_earliest_date_for_full_payment(self, context: RequestContext) -> str:
        req = context.request
        req_date = datetime.strptime(req.request_date, "%Y-%m-%d").date()
        amt = req.requested_amount
        home_curr = context.profile.home_currency

        for day_offset in range(91):
            cand_date = req_date + timedelta(days=day_offset)
            cand_date_str = cand_date.strftime("%Y-%m-%d")
            flow = ScheduledCashFlow(
                flow_id=f"test_full_pay_{cand_date_str}",
                date=cand_date_str,
                amount=amt,
                original_amount=amt,
                original_currency=home_curr,
                direction=EventDirection.DEBIT,
                category=req.request_type,
                description="Full payment date test",
            )
            res = self.simulator.simulate_candidate(context, [flow])
            if res.is_safe:
                return cand_date_str

        return ""

    def _generate_explanation(
        self,
        context: RequestContext,
        candidate: CandidatePlan,
        safe_amt: float,
        earliest_date: str,
    ) -> str:
        curr = context.profile.home_currency
        min_b = context.profile.minimum_balance_to_keep
        min_str = self._fmt_display_num(min_b)
        req_amt = context.request.requested_amount
        amt_str = self._fmt_display_num(req_amt)
        deadline = context.request.desired_completion_date

        if candidate.payment_method == "full_payment":
            if not candidate.requires_spending_changes:
                return f"Pay {curr} {amt_str} today. This leaves at least {curr} {min_str} available over the next 90 days."
            else:
                # With spending changes
                changes_phrase = self._describe_spending_changes(context, candidate.spending_change_list)
                return f"{changes_phrase}, then pay {curr} {amt_str} today. This leaves at least {curr} {min_str} available."

        elif candidate.payment_method == "installments":
            inst_amt = candidate.payments[0][1] if candidate.payments else 0.0
            inst_str = self._fmt_display_num(inst_amt)
            start_date_obj = datetime.strptime(candidate.start_date, "%Y-%m-%d")
            start_fmt = f"{start_date_obj.day} {start_date_obj.strftime("%B")} {start_date_obj.year}"
            return f"Use {candidate.number_of_payments} installments of {curr} {inst_str}, starting {start_fmt}. This leaves at least {curr} {min_str} available."

        elif candidate.payment_method == "partial_payment":
            p1 = candidate.payments[0][1]
            p2 = candidate.payments[1][1]
            p1_str = self._fmt_display_num(p1)
            p2_str = self._fmt_display_num(p2)
            date_obj = datetime.strptime(earliest_date, "%Y-%m-%d")
            date_fmt = f"{date_obj.day} {date_obj.strftime("%B")} {date_obj.year}"
            return f"Pay {curr} {p1_str} today and the remaining {curr} {p2_str} on {date_fmt}. This completes the full request and keeps the {curr} {min_str} minimum protected."

        elif candidate.payment_method == "wait":
            date_obj = datetime.strptime(earliest_date, "%Y-%m-%d")
            date_fmt = f"{date_obj.day} {date_obj.strftime("%B")} {date_obj.year}"
            return f"Pay {curr} {amt_str} in full on {date_fmt}. Paying earlier would take the balance below the {curr} {min_str} minimum."

        else:  # not_recommended
            if safe_amt > 0.0:
                safe_str = self._fmt_display_num(safe_amt)
                return f"Do not proceed with the {curr} {amt_str} request. Although {curr} {safe_str} is available today, the full amount cannot be completed safely within 90 days."
            else:
                dead_obj = datetime.strptime(deadline, "%Y-%m-%d")
                dead_fmt = f"{dead_obj.day} {dead_obj.strftime("%B")} {dead_obj.year}"
                return f"Do not make this payment by {dead_fmt}. None of the available options keeps the {curr} {min_str} minimum protected."

    def _describe_spending_changes(
        self, context: RequestContext, change_list: List[Tuple[str, str, Optional[float]]]
    ) -> str:
        parts = []
        events_by_id = {e.event_id: e for e in context.events}
        curr = context.profile.home_currency

        for act, eid, amt in change_list:
            ev = events_by_id.get(eid)
            desc = ev.description.lower() if ev else "expense"
            if act == "stop":
                parts.append(f"Stop the {desc}")
            elif act == "reduce_to":
                amt_str = self._fmt_display_num(amt or 0.0)
                parts.append(f"reduce the {desc} to {curr} {amt_str}")

        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return ", ".join(parts[:-1]) + f", and {parts[-1]}"

    @staticmethod
    def _fmt_amount(val: float) -> str:
        if abs(val - round(val)) < 1e-5:
            return str(int(round(val)))
        return f"{val:.2f}"

    @staticmethod
    def _fmt_display_num(val: float) -> str:
        if abs(val - round(val)) < 1e-6:
            return f"{int(round(val)):,}"
        return f"{val:,.2f}".rstrip("0").rstrip(".")
