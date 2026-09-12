import calendar
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Set, Tuple

from ..models.context import RequestContext
from ..models.event import EventStatus, EventDirection, EventFlexibility, FinancialEvent
from ..models.evidence import FactType
from ..models.state import ScheduledCashFlow, DailyBalanceSnapshot, SafetyResult
from .recurrence_detector import RecurrenceDetector, RecurringSeries


class CashFlowSimulator:
    """
    Deterministic, time-indexed 90-day cash flow simulation engine.
    Applies conservative cash accounting rules and checks the minimum balance invariant.
    """

    def __init__(self, recurrence_detector: Optional[RecurrenceDetector] = None):
        self.recurrence_detector = recurrence_detector or RecurrenceDetector()

    def simulate_baseline(self, context: RequestContext) -> SafetyResult:
        """
        Simulates the user baseline cash flow path over 90 days WITHOUT the new purchase.
        """
        all_flows = self._collect_all_flows(context, candidate_flows=[])
        return self._run_simulation(context, all_flows)

    def simulate_candidate(
        self, context: RequestContext, candidate_flows: List[ScheduledCashFlow]
    ) -> SafetyResult:
        """
        Simulates a hypothetical candidate payment plan (e.g. full payment, installments, partial).
        """
        all_flows = self._collect_all_flows(context, candidate_flows=candidate_flows)
        return self._run_simulation(context, all_flows)

    def _collect_all_flows(
        self, context: RequestContext, candidate_flows: List[ScheduledCashFlow]
    ) -> List[ScheduledCashFlow]:
        """
        Gathers and normalizes all cash flows across discrete events, recurring series, and candidate flows.
        """
        req_date_str = context.request.request_date
        req_date = datetime.strptime(req_date_str, "%Y-%m-%d").date()
        end_date = req_date + timedelta(days=90)
        end_date_str = end_date.strftime("%Y-%m-%d")

        discrete_flows: List[ScheduledCashFlow] = []

        # 1. Discrete events from context.events
        for e in context.events:
            # Rule 1: Non-cash valuations and unrealized assets never affect liquid cash
            if not e.is_cash_flow:
                continue

            # Rule 2: Failed or cancelled transactions never affect spendable cash
            if e.status in (EventStatus.FAILED, EventStatus.CANCELLED):
                continue

            # Rule 3: Internal self-transfers between user accounts have net zero impact
            if e.event_type == "transfer":
                continue

            amt = e.converted_amount or e.amount or 0.0
            if amt <= 0:
                continue

            # Rule 4: Pending Debits MUST be reserved immediately
            if e.status == EventStatus.PENDING and e.direction == EventDirection.DEBIT:
                eff_date = (
                    e.settlement_date
                    if e.settlement_date and e.settlement_date >= req_date_str
                    else req_date_str
                )
                if eff_date <= end_date_str:
                    discrete_flows.append(
                        ScheduledCashFlow(
                            flow_id=f"disc_pend_{e.event_id}",
                            date=eff_date,
                            amount=amt,
                            original_amount=e.amount or amt,
                            original_currency=e.currency,
                            direction=EventDirection.DEBIT,
                            category=e.category,
                            description=f"Pending: {e.description}",
                            source_event_id=e.event_id,
                            is_confirmed=True,
                            is_recurring=False,
                            flexibility=e.flexibility,
                            minimum_allowed_amount=e.minimum_allowed_amount,
                            provenance=e.provenance,
                        )
                    )

            # Rule 5: Pending Credits / prizes / refunds / commissions EXCLUDED until settled
            elif e.status == EventStatus.PENDING and e.direction == EventDirection.CREDIT:
                continue

            # Rule 6: Scheduled Confirmed events (e.g. Next confirmed salary)
            elif e.status == EventStatus.SCHEDULED:
                eff_date = e.settlement_date or e.event_date
                if req_date_str <= eff_date <= end_date_str:
                    discrete_flows.append(
                        ScheduledCashFlow(
                            flow_id=f"disc_sched_{e.event_id}",
                            date=eff_date,
                            amount=amt,
                            original_amount=e.amount or amt,
                            original_currency=e.currency,
                            direction=e.direction,
                            category=e.category,
                            description=e.description,
                            source_event_id=e.event_id,
                            is_confirmed=True,
                            is_recurring=False,
                            flexibility=e.flexibility,
                            minimum_allowed_amount=e.minimum_allowed_amount,
                            provenance=e.provenance,
                        )
                    )

            # Rule 7: Settled events with future date (if any)
            elif e.status == EventStatus.SETTLED and e.event_date > req_date_str:
                if e.event_date <= end_date_str:
                    discrete_flows.append(
                        ScheduledCashFlow(
                            flow_id=f"disc_settled_{e.event_id}",
                            date=e.event_date,
                            amount=amt,
                            original_amount=e.amount or amt,
                            original_currency=e.currency,
                            direction=e.direction,
                            category=e.category,
                            description=e.description,
                            source_event_id=e.event_id,
                            is_confirmed=True,
                            is_recurring=False,
                            flexibility=e.flexibility,
                            minimum_allowed_amount=e.minimum_allowed_amount,
                            provenance=e.provenance,
                        )
                    )

        # 2. Projected recurring commitments
        series_list = self.recurrence_detector.detect_series(
            context.events, req_date_str, context.messages
        )
        existing_scheduled_dates = set((f.date, f.category) for f in discrete_flows)
        recurring_flows = self.recurrence_detector.project_flows(
            series_list=series_list,
            request_date_str=req_date_str,
            horizon_days=90,
            existing_scheduled_dates=existing_scheduled_dates,
        )

        all_flows = discrete_flows + recurring_flows + candidate_flows
        all_flows.sort(key=lambda x: x.date)
        return all_flows

    def _run_simulation(
        self, context: RequestContext, all_flows: List[ScheduledCashFlow]
    ) -> SafetyResult:
        """
        Executes daily balance timeline simulation across exactly 91 calendar days [T, T+90].
        """
        req_date_str = context.request.request_date
        req_date = datetime.strptime(req_date_str, "%Y-%m-%d").date()
        initial_balance = context.profile.current_available_balance
        protected_minimum = context.profile.minimum_balance_to_keep

        # Group flows by date
        flows_by_date: Dict[str, List[ScheduledCashFlow]] = {}
        total_income = 0.0
        total_expenses = 0.0

        for f in all_flows:
            flows_by_date.setdefault(f.date, []).append(f)
            if f.direction == EventDirection.CREDIT:
                total_income += f.amount
            elif f.direction == EventDirection.DEBIT:
                total_expenses += f.amount

        timeline: Dict[str, DailyBalanceSnapshot] = {}
        curr_balance = initial_balance
        min_projected_balance = initial_balance
        date_of_min_balance = req_date_str
        first_violation_date = None
        violation_reasons: List[str] = []

        for day_offset in range(91):
            day_dt = req_date + timedelta(days=day_offset)
            day_str = day_dt.strftime("%Y-%m-%d")

            opening = curr_balance
            flows_today = flows_by_date.get(day_str, [])

            cash_in = sum(f.amount for f in flows_today if f.direction == EventDirection.CREDIT)
            cash_out = sum(f.amount for f in flows_today if f.direction == EventDirection.DEBIT)

            closing = round(opening + cash_in - cash_out, 2)
            curr_balance = closing

            margin = round(closing - protected_minimum, 2)
            is_breached = closing < protected_minimum

            snapshot = DailyBalanceSnapshot(
                date=day_str,
                opening_balance=opening,
                cash_in=cash_in,
                cash_out=cash_out,
                closing_balance=closing,
                flows=flows_today,
                is_minimum_breached=is_breached,
                margin_above_minimum=margin,
            )
            timeline[day_str] = snapshot

            if closing < min_projected_balance:
                min_projected_balance = closing
                date_of_min_balance = day_str

            if is_breached:
                if first_violation_date is None:
                    first_violation_date = day_str
                reason = (
                    f"Day {day_offset} ({day_str}): Closing balance {closing:,.2f} "
                    f"falls below minimum balance {protected_minimum:,.2f} (margin: {margin:,.2f})"
                )
                if reason not in violation_reasons:
                    violation_reasons.append(reason)

        is_safe = min_projected_balance >= protected_minimum
        minimum_margin = round(min_projected_balance - protected_minimum, 2)

        return SafetyResult(
            is_safe=is_safe,
            minimum_projected_balance=min_projected_balance,
            date_of_minimum_balance=date_of_min_balance,
            protected_minimum=protected_minimum,
            minimum_margin=minimum_margin,
            first_violation_date=first_violation_date,
            daily_timeline=timeline,
            total_income_projected=round(total_income, 2),
            total_expenses_projected=round(total_expenses, 2),
            violation_reasons=violation_reasons,
        )
