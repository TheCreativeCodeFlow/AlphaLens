"""
Phase 3 Unit Test Suite: Affordability Decision & Payment Optimizer.
Tests deterministic candidate generation, ranking hierarchy, partial payment invariants,
spending change constraints, and decision explanations.
"""

import pytest
from datetime import datetime

from alphalens.models.profile import FinancialProfile
from alphalens.models.request import FinancialRequest, PaymentOption
from alphalens.models.event import FinancialEvent, EventDirection, EventFlexibility, EventStatus
from alphalens.models.context import RequestContext
from alphalens.engine.recurrence_detector import RecurrenceDetector
from alphalens.engine.cash_flow_simulator import CashFlowSimulator
from alphalens.engine.candidate_generator import CandidateGenerator
from alphalens.engine.affordability_engine import AffordabilityEngine


@pytest.fixture
def mock_context():
    profile = FinancialProfile(
        user_id="user_test",
        home_currency="USD",
        current_available_balance=5000.0,
        minimum_balance_to_keep=1000.0,
        financial_priorities=["emergency_savings"],
        expense_categories_to_protect=["rent", "groceries"],
        expense_categories_user_is_willing_to_reduce=["streaming"],
        expense_categories_user_is_willing_to_stop=["cloud_storage"],
        payment_methods_user_will_consider=["full_payment", "partial_payment", "installments"],
        max_installment_months=6,
    )
    request = FinancialRequest(
        request_id="req_test_01",
        user_id="user_test",
        request_date="2026-05-01",
        request_type="electronics",
        requested_amount=1200.0,
        desired_completion_date="2026-06-01",
        allows_partial_payment=True,
        request_text="Can I afford this laptop?",
    )
    events = [
        FinancialEvent(
            event_id="ev_salary",
            user_id="user_test",
            event_type="income",
            description="Payroll credit",
            category="salary",
            direction=EventDirection.CREDIT,
            amount=3000.0,
            currency="USD",
            event_date="2026-04-15",
            settlement_date="2026-04-15",
            status=EventStatus.SETTLED,
            flexibility=EventFlexibility.FIXED,
        ),
        FinancialEvent(
            event_id="ev_rent",
            user_id="user_test",
            event_type="expense",
            description="Apartment rent",
            category="rent",
            direction=EventDirection.DEBIT,
            amount=1500.0,
            currency="USD",
            event_date="2026-04-01",
            settlement_date="2026-04-01",
            status=EventStatus.SETTLED,
            flexibility=EventFlexibility.FIXED,
        ),
    ]
    options = [
        PaymentOption(
            payment_option_id="opt_1",
            request_id="req_test_01",
            payment_method="installments",
            payment_amount=400.0,
            number_of_payments=3,
            first_payment_date="2026-05-01",
            payment_frequency_days=30,
            financing_fee=0.0,
            total_payable_amount=1200.0,
        )
    ]
    return RequestContext(
        request=request,
        profile=profile,
        events=events,
        payment_options=options,
        messages=[],
        image_evidence=None,
    )


def test_full_payment_affordable_today(mock_context):
    detector = RecurrenceDetector()
    simulator = CashFlowSimulator(detector)
    engine = AffordabilityEngine(simulator)

    decision = engine.evaluate_request(mock_context)
    assert decision["affordability_status"] in ("affordable_now", "affordable_with_plan")
    assert decision["recommended_payment_method"] in ("full_payment", "installments")
    assert float(decision["amount_safe_to_pay"]) >= 0.0
    assert "USD" in decision["decision_explanation"]


def test_partial_payment_invariant():
    """Verify that partial payment plan has exactly two payments that sum to requested_amount."""
    profile = FinancialProfile(
        user_id="user_test_part",
        home_currency="EUR",
        current_available_balance=1200.0,
        minimum_balance_to_keep=800.0,
        financial_priorities=[],
        expense_categories_to_protect=["rent"],
        expense_categories_user_is_willing_to_reduce=[],
        expense_categories_user_is_willing_to_stop=[],
        payment_methods_user_will_consider=["partial_payment"],
        max_installment_months=None,
    )
    request = FinancialRequest(
        request_id="req_test_part",
        user_id="user_test_part",
        request_date="2026-05-01",
        request_type="purchase",
        requested_amount=1000.0,
        desired_completion_date="2026-06-15",
        allows_partial_payment=True,
        request_text="Can I do partial payment?",
    )
    events = [
        FinancialEvent(
            event_id="ev_sal_past",
            user_id="user_test_part",
            event_type="income",
            description="Payroll credit",
            category="salary",
            direction=EventDirection.CREDIT,
            amount=2000.0,
            currency="EUR",
            event_date="2026-04-15",
            settlement_date="2026-04-15",
            status=EventStatus.SETTLED,
            flexibility=EventFlexibility.FIXED,
        ),
    ]
    ctx = RequestContext(
        request=request,
        profile=profile,
        events=events,
        payment_options=[],
        messages=[],
        image_evidence=None,
    )

    detector = RecurrenceDetector()
    simulator = CashFlowSimulator(detector)
    engine = AffordabilityEngine(simulator)

    decision = engine.evaluate_request(ctx)
    if decision["recommended_payment_method"] == "partial_payment":
        parts = decision["payment_plan"].split("|")
        assert len(parts) == 2
        d1, a1 = parts[0].split(":")
        d2, a2 = parts[1].split(":")
        assert round(float(a1) + float(a2), 2) == 1000.0
        assert d1 == "2026-05-01"


def test_spending_changes_constraints(mock_context):
    """Verify spending changes never touch protected categories and never exceed 3 actions."""
    detector = RecurrenceDetector()
    simulator = CashFlowSimulator(detector)
    gen = CandidateGenerator(simulator)

    cands = gen._generate_spending_change_candidates(mock_context)
    for c in cands:
        if c.spending_changes != "none":
            actions = c.spending_changes.split("|")
            assert len(actions) <= 3
            for act in actions:
                assert act.startswith("stop:") or act.startswith("reduce_to:")
                parts = act.split(":")
                ev_id = parts[1]
                assert ev_id not in [e.event_id for e in mock_context.events if e.category in mock_context.profile.expense_categories_to_protect]


def test_not_affordable_when_no_options_and_no_cash():
    """Verify not_affordable status and not_recommended method when user is in deficit."""
    profile = FinancialProfile(
        user_id="user_poor",
        home_currency="USD",
        current_available_balance=100.0,
        minimum_balance_to_keep=500.0,  # Already breaching
        financial_priorities=[],
        expense_categories_to_protect=[],
        expense_categories_user_is_willing_to_reduce=[],
        expense_categories_user_is_willing_to_stop=[],
        payment_methods_user_will_consider=["full_payment"],
        max_installment_months=None,
    )
    request = FinancialRequest(
        request_id="req_poor",
        user_id="user_poor",
        request_date="2026-05-01",
        request_type="luxury",
        requested_amount=10000.0,
        desired_completion_date="2026-05-10",
        allows_partial_payment=False,
        request_text="Can I buy luxury item?",
    )
    ctx = RequestContext(
        request=request,
        profile=profile,
        events=[],
        payment_options=[],
        messages=[],
        image_evidence=None,
    )

    detector = RecurrenceDetector()
    simulator = CashFlowSimulator(detector)
    engine = AffordabilityEngine(simulator)

    decision = engine.evaluate_request(ctx)
    assert decision["affordability_status"] == "not_affordable"
    assert decision["recommended_payment_method"] == "not_recommended"
    assert decision["payment_plan"] == "none"
    assert decision["spending_changes_needed"] == "none"
    assert decision["earliest_date_for_full_payment"] == ""


def test_output_schema_keys(mock_context):
    """Verify that decision dictionary contains all required challenge columns."""
    detector = RecurrenceDetector()
    simulator = CashFlowSimulator(detector)
    engine = AffordabilityEngine(simulator)

    decision = engine.evaluate_request(mock_context)
    required_cols = [
        "request_id",
        "amount_safe_to_pay",
        "affordability_status",
        "recommended_payment_method",
        "payment_plan",
        "earliest_date_for_full_payment",
        "spending_changes_needed",
        "decision_explanation",
    ]
    for col in required_cols:
        assert col in decision, f"Missing required column: {col}"
