import pytest
from typing import List, Optional

from alphalens.models.profile import FinancialProfile
from alphalens.models.request import FinancialRequest, PaymentOption
from alphalens.models.event import FinancialEvent, EventStatus, EventDirection, EventFlexibility
from alphalens.models.context import RequestContext
from alphalens.engine.recurrence_detector import RecurrenceDetector
from alphalens.engine.cash_flow_simulator import CashFlowSimulator
from alphalens.engine.affordability_engine import AffordabilityEngine


def make_context(
    curr_balance: float = 5000.0,
    min_keep: float = 1000.0,
    req_amount: float = 1500.0,
    req_date: str = "2026-05-01",
    deadline: str = "2026-05-20",
    allows_partial: bool = False,
    user_methods: Optional[List[str]] = None,
    events: Optional[List[FinancialEvent]] = None,
    options: Optional[List[PaymentOption]] = None,
    protected_categories: Optional[List[str]] = None,
    willing_to_stop: Optional[List[str]] = None,
    willing_to_reduce: Optional[List[str]] = None,
) -> RequestContext:
    user = FinancialProfile(
        user_id="synth_user_01",
        home_currency="EUR",
        current_available_balance=curr_balance,
        minimum_balance_to_keep=min_keep,
        financial_priorities=["emergency_savings"],
        expense_categories_to_protect=protected_categories or ["rent", "utilities"],
        expense_categories_user_is_willing_to_reduce=willing_to_reduce or ["dining"],
        expense_categories_user_is_willing_to_stop=willing_to_stop or ["streaming"],
        payment_methods_user_will_consider=user_methods or ["full_payment", "partial_payment", "installments"],
        max_installment_months=6,
    )

    req = FinancialRequest(
        request_id="synth_req_01",
        user_id="synth_user_01",
        request_date=req_date,
        request_type="purchase",
        requested_amount=req_amount,
        desired_completion_date=deadline,
        allows_partial_payment=allows_partial,
        request_text="Can I afford this item?",
    )

    return RequestContext(
        request=req,
        profile=user,
        events=events or [],
        payment_options=options or [],
        messages=[],
    )


@pytest.fixture
def engine():
    sim = CashFlowSimulator(RecurrenceDetector())
    return AffordabilityEngine(sim)


# ---------------------------------------------------------------------------
# Synthetic Holdout Scenarios (Not copied from sample requests)
# ---------------------------------------------------------------------------

def test_synthetic_ample_cash_affordable_now(engine):
    """User with ample cash above minimum balance can afford full payment today."""
    ctx = make_context(curr_balance=10000.0, min_keep=2000.0, req_amount=3000.0)
    res = engine.evaluate_request(ctx)
    assert res["affordability_status"] == "affordable_now"
    assert res["recommended_payment_method"] == "full_payment"
    assert res["payment_plan"] == f"{ctx.request.request_date}:3000"
    assert res["earliest_date_for_full_payment"] == ctx.request.request_date
    assert float(res["amount_safe_to_pay"]) == 3000.0


def test_synthetic_future_salary_affordable_later(engine):
    """User with insufficient cash today but confirmed salary arrives before 90 days."""
    sal_event = FinancialEvent(
        event_id="synth_sal_1",
        user_id="synth_user_01",
        event_type="income",
        description="Confirmed salary",
        category="salary",
        direction=EventDirection.CREDIT,
        amount=4000.0,
        currency="EUR",
        event_date="2026-05-15",
        settlement_date="2026-05-15",
        status=EventStatus.SETTLED,
    )
    # Balance is 1200, min keep 1000 -> only 200 safe today, item is 2500
    ctx = make_context(
        curr_balance=1200.0,
        min_keep=1000.0,
        req_amount=2500.0,
        deadline="2026-05-30",
        events=[sal_event],
    )
    res = engine.evaluate_request(ctx)
    assert res["affordability_status"] == "affordable_later"
    assert res["recommended_payment_method"] == "wait"
    assert res["earliest_date_for_full_payment"] == "2026-05-15"
    assert res["payment_plan"] == "2026-05-15:2500"


def test_synthetic_installments_chosen_when_within_deadline(engine):
    """Installment option completes by deadline and preserves minimum balance."""
    opt = PaymentOption(
        payment_option_id="synth_opt_3m",
        request_id="synth_req_01",
        payment_method="installments",
        payment_amount=500.0,
        number_of_payments=3,
        first_payment_date="2026-05-01",
        payment_frequency_days=30,
        financing_fee=0.0,
        total_payable_amount=1500.0,
    )
    # Starting balance 3000, min keep 1000. 3000 - 500 - 500 - 500 = 1500 >= 1000
    ctx = make_context(
        curr_balance=3000.0,
        min_keep=1000.0,
        req_amount=1500.0,
        deadline="2026-07-15",
        user_methods=["installments"],
        options=[opt],
    )
    res = engine.evaluate_request(ctx)
    assert res["affordability_status"] == "affordable_with_plan"
    assert res["recommended_payment_method"] == "installments"
    assert len(res["payment_plan"].split("|")) == 3


def test_synthetic_uncertain_gig_income_ignored(engine):
    """Uncertain freelance/gig income does not make an unaffordable purchase safe."""
    gig_event = FinancialEvent(
        event_id="synth_gig_1",
        user_id="synth_user_01",
        event_type="gig_income",
        description="Pending unconfirmed gig bonus",
        category="gig",
        direction=EventDirection.CREDIT,
        amount=10000.0,
        currency="EUR",
        event_date="2026-05-05",
        settlement_date="2026-05-05",
        status=EventStatus.PENDING,
    )
    ctx = make_context(
        curr_balance=1000.0,
        min_keep=1000.0,
        req_amount=5000.0,
        events=[gig_event],
    )
    res = engine.evaluate_request(ctx)
    assert res["affordability_status"] == "not_affordable"
    assert res["recommended_payment_method"] == "not_recommended"
    assert float(res["amount_safe_to_pay"]) == 0.0


def test_synthetic_heavy_future_rent_restricts_immediate_spending(engine):
    """Heavy confirmed rent payment in 5 days prevents spending cash today."""
    rent_event = FinancialEvent(
        event_id="synth_rent_1",
        user_id="synth_user_01",
        event_type="housing",
        description="Scheduled rent",
        category="rent",
        direction=EventDirection.DEBIT,
        amount=2500.0,
        currency="EUR",
        event_date="2026-05-06",
        settlement_date="2026-05-06",
        status=EventStatus.SCHEDULED,
    )
    # Starting balance 4000, min keep 1000. Rent takes 2500 -> trough is 1500 - 1000 = 500 safe
    ctx = make_context(
        curr_balance=4000.0,
        min_keep=1000.0,
        req_amount=1200.0,
        events=[rent_event],
    )
    res = engine.evaluate_request(ctx)
    assert float(res["amount_safe_to_pay"]) == 500.0
    assert res["affordability_status"] != "affordable_now"


# ---------------------------------------------------------------------------
# Generalized Invariant & Monotonicity Properties
# ---------------------------------------------------------------------------

def test_invariant_amount_safe_to_pay_bounds(engine):
    """amount_safe_to_pay must always be in [0, requested_amount]."""
    for bal in [500.0, 1000.0, 2500.0, 10000.0]:
        for keep in [200.0, 1000.0, 3000.0]:
            for amt in [50.0, 500.0, 2000.0]:
                ctx = make_context(curr_balance=bal, min_keep=keep, req_amount=amt)
                res = engine.evaluate_request(ctx)
                safe = float(res["amount_safe_to_pay"])
                assert 0.0 <= safe <= amt, f"Violation: {safe} not in [0, {amt}] (bal={bal}, keep={keep})"


def test_monotonicity_increasing_requested_amount_does_not_increase_safe_capacity(engine):
    """If requested amount increases while all else is unchanged, baseline margin is constant."""
    ctx_small = make_context(curr_balance=3000.0, min_keep=1000.0, req_amount=800.0)
    ctx_large = make_context(curr_balance=3000.0, min_keep=1000.0, req_amount=1500.0)
    res_small = engine.evaluate_request(ctx_small)
    res_large = engine.evaluate_request(ctx_large)
    base_small = res_small["baseline_result"].minimum_projected_balance
    base_large = res_large["baseline_result"].minimum_projected_balance
    assert base_small == base_large


def test_monotonicity_increasing_minimum_keep_decreases_or_maintains_safe_capacity(engine):
    """If minimum_balance_to_keep increases, amount_safe_to_pay must decrease or stay equal."""
    ctx_low_keep = make_context(curr_balance=5000.0, min_keep=1000.0, req_amount=3000.0)
    ctx_high_keep = make_context(curr_balance=5000.0, min_keep=3000.0, req_amount=3000.0)
    res_low = engine.evaluate_request(ctx_low_keep)
    res_high = engine.evaluate_request(ctx_high_keep)
    assert float(res_low["amount_safe_to_pay"]) >= float(res_high["amount_safe_to_pay"])


def test_monotonicity_future_expense_cannot_improve_affordability(engine):
    """If a future expense increases, the user cannot become more liquid or afford more."""
    ctx_base = make_context(curr_balance=3000.0, min_keep=1000.0, req_amount=1500.0)
    expensive_event = FinancialEvent(
        event_id="synth_exp_1",
        user_id="synth_user_01",
        event_type="expense",
        description="Utility spike",
        category="utilities",
        direction=EventDirection.DEBIT,
        amount=1200.0,
        currency="EUR",
        event_date="2026-05-10",
        settlement_date="2026-05-10",
        status=EventStatus.SCHEDULED,
    )
    ctx_debit = make_context(
        curr_balance=3000.0, min_keep=1000.0, req_amount=1500.0, events=[expensive_event]
    )
    res_base = engine.evaluate_request(ctx_base)
    res_debit = engine.evaluate_request(ctx_debit)
    assert float(res_base["amount_safe_to_pay"]) >= float(res_debit["amount_safe_to_pay"])


def test_monotonicity_delayed_income_cannot_make_purchase_safe_earlier(engine):
    """If confirmed salary is delayed, earliest_date_for_full_payment cannot move earlier."""
    sal_early = FinancialEvent(
        event_id="synth_sal_early",
        user_id="synth_user_01",
        event_type="income",
        description="Salary early",
        category="salary",
        direction=EventDirection.CREDIT,
        amount=5000.0,
        currency="EUR",
        event_date="2026-05-15",
        settlement_date="2026-05-15",
        status=EventStatus.SETTLED,
    )
    sal_late = FinancialEvent(
        event_id="synth_sal_late",
        user_id="synth_user_01",
        event_type="income",
        description="Salary late",
        category="salary",
        direction=EventDirection.CREDIT,
        amount=5000.0,
        currency="EUR",
        event_date="2026-05-25",
        settlement_date="2026-05-25",
        status=EventStatus.SETTLED,
    )
    ctx_early = make_context(curr_balance=1000.0, min_keep=1000.0, req_amount=3000.0, events=[sal_early])
    ctx_late = make_context(curr_balance=1000.0, min_keep=1000.0, req_amount=3000.0, events=[sal_late])
    res_early = engine.evaluate_request(ctx_early)
    res_late = engine.evaluate_request(ctx_late)
    assert res_early["earliest_date_for_full_payment"] <= res_late["earliest_date_for_full_payment"]
