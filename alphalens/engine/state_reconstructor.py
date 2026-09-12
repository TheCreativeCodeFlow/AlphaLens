from typing import List, Dict, Optional, Set
from ..models.context import RequestContext
from ..models.event import EventStatus, EventDirection, EventFlexibility, FinancialEvent
from ..models.state import FinancialState, ScheduledCashFlow, SafetyResult
from .recurrence_detector import RecurrenceDetector
from .cash_flow_simulator import CashFlowSimulator


class StateReconstructor:
    """
    Reconstructs the formal, granular FinancialState for a user from their hydrated RequestContext.
    Calculates baseline cash flow forecasts and exposes queryable financial metrics.
    """

    def __init__(
        self,
        recurrence_detector: Optional[RecurrenceDetector] = None,
        simulator: Optional[CashFlowSimulator] = None,
    ):
        self.recurrence_detector = recurrence_detector or RecurrenceDetector()
        self.simulator = simulator or CashFlowSimulator(self.recurrence_detector)

    def reconstruct_state(self, context: RequestContext) -> FinancialState:
        """
        Builds the complete FinancialState including categorized cash flow buckets and baseline forecast.
        """
        u_id = context.profile.user_id
        home_curr = context.profile.home_currency
        req_date = context.request.request_date
        current_bal = context.profile.current_available_balance
        min_bal = context.profile.minimum_balance_to_keep

        state = FinancialState(
            user_id=u_id,
            home_currency=home_curr,
            current_cash_balance=current_bal,
            protected_minimum=min_bal,
            request_date=req_date,
        )

        # Categorize discrete events
        for e in context.events:
            amt = e.converted_amount or e.amount or 0.0

            # 1. Non-cash / unrealized investments
            if not e.is_cash_flow:
                state.unrealized_assets.append(
                    ScheduledCashFlow(
                        flow_id=f"asset_{e.event_id}",
                        date=e.effective_date,
                        amount=amt,
                        original_amount=e.amount or amt,
                        original_currency=e.currency,
                        direction=e.direction,
                        category=e.category,
                        description=e.description,
                        source_event_id=e.event_id,
                        is_confirmed=False,
                        flexibility=e.flexibility,
                        provenance=e.provenance,
                    )
                )
                continue

            # 2. Failed and Cancelled transactions
            if e.status == EventStatus.FAILED:
                state.failed_transactions.append(
                    ScheduledCashFlow(
                        flow_id=f"failed_{e.event_id}",
                        date=e.effective_date,
                        amount=amt,
                        original_amount=e.amount or amt,
                        original_currency=e.currency,
                        direction=e.direction,
                        category=e.category,
                        description=e.description,
                        source_event_id=e.event_id,
                        is_confirmed=False,
                    )
                )
                continue

            if e.status == EventStatus.CANCELLED:
                state.cancelled_transactions.append(
                    ScheduledCashFlow(
                        flow_id=f"cancelled_{e.event_id}",
                        date=e.effective_date,
                        amount=amt,
                        original_amount=e.amount or amt,
                        original_currency=e.currency,
                        direction=e.direction,
                        category=e.category,
                        description=e.description,
                        source_event_id=e.event_id,
                        is_confirmed=False,
                    )
                )
                continue

            # 3. Internal transfers
            if e.event_type == "transfer":
                state.transfers.append(
                    ScheduledCashFlow(
                        flow_id=f"transfer_{e.event_id}",
                        date=e.effective_date,
                        amount=amt,
                        original_amount=e.amount or amt,
                        original_currency=e.currency,
                        direction=e.direction,
                        category=e.category,
                        description=e.description,
                        source_event_id=e.event_id,
                        is_confirmed=True,
                    )
                )
                continue

            # 4. Pending debits
            if e.status == EventStatus.PENDING and e.direction == EventDirection.DEBIT:
                eff = e.settlement_date if e.settlement_date and e.settlement_date >= req_date else req_date
                flow = ScheduledCashFlow(
                    flow_id=f"pend_debit_{e.event_id}",
                    date=eff,
                    amount=amt,
                    original_amount=e.amount or amt,
                    original_currency=e.currency,
                    direction=EventDirection.DEBIT,
                    category=e.category,
                    description=e.description,
                    source_event_id=e.event_id,
                    is_confirmed=True,
                    flexibility=e.flexibility,
                )
                state.pending_payments.append(flow)
                state.essential_expenses.append(flow)

            # 5. Pending credits (excluded from liquid cash)
            elif e.status == EventStatus.PENDING and e.direction == EventDirection.CREDIT:
                eff = e.settlement_date or e.event_date
                state.pending_income.append(
                    ScheduledCashFlow(
                        flow_id=f"pend_credit_{e.event_id}",
                        date=eff,
                        amount=amt,
                        original_amount=e.amount or amt,
                        original_currency=e.currency,
                        direction=EventDirection.CREDIT,
                        category=e.category,
                        description=e.description,
                        source_event_id=e.event_id,
                        is_confirmed=False,
                    )
                )

            # 6. Scheduled events (confirmed salary or scheduled bills)
            elif e.status == EventStatus.SCHEDULED:
                eff = e.settlement_date or e.event_date
                if eff >= req_date:
                    flow = ScheduledCashFlow(
                        flow_id=f"sched_{e.event_id}",
                        date=eff,
                        amount=amt,
                        original_amount=e.amount or amt,
                        original_currency=e.currency,
                        direction=e.direction,
                        category=e.category,
                        description=e.description,
                        source_event_id=e.event_id,
                        is_confirmed=True,
                        flexibility=e.flexibility,
                        minimum_allowed_amount=e.minimum_allowed_amount,
                    )
                    if e.direction == EventDirection.CREDIT:
                        state.confirmed_income.append(flow)
                    else:
                        state.scheduled_payments.append(flow)
                        if e.flexibility in (EventFlexibility.STOPPABLE, EventFlexibility.REDUCIBLE, EventFlexibility.REDUCIBLE_OR_STOPPABLE):
                            state.flexible_expenses.append(flow)
                        else:
                            state.essential_expenses.append(flow)

        # 7. Projected recurring series
        series_list = self.recurrence_detector.detect_series(
            context.events, req_date, context.messages
        )
        existing_scheduled = set((f.date, f.category) for f in state.confirmed_income + state.scheduled_payments)
        recurring_flows = self.recurrence_detector.project_flows(
            series_list=series_list,
            request_date_str=req_date,
            horizon_days=90,
            existing_scheduled_dates=existing_scheduled,
        )

        for rf in recurring_flows:
            if rf.direction == EventDirection.CREDIT:
                state.recurring_income.append(rf)
                state.confirmed_income.append(rf)
            else:
                state.recurring_expenses.append(rf)
                # Distinguish essential vs flexible based on user preferences and event flexibility
                is_stoppable = rf.flexibility in (EventFlexibility.STOPPABLE, EventFlexibility.REDUCIBLE_OR_STOPPABLE)
                is_reducible = rf.flexibility in (EventFlexibility.REDUCIBLE, EventFlexibility.REDUCIBLE_OR_STOPPABLE)
                is_protected = context.profile.is_category_protected(rf.category)

                can_change = (
                    not is_protected
                    and (
                        (is_stoppable and context.profile.is_category_stoppable(rf.category))
                        or (is_reducible and context.profile.is_category_reducible(rf.category))
                    )
                )

                if can_change:
                    state.flexible_expenses.append(rf)
                else:
                    state.essential_expenses.append(rf)

        # 8. Compute and attach baseline simulation
        baseline_result = self.simulator.simulate_baseline(context)
        state.baseline_forecast = baseline_result

        return state
