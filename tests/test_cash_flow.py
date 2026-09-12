import pytest
from alphalens.models.profile import FinancialProfile
from alphalens.models.request import FinancialRequest
from alphalens.models.event import FinancialEvent, EventStatus, EventDirection, EventFlexibility
from alphalens.models.context import RequestContext
from alphalens.models.state import ScheduledCashFlow
from alphalens.engine.cash_flow_simulator import CashFlowSimulator
from alphalens.engine.state_reconstructor import StateReconstructor


def make_context(
    balance: float = 10000.0,
    minimum: float = 2000.0,
    req_date: str = "2026-03-01",
    events=None,
    messages=None,
    protected_categories=None,
    stoppable_categories=None,
    reducible_categories=None,
):
    profile = FinancialProfile(
        user_id="test_user",
        home_currency="USD",
        current_available_balance=balance,
        minimum_balance_to_keep=minimum,
        financial_priorities=["emergency_savings"],
        expense_categories_to_protect=protected_categories or ["rent", "groceries"],
        expense_categories_user_is_willing_to_stop=stoppable_categories or ["streaming"],
        expense_categories_user_is_willing_to_reduce=reducible_categories or ["dining"],
        payment_methods_user_will_consider=["full_payment"],
        max_installment_months=None,
    )
    request = FinancialRequest(
        request_id="test_req",
        user_id="test_user",
        request_date=req_date,
        request_type="purchase",
        requested_amount=3000.0,
        desired_completion_date="2026-03-31",
        allows_partial_payment=True,
        request_text="Can I afford this purchase?",
    )
    return RequestContext(
        request=request,
        profile=profile,
        events=events or [],
        payment_options=[],
        messages=messages or [],
    )


def test_purchase_affordable_today():
    ctx = make_context(balance=10000.0, minimum=2000.0)
    sim = CashFlowSimulator()
    candidate = [
        ScheduledCashFlow(
            flow_id="cand_1",
            date=ctx.request.request_date,
            amount=3000.0,
            original_amount=3000.0,
            original_currency="USD",
            direction=EventDirection.DEBIT,
            category="purchase",
            description="Laptop purchase",
        )
    ]
    res = sim.simulate_candidate(ctx, candidate)
    assert res.is_safe is True
    assert res.minimum_projected_balance == 7000.0
    assert res.minimum_margin == 5000.0
    assert res.first_violation_date is None


def test_purchase_unaffordable_because_of_future_rent():
    rent_event = FinancialEvent(
        event_id="ev_rent_due",
        user_id="test_user",
        event_type="expense",
        description="Apartment rent",
        category="rent",
        direction=EventDirection.DEBIT,
        amount=6000.0,
        currency="USD",
        event_date="2026-03-05",
        settlement_date="2026-03-05",
        status=EventStatus.SCHEDULED,
        flexibility=EventFlexibility.FIXED,
    )
    ctx = make_context(balance=10000.0, minimum=2000.0, events=[rent_event])
    sim = CashFlowSimulator()

    candidate = [
        ScheduledCashFlow(
            flow_id="cand_1",
            date=ctx.request.request_date,
            amount=3000.0,
            original_amount=3000.0,
            original_currency="USD",
            direction=EventDirection.DEBIT,
            category="purchase",
            description="Laptop purchase",
        )
    ]
    res = sim.simulate_candidate(ctx, candidate)
    assert res.is_safe is False
    assert res.minimum_projected_balance == 1000.0
    assert res.first_violation_date == "2026-03-05"
    assert len(res.violation_reasons) > 0


def test_future_salary_arriving_before_purchase():
    salary_event = FinancialEvent(
        event_id="ev_salary",
        user_id="test_user",
        event_type="income",
        description="Payroll",
        category="salary",
        direction=EventDirection.CREDIT,
        amount=5000.0,
        currency="USD",
        event_date="2026-03-10",
        settlement_date="2026-03-10",
        status=EventStatus.SCHEDULED,
    )
    ctx = make_context(balance=2500.0, minimum=2000.0, events=[salary_event])
    sim = CashFlowSimulator()

    candidate = [
        ScheduledCashFlow(
            flow_id="cand_delayed",
            date="2026-03-12",
            amount=3000.0,
            original_amount=3000.0,
            original_currency="USD",
            direction=EventDirection.DEBIT,
            category="purchase",
            description="Delayed purchase",
        )
    ]
    res = sim.simulate_candidate(ctx, candidate)
    assert res.is_safe is True
    assert res.minimum_projected_balance == 2500.0


def test_future_salary_arriving_after_purchase():
    salary_event = FinancialEvent(
        event_id="ev_salary",
        user_id="test_user",
        event_type="income",
        description="Payroll",
        category="salary",
        direction=EventDirection.CREDIT,
        amount=5000.0,
        currency="USD",
        event_date="2026-03-15",
        settlement_date="2026-03-15",
        status=EventStatus.SCHEDULED,
    )
    ctx = make_context(balance=2500.0, minimum=2000.0, events=[salary_event])
    sim = CashFlowSimulator()

    candidate = [
        ScheduledCashFlow(
            flow_id="cand_immediate",
            date="2026-03-01",
            amount=3000.0,
            original_amount=3000.0,
            original_currency="USD",
            direction=EventDirection.DEBIT,
            category="purchase",
            description="Immediate purchase",
        )
    ]
    res = sim.simulate_candidate(ctx, candidate)
    assert res.is_safe is False
    assert res.first_violation_date == "2026-03-01"


def test_pending_income_excluded_from_cash():
    pending_gig = FinancialEvent(
        event_id="ev_gig_pending",
        user_id="test_user",
        event_type="income",
        description="Pending gig payout",
        category="gig_income",
        direction=EventDirection.CREDIT,
        amount=10000.0,
        currency="USD",
        event_date="2026-03-03",
        settlement_date="2026-03-03",
        status=EventStatus.PENDING,
    )
    ctx = make_context(balance=2500.0, minimum=2000.0, events=[pending_gig])
    sim = CashFlowSimulator()
    base_res = sim.simulate_baseline(ctx)
    assert base_res.minimum_projected_balance == 2500.0
    assert base_res.total_income_projected == 0.0


def test_uncertain_income_excluded():
    uncertain_prize = FinancialEvent(
        event_id="ev_prize",
        user_id="test_user",
        event_type="income",
        description="Pending prize claim",
        category="prize",
        direction=EventDirection.CREDIT,
        amount=50000.0,
        currency="USD",
        event_date="2026-03-04",
        status=EventStatus.PENDING,
    )
    ctx = make_context(balance=2500.0, minimum=2000.0, events=[uncertain_prize])
    sim = CashFlowSimulator()
    base_res = sim.simulate_baseline(ctx)
    assert base_res.total_income_projected == 0.0


def test_failed_transaction_excluded():
    failed_charge = FinancialEvent(
        event_id="ev_failed",
        user_id="test_user",
        event_type="expense",
        description="Failed merchant charge",
        category="shopping",
        direction=EventDirection.DEBIT,
        amount=500.0,
        currency="USD",
        event_date="2026-03-05",
        status=EventStatus.FAILED,
    )
    ctx = make_context(balance=5000.0, minimum=2000.0, events=[failed_charge])
    sim = CashFlowSimulator()
    res = sim.simulate_baseline(ctx)
    assert res.minimum_projected_balance == 5000.0
    assert res.total_expenses_projected == 0.0


def test_cancelled_transaction_excluded():
    cancelled_charge = FinancialEvent(
        event_id="ev_cancelled",
        user_id="test_user",
        event_type="expense",
        description="Cancelled order",
        category="shopping",
        direction=EventDirection.DEBIT,
        amount=750.0,
        currency="USD",
        event_date="2026-03-06",
        status=EventStatus.CANCELLED,
    )
    ctx = make_context(balance=5000.0, minimum=2000.0, events=[cancelled_charge])
    sim = CashFlowSimulator()
    res = sim.simulate_baseline(ctx)
    assert res.minimum_projected_balance == 5000.0
    assert res.total_expenses_projected == 0.0


def test_temporary_minimum_balance_violation():
    dip_expense = FinancialEvent(
        event_id="ev_dip",
        user_id="test_user",
        event_type="expense",
        description="Car repair",
        category="transport",
        direction=EventDirection.DEBIT,
        amount=4000.0,
        currency="USD",
        event_date="2026-03-05",
        settlement_date="2026-03-05",
        status=EventStatus.SCHEDULED,
    )
    recovery_salary = FinancialEvent(
        event_id="ev_rec_salary",
        user_id="test_user",
        event_type="income",
        description="Salary",
        category="salary",
        direction=EventDirection.CREDIT,
        amount=10000.0,
        currency="USD",
        event_date="2026-03-10",
        settlement_date="2026-03-10",
        status=EventStatus.SCHEDULED,
    )
    ctx = make_context(balance=5000.0, minimum=2000.0, events=[dip_expense, recovery_salary])
    sim = CashFlowSimulator()
    res = sim.simulate_baseline(ctx)

    assert res.is_safe is False
    assert res.first_violation_date == "2026-03-05"
    assert res.minimum_projected_balance == 1000.0
    assert res.daily_timeline["2026-03-05"].is_minimum_breached is True
    assert res.daily_timeline["2026-03-10"].is_minimum_breached is False
    assert res.daily_timeline["2026-03-10"].closing_balance == 11000.0


def test_multiple_events_same_date():
    e1 = FinancialEvent(
        event_id="ev_1",
        user_id="test_user",
        event_type="expense",
        description="Groceries",
        category="groceries",
        direction=EventDirection.DEBIT,
        amount=300.0,
        currency="USD",
        event_date="2026-03-05",
        settlement_date="2026-03-05",
        status=EventStatus.SCHEDULED,
    )
    e2 = FinancialEvent(
        event_id="ev_2",
        user_id="test_user",
        event_type="expense",
        description="Utilities",
        category="utilities",
        direction=EventDirection.DEBIT,
        amount=200.0,
        currency="USD",
        event_date="2026-03-05",
        settlement_date="2026-03-05",
        status=EventStatus.SCHEDULED,
    )
    e3 = FinancialEvent(
        event_id="ev_3",
        user_id="test_user",
        event_type="income",
        description="Bonus",
        category="salary",
        direction=EventDirection.CREDIT,
        amount=1000.0,
        currency="USD",
        event_date="2026-03-05",
        settlement_date="2026-03-05",
        status=EventStatus.SCHEDULED,
    )
    ctx = make_context(balance=5000.0, minimum=2000.0, events=[e1, e2, e3])
    sim = CashFlowSimulator()
    res = sim.simulate_baseline(ctx)

    snap = res.daily_timeline["2026-03-05"]
    assert snap.opening_balance == 5000.0
    assert snap.cash_in == 1000.0
    assert snap.cash_out == 500.0
    assert snap.closing_balance == 5500.0


def test_unrealized_investment_value_excluded():
    unrealized_event = FinancialEvent(
        event_id="ev_unrealized",
        user_id="test_user",
        event_type="investment_valuation",
        description="Stock portfolio valuation",
        category="investment",
        direction=EventDirection.NON_CASH,
        amount=50000.0,
        currency="USD",
        event_date="2026-03-02",
        status=EventStatus.UNREALIZED,
    )
    ctx = make_context(balance=3000.0, minimum=2000.0, events=[unrealized_event])
    reconstructor = StateReconstructor()
    state = reconstructor.reconstruct_state(ctx)

    assert len(state.unrealized_assets) == 1
    assert state.unrealized_assets[0].amount == 50000.0
    assert state.current_available_cash() == 3000.0
    assert state.baseline_forecast.total_income_projected == 0.0


def test_transfer_between_accounts_net_zero():
    transfer_event = FinancialEvent(
        event_id="ev_transfer",
        user_id="test_user",
        event_type="transfer",
        description="Transfer to savings",
        category="savings",
        direction=EventDirection.DEBIT,
        amount=2000.0,
        currency="USD",
        event_date="2026-03-04",
        status=EventStatus.SETTLED,
    )
    ctx = make_context(balance=5000.0, minimum=2000.0, events=[transfer_event])
    reconstructor = StateReconstructor()
    state = reconstructor.reconstruct_state(ctx)

    assert len(state.transfers) == 1
    assert state.current_available_cash() == 5000.0
    assert state.baseline_forecast.total_expenses_projected == 0.0


def test_pending_debit_reserved_immediately():
    pending_debit = FinancialEvent(
        event_id="ev_card_auth",
        user_id="test_user",
        event_type="expense",
        description="Pending card hold",
        category="transport",
        direction=EventDirection.DEBIT,
        amount=500.0,
        currency="USD",
        event_date="2026-02-28",
        settlement_date="2026-03-03",
        status=EventStatus.PENDING,
    )
    ctx = make_context(balance=5000.0, minimum=2000.0, events=[pending_debit])
    sim = CashFlowSimulator()
    res = sim.simulate_baseline(ctx)

    assert res.daily_timeline["2026-03-03"].cash_out == 500.0
    assert res.daily_timeline["2026-03-03"].closing_balance == 4500.0


def test_essential_vs_flexible_spending_exposure():
    e_rent = FinancialEvent(
        event_id="ev_rent",
        user_id="test_user",
        event_type="expense",
        description="Rent",
        category="rent",
        direction=EventDirection.DEBIT,
        amount=2000.0,
        currency="USD",
        event_date="2026-03-05",
        status=EventStatus.SCHEDULED,
        flexibility=EventFlexibility.FIXED,
    )
    e_stream = FinancialEvent(
        event_id="ev_stream",
        user_id="test_user",
        event_type="expense",
        description="Streaming",
        category="streaming",
        direction=EventDirection.DEBIT,
        amount=20.0,
        currency="USD",
        event_date="2026-03-06",
        status=EventStatus.SCHEDULED,
        flexibility=EventFlexibility.STOPPABLE,
    )
    ctx = make_context(
        balance=10000.0,
        minimum=2000.0,
        events=[e_rent, e_stream],
        protected_categories=["rent"],
        stoppable_categories=["streaming"],
    )
    reconstructor = StateReconstructor()
    state = reconstructor.reconstruct_state(ctx)

    assert any(f.source_event_id == "ev_rent" for f in state.essential_expenses)
    assert any(f.source_event_id == "ev_stream" for f in state.flexible_expenses)
