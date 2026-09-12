import pytest
from datetime import date
from alphalens.models.profile import FinancialProfile
from alphalens.models.request import FinancialRequest
from alphalens.models.event import FinancialEvent, EventStatus, EventDirection, EventFlexibility
from alphalens.models.evidence import MessageFact, FactType, Provenance
from alphalens.models.context import RequestContext
from alphalens.engine.recurrence_detector import RecurrenceDetector
from alphalens.engine.cash_flow_simulator import CashFlowSimulator
from alphalens.engine.state_reconstructor import StateReconstructor


def test_future_recurring_expense_generation():
    """9. Future recurring expenses generated across 90 days from history."""
    # User has 3 monthly rent events in history on the 5th
    events = [
        FinancialEvent(
            event_id=f"ev_rent_{i}",
            user_id="user_test",
            event_type="expense",
            description="Apartment rent",
            category="rent",
            direction=EventDirection.DEBIT,
            amount=1500.0,
            currency="USD",
            event_date=f"2026-0{i}-05",
            status=EventStatus.SETTLED,
        )
        for i in range(1, 4)
    ]
    detector = RecurrenceDetector()
    series = detector.detect_series(events, request_date_str="2026-03-01")
    assert len(series) == 1
    s = series[0]
    assert s.category == "rent"
    assert s.day_of_month == 5
    assert s.base_amount == 1500.0

    flows = detector.project_flows(series, request_date_str="2026-03-01", horizon_days=90)
    # Projected on 2026-03-05, 2026-04-05, 2026-05-05
    dates = [f.date for f in flows]
    assert "2026-03-05" in dates
    assert "2026-04-05" in dates
    assert "2026-05-05" in dates
    assert all(f.amount == 1500.0 for f in flows)


def test_recurring_expense_with_changed_amount():
    """10 & 20. Message-derived amendment modifies future recurring expense on effective date."""
    rent_events = [
        FinancialEvent(
            event_id=f"ev_rent_{i}",
            user_id="user_test",
            event_type="expense",
            description="Apartment rent",
            category="rent",
            direction=EventDirection.DEBIT,
            amount=1000.0,
            currency="USD",
            event_date=f"2026-0{i}-05",
            status=EventStatus.SETTLED,
        )
        for i in range(1, 4)
    ]
    # Message: 10% rent increase effective 2026-04-01
    msg = MessageFact(
        fact_type=FactType.LEASE_RENT_INCREASE,
        user_id="user_test",
        entity="Landlord",
        percentage_change=10.0,
        effective_date="2026-04-01",
        source_type="service_provider",
        source_id="msg_rent_inc",
    )
    detector = RecurrenceDetector()
    series = detector.detect_series(rent_events, request_date_str="2026-03-01", messages=[msg])
    assert len(series) == 1
    assert series[0].amended_amount == 1100.0
    assert series[0].amendment_effective_date == "2026-04-01"

    flows = detector.project_flows(series, request_date_str="2026-03-01", horizon_days=90)
    flow_map = {f.date: f.amount for f in flows}
    # On 2026-03-05 (before effective date): original 1000.0
    assert flow_map["2026-03-05"] == 1000.0
    # On 2026-04-05 (after effective date): amended 1100.0
    assert flow_map["2026-04-05"] == 1100.0
    # On 2026-05-05: amended 1100.0
    assert flow_map["2026-05-05"] == 1100.0


def test_salary_update_message_amendment():
    """Message-derived salary increase modifies future salary projection."""
    salary_events = [
        FinancialEvent(
            event_id=f"ev_sal_{i}",
            user_id="user_test",
            event_type="income",
            description="Payroll",
            category="salary",
            direction=EventDirection.CREDIT,
            amount=4000.0,
            currency="USD",
            event_date=f"2026-0{i}-15",
            status=EventStatus.SETTLED,
        )
        for i in range(1, 4)
    ]
    # Message: salary increases to 4500 effective 2026-04-15
    msg = MessageFact(
        fact_type=FactType.SALARY_UPDATE,
        user_id="user_test",
        entity="Employer",
        amount=4500.0,
        currency="USD",
        effective_date="2026-04-15",
        source_type="employer",
        source_id="msg_sal_up",
    )
    detector = RecurrenceDetector()
    series = detector.detect_series(salary_events, request_date_str="2026-03-01", messages=[msg])
    flows = detector.project_flows(series, request_date_str="2026-03-01", horizon_days=90)
    flow_map = {f.date: f.amount for f in flows}
    assert flow_map["2026-03-15"] == 4000.0
    assert flow_map["2026-04-15"] == 4500.0
    assert flow_map["2026-05-15"] == 4500.0


def test_month_boundary_and_leap_year_calendar():
    """15. Handles month boundaries, differing days in month, and leap years."""
    # Recurring series on day 31 of month
    events = [
        FinancialEvent(
            event_id=f"ev_bill_{m}",
            user_id="user_test",
            event_type="expense",
            description="End of month billing",
            category="utilities",
            direction=EventDirection.DEBIT,
            amount=200.0,
            currency="USD",
            event_date=f"2024-0{m}-31" if m in (1, 3) else f"2024-02-29",
            status=EventStatus.SETTLED,
        )
        for m in (1, 2, 3)
    ]
    detector = RecurrenceDetector()
    series = detector.detect_series(events, request_date_str="2024-04-01")
    assert len(series) == 1
    # Day 31 clamped in April (30 days), May (31 days), June (30 days)
    flows = detector.project_flows(series, request_date_str="2024-04-01", horizon_days=90)
    dates = [f.date for f in flows]
    assert "2024-04-30" in dates  # April has 30 days
    assert "2024-05-31" in dates  # May has 31 days
    assert "2024-06-30" in dates  # June has 30 days


def test_multi_currency_events_in_simulation():
    """16. Foreign currency events properly converted to user home currency."""
    profile = FinancialProfile(
        user_id="user_eur",
        home_currency="EUR",
        current_available_balance=5000.0,
        minimum_balance_to_keep=1000.0,
    )
    request = FinancialRequest(
        request_id="req_eur",
        user_id="user_eur",
        request_date="2026-05-01",
        request_type="purchase",
        requested_amount=500.0,
        desired_completion_date="2026-05-30",
        allows_partial_payment=True,
        request_text="Can I afford this?",
    )
    # Event in USD with converted_amount in EUR
    foreign_event = FinancialEvent(
        event_id="ev_usd_flight",
        user_id="user_eur",
        event_type="expense",
        description="US flight booking",
        category="travel",
        direction=EventDirection.DEBIT,
        amount=110.0,
        currency="USD",
        converted_amount=100.0,  # 110 USD = 100 EUR
        conversion_rate=0.909,
        event_date="2026-05-10",
        status=EventStatus.SCHEDULED,
    )
    ctx = RequestContext(
        request=request,
        profile=profile,
        events=[foreign_event],
    )
    sim = CashFlowSimulator()
    res = sim.simulate_baseline(ctx)
    # The deducted amount must be 100.0 EUR, not 110.0 USD
    snap = res.daily_timeline["2026-05-10"]
    assert snap.cash_out == 100.0
    assert snap.closing_balance == 4900.0


def test_image_derived_financial_event():
    """19. Financial event with amount populated from image evidence is simulated accurately."""
    profile = FinancialProfile(
        user_id="user_img",
        home_currency="IDR",
        current_available_balance=5000000.0,
        minimum_balance_to_keep=1000000.0,
    )
    request = FinancialRequest(
        request_id="req_img",
        user_id="user_img",
        request_date="2026-06-01",
        request_type="purchase",
        requested_amount=1000000.0,
        desired_completion_date="2026-06-30",
        allows_partial_payment=True,
        request_text="Can I afford this?",
    )
    # Event whose amount was resolved from image_01 (4,365,000 IDR net salary)
    salary_event = FinancialEvent(
        event_id="ev_image_salary",
        user_id="user_img",
        event_type="income",
        description="Salary from payslip",
        category="salary",
        direction=EventDirection.CREDIT,
        amount=4365000.0,
        currency="IDR",
        converted_amount=4365000.0,
        is_amount_from_image=True,
        provenance=Provenance(source_type="images.csv+media", source_id="image_01", raw_reference="image_01.png"),
        event_date="2026-06-15",
        status=EventStatus.SCHEDULED,
    )
    ctx = RequestContext(
        request=request,
        profile=profile,
        events=[salary_event],
    )
    sim = CashFlowSimulator()
    res = sim.simulate_baseline(ctx)
    snap = res.daily_timeline["2026-06-15"]
    assert snap.cash_in == 4365000.0
    assert snap.closing_balance == 9365000.0
