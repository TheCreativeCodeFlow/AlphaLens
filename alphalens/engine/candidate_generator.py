from datetime import datetime, timedelta, date
from typing import List, Optional, Tuple, Dict, Any
from itertools import combinations

from ..models.context import RequestContext
from ..models.candidate import CandidatePlan
from ..models.event import EventDirection, EventFlexibility
from ..models.state import ScheduledCashFlow
from ..models.request import PaymentOption
from .cash_flow_simulator import CashFlowSimulator


class CandidateGenerator:
    """
    Generates and simulates candidate payment strategies for a given request.
    """

    def __init__(self, simulator: CashFlowSimulator):
        self.simulator = simulator

    def generate_candidates(
        self,
        context: RequestContext,
        amount_safe_to_pay: float,
        earliest_date_for_full_payment: str,
    ) -> List[CandidatePlan]:
        candidates: List[CandidatePlan] = []
        user = context.profile
        req = context.request
        desired_deadline = req.desired_completion_date
        req_amt = req.requested_amount
        home_curr = user.home_currency
        allowed_methods = set(user.payment_methods_user_will_consider)

        # 1. Full payment today (no spending changes)
        if "full_payment" in allowed_methods and amount_safe_to_pay >= req_amt:
            cand = self._create_full_payment_today(context, req_amt)
            if cand.is_safe:
                candidates.append(cand)

        # 2. Supplied installment options (no spending changes)
        if "installments" in allowed_methods and user.max_installment_months is not None:
            for opt in context.payment_options:
                if opt.payment_method == "installments":
                    # Check duration constraint
                    duration_days = (opt.number_of_payments - 1) * (opt.payment_frequency_days or 30)
                    duration_months = round(duration_days / 30.0)
                    if opt.number_of_payments > 1 and duration_months > user.max_installment_months:
                        continue
                    if opt.number_of_payments > (user.max_installment_months + 1):
                        continue

                    cand = self._create_installment_candidate(context, opt)
                    if cand.is_safe:
                        candidates.append(cand)

        # 3. Partial payment (no spending changes)
        if (
            req.allows_partial_payment
            and "partial_payment" in allowed_methods
            and 0 < amount_safe_to_pay < req_amt
            and earliest_date_for_full_payment
            and earliest_date_for_full_payment <= desired_deadline
        ):
            cand = self._create_partial_payment_candidate(
                context, amount_safe_to_pay, earliest_date_for_full_payment
            )
            if cand.is_safe:
                candidates.append(cand)

        # 4. Spending changes candidates (if needed for completion by desired deadline)
        # Check if immediate full payment or installments can be made viable with spending cuts
        # Evaluate only if no candidate currently completes by deadline without spending changes
        deadline_completed = any(
            c.is_within_desired_completion and not c.requires_spending_changes
            for c in candidates
        )
        if not deadline_completed:
            spending_cands = self._generate_spending_change_candidates(context)
            for sc in spending_cands:
                if sc.is_safe:
                    candidates.append(sc)

        # 5. Wait candidate (future full payment)
        if earliest_date_for_full_payment and "full_payment" in allowed_methods:
            cand = self._create_wait_candidate(context, earliest_date_for_full_payment)
            candidates.append(cand)

        # 6. Fallback: Not recommended
        fallback = self._create_not_recommended_candidate(context)
        candidates.append(fallback)

        return candidates

    def _create_full_payment_today(self, context: RequestContext, amount: float) -> CandidatePlan:
        req = context.request
        req_date = req.request_date
        plan_str = f"{req_date}:{self._fmt_num(amount)}"
        
        flow = ScheduledCashFlow(
            flow_id="cand_full_today",
            date=req_date,
            amount=amount,
            original_amount=amount,
            original_currency=context.profile.home_currency,
            direction=EventDirection.DEBIT,
            category=req.request_type,
            description=req.request_text[:30],
        )
        res = self.simulator.simulate_candidate(context, [flow])
        
        return CandidatePlan(
            strategy_id="full_payment_today",
            payment_method="full_payment",
            affordability_status="affordable_now",
            payment_plan=plan_str,
            payments=[(req_date, amount)],
            total_amount=amount,
            start_date=req_date,
            completion_date=req_date,
            spending_changes="none",
            is_safe=res.is_safe,
            minimum_projected_balance=res.minimum_projected_balance,
            minimum_balance_date=res.date_of_minimum_balance,
            violations=[v.date for v in res.get_violations()],
            number_of_payments=1,
            is_within_desired_completion=req_date <= req.desired_completion_date,
            requires_spending_changes=False,
        )

    def _create_installment_candidate(
        self, context: RequestContext, option: PaymentOption
    ) -> CandidatePlan:
        start_dt = datetime.strptime(option.first_payment_date, "%Y-%m-%d").date()
        freq = option.payment_frequency_days or 30
        payments: List[Tuple[str, float]] = []
        flows: List[ScheduledCashFlow] = []

        curr_dt = start_dt
        for i in range(option.number_of_payments):
            dt_str = curr_dt.strftime("%Y-%m-%d")
            amt = option.payment_amount
            payments.append((dt_str, amt))
            flows.append(
                ScheduledCashFlow(
                    flow_id=f"cand_inst_{option.payment_option_id}_{i}",
                    date=dt_str,
                    amount=amt,
                    original_amount=amt,
                    original_currency=context.profile.home_currency,
                    direction=EventDirection.DEBIT,
                    category=context.request.request_type,
                    description=f"Installment {i+1}",
                )
            )
            curr_dt += timedelta(days=freq)

        completion_date = payments[-1][0]
        plan_str = "|".join(f"{dt}:{self._fmt_num(amt)}" for dt, amt in payments)
        res = self.simulator.simulate_candidate(context, flows)

        return CandidatePlan(
            strategy_id=f"inst_{option.payment_option_id}",
            payment_method="installments",
            affordability_status="affordable_with_plan",
            payment_plan=plan_str,
            payments=payments,
            total_amount=option.total_payable_amount,
            start_date=payments[0][0],
            completion_date=completion_date,
            spending_changes="none",
            is_safe=res.is_safe,
            minimum_projected_balance=res.minimum_projected_balance,
            minimum_balance_date=res.date_of_minimum_balance,
            violations=[v.date for v in res.get_violations()],
            number_of_payments=option.number_of_payments,
            option_id=option.payment_option_id,
            is_within_desired_completion=completion_date <= context.request.desired_completion_date,
            requires_spending_changes=False,
        )

    def _create_partial_payment_candidate(
        self, context: RequestContext, safe_amt: float, second_date: str
    ) -> CandidatePlan:
        req = context.request
        req_date = req.request_date
        second_amt = req.requested_amount - safe_amt
        payments = [(req_date, safe_amt), (second_date, second_amt)]
        plan_str = f"{req_date}:{self._fmt_num(safe_amt)}|{second_date}:{self._fmt_num(second_amt)}"

        flows = [
            ScheduledCashFlow(
                flow_id="cand_partial_1",
                date=req_date,
                amount=safe_amt,
                original_amount=safe_amt,
                original_currency=context.profile.home_currency,
                direction=EventDirection.DEBIT,
                category=req.request_type,
                description="Partial payment 1",
            ),
            ScheduledCashFlow(
                flow_id="cand_partial_2",
                date=second_date,
                amount=second_amt,
                original_amount=second_amt,
                original_currency=context.profile.home_currency,
                direction=EventDirection.DEBIT,
                category=req.request_type,
                description="Partial payment 2",
            ),
        ]
        res = self.simulator.simulate_candidate(context, flows)

        return CandidatePlan(
            strategy_id="partial_payment_2step",
            payment_method="partial_payment",
            affordability_status="affordable_with_plan",
            payment_plan=plan_str,
            payments=payments,
            total_amount=req.requested_amount,
            start_date=req_date,
            completion_date=second_date,
            spending_changes="none",
            is_safe=res.is_safe,
            minimum_projected_balance=res.minimum_projected_balance,
            minimum_balance_date=res.date_of_minimum_balance,
            violations=[v.date for v in res.get_violations()],
            number_of_payments=2,
            is_within_desired_completion=second_date <= req.desired_completion_date,
            requires_spending_changes=False,
        )

    def _generate_spending_change_candidates(
        self, context: RequestContext
    ) -> List[CandidatePlan]:
        import copy
        user = context.profile
        req = context.request
        candidates: List[CandidatePlan] = []
        allowed_methods = set(user.payment_methods_user_will_consider)
        if "full_payment" not in allowed_methods:
            return []

        stop_cats = set(user.expense_categories_user_is_willing_to_stop)
        reduce_cats = set(user.expense_categories_user_is_willing_to_reduce)

        # Detect active recurring series
        base_series = self.simulator.recurrence_detector.detect_series(
            context.events, req.request_date, context.messages
        )

        possible_actions = []
        for s in base_series:
            if s.direction != EventDirection.DEBIT or s.category in user.expense_categories_to_protect:
                continue
            if s.category in stop_cats and s.flexibility in (
                EventFlexibility.STOPPABLE, EventFlexibility.REDUCIBLE_OR_STOPPABLE
            ):
                possible_actions.append(("stop", s.source_event_id, None, s))
            if (
                s.category in reduce_cats
                and s.flexibility in (EventFlexibility.REDUCIBLE, EventFlexibility.REDUCIBLE_OR_STOPPABLE)
                and s.minimum_allowed_amount is not None
            ):
                possible_actions.append(("reduce_to", s.source_event_id, s.minimum_allowed_amount, s))

        if not possible_actions:
            return []

        # Try combinations of 1, 2, or 3 actions
        action_combos = []
        for k in (1, 2, 3):
            for combo in combinations(possible_actions, k):
                # Ensure no duplicate event_id
                eids = [c[1] for c in combo]
                if len(eids) == len(set(eids)):
                    action_combos.append(combo)

        req_date = req.request_date
        req_amt = req.requested_amount
        plan_str = f"{req_date}:{self._fmt_num(req_amt)}"

        purchase_flow = ScheduledCashFlow(
            flow_id="cand_purchase_with_changes",
            date=req_date,
            amount=req_amt,
            original_amount=req_amt,
            original_currency=context.profile.home_currency,
            direction=EventDirection.DEBIT,
            category=req.request_type,
            description=req.request_text[:30],
        )

        for combo in action_combos:
            change_strs = []
            change_list = []
            stops = set(c[1] for c in combo if c[0] == "stop")
            reduces = {c[1]: c[2] for c in combo if c[0] == "reduce_to"}

            for act, eid, amt, s in combo:
                if act == "stop":
                    change_strs.append(f"stop:{eid}")
                    change_list.append(("stop", eid, None))
                elif act == "reduce_to":
                    change_strs.append(f"reduce_to:{eid}:{self._fmt_num(amt)}")
                    change_list.append(("reduce_to", eid, amt))

            changes_needed = "|".join(change_strs)

            # Build modified series
            modified_series = [copy.copy(s) for s in base_series]
            for s in modified_series:
                if s.source_event_id in stops:
                    s.is_halted = True
                elif s.source_event_id in reduces:
                    s.base_amount = reduces[s.source_event_id]

            res = self.simulator.simulate_candidate(
                context, [purchase_flow], modified_series=modified_series
            )
            if res.is_safe:
                cand = CandidatePlan(
                    strategy_id=f"spend_changes_{len(change_list)}",
                    payment_method="full_payment",
                    affordability_status="affordable_with_plan",
                    payment_plan=plan_str,
                    payments=[(req_date, req_amt)],
                    total_amount=req_amt,
                    start_date=req_date,
                    completion_date=req_date,
                    spending_changes=changes_needed,
                    spending_change_list=change_list,
                    is_safe=True,
                    minimum_projected_balance=res.minimum_projected_balance,
                    minimum_balance_date=res.date_of_minimum_balance,
                    violations=[],
                    number_of_payments=1,
                    is_within_desired_completion=req_date <= req.desired_completion_date,
                    requires_spending_changes=True,
                )
                candidates.append(cand)

        return candidates

    def _create_wait_candidate(
        self, context: RequestContext, earliest_date: str
    ) -> CandidatePlan:
        req = context.request
        amt = req.requested_amount
        plan_str = f"{earliest_date}:{self._fmt_num(amt)}"

        return CandidatePlan(
            strategy_id="wait_for_future_full",
            payment_method="wait",
            affordability_status="affordable_later",
            payment_plan=plan_str,
            payments=[(earliest_date, amt)],
            total_amount=amt,
            start_date=earliest_date,
            completion_date=earliest_date,
            spending_changes="none",
            is_safe=True,
            minimum_projected_balance=context.profile.minimum_balance_to_keep,
            minimum_balance_date=earliest_date,
            number_of_payments=1,
            is_within_desired_completion=earliest_date <= req.desired_completion_date,
            requires_spending_changes=False,
        )

    def _create_not_recommended_candidate(self, context: RequestContext) -> CandidatePlan:
        return CandidatePlan(
            strategy_id="not_recommended",
            payment_method="not_recommended",
            affordability_status="not_affordable",
            payment_plan="none",
            payments=[],
            total_amount=0.0,
            start_date="",
            completion_date="",
            spending_changes="none",
            is_safe=True,
            minimum_projected_balance=0.0,
            minimum_balance_date="",
            number_of_payments=0,
            is_within_desired_completion=False,
            requires_spending_changes=False,
        )

    @staticmethod
    def _fmt_num(val: float) -> str:
        if abs(val - round(val)) < 1e-5:
            return str(int(round(val)))
        return f"{val:.2f}"
