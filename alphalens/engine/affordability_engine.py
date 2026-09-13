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
        # Specification definition (problem_statement.md §Output meaning & §90-Day Safety Check):
        # "largest amount the user can safely pay on request_date before optional spending changes,
        # while covering protected expenses and maintaining their minimum balance"
        # "the most the user can pay today before optional spending changes without breaking the 90-day safety check, capped at requested_amount."
        #
        # Mathematical derivation:
        # If amount A is paid on request_date, the user's closing balance on day t is:
        #   closing_balance(t) - A >= minimum_balance_to_keep  forall t in [0, 90]
        #   A <= closing_balance(t) - minimum_balance_to_keep  forall t in [0, 90]
        #   A <= min_{t} (closing_balance(t) - minimum_balance_to_keep)
        #
        # Therefore, if baseline simulation is unsafe (balance breaches min_keep), safe capacity is 0.0.
        # Otherwise, safe capacity is min(requested_amount, min_{t} closing_balance(t) - min_keep).
        if not base_res.is_safe:
            amount_safe_to_pay = 0.0
        else:
            net_safe_margin = base_res.minimum_projected_balance - min_keep
            amount_safe_to_pay = max(0.0, min(req.requested_amount, round(net_safe_margin, 2)))

        # 4. earliest_date_for_full_payment (fast suffix-minimum scan)
        earliest_date = self.find_earliest_date_for_full_payment(context, base_res)

        # 5. Generate candidate strategies
        candidates = self.generator.generate_candidates(
            context,
            amount_safe_to_pay=amount_safe_to_pay,
            earliest_date_for_full_payment=earliest_date,
        )

        # 6. Filter valid & safe candidates
        safe_candidates = [c for c in candidates if c.is_safe]

        # 7. Rank candidates
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
        elif best_candidate.affordability_status == "not_affordable":
            earliest_date = ""

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

    def find_earliest_date_for_full_payment(
        self, context: RequestContext, baseline_result: Optional[SafetyResult] = None
    ) -> str:
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
