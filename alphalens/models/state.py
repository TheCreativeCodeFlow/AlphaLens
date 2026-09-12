from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .event import EventDirection, EventFlexibility
from .evidence import Provenance


@dataclass
class ScheduledCashFlow:
    """
    Represents a discrete cash flow event projected or scheduled for a specific date.
    All simulation arithmetic is performed in user base/home currency.
    """
    flow_id: str
    date: str  # YYYY-MM-DD
    amount: float  # In user home_currency
    original_amount: float
    original_currency: str
    direction: EventDirection
    category: str
    description: str
    source_event_id: Optional[str] = None
    is_confirmed: bool = True
    is_recurring: bool = False
    flexibility: EventFlexibility = EventFlexibility.FIXED
    minimum_allowed_amount: Optional[float] = None
    provenance: Optional[Provenance] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "date": self.date,
            "amount": self.amount,
            "original_amount": self.original_amount,
            "original_currency": self.original_currency,
            "direction": self.direction.value,
            "category": self.category,
            "description": self.description,
            "source_event_id": self.source_event_id,
            "is_confirmed": self.is_confirmed,
            "is_recurring": self.is_recurring,
            "flexibility": self.flexibility.value,
            "minimum_allowed_amount": self.minimum_allowed_amount,
        }


@dataclass
class DailyBalanceSnapshot:
    """
    Represents the financial state and cash flows for a single calendar day.
    """
    date: str  # YYYY-MM-DD
    opening_balance: float
    cash_in: float
    cash_out: float
    closing_balance: float
    flows: List[ScheduledCashFlow] = field(default_factory=list)
    is_minimum_breached: bool = False
    margin_above_minimum: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "opening_balance": round(self.opening_balance, 2),
            "cash_in": round(self.cash_in, 2),
            "cash_out": round(self.cash_out, 2),
            "closing_balance": round(self.closing_balance, 2),
            "flow_count": len(self.flows),
            "is_minimum_breached": self.is_minimum_breached,
            "margin_above_minimum": round(self.margin_above_minimum, 2),
        }


@dataclass
class SafetyResult:
    """
    The deterministic evaluation result of a 90-day cash flow simulation.
    """
    is_safe: bool
    minimum_projected_balance: float
    date_of_minimum_balance: str
    protected_minimum: float
    minimum_margin: float
    first_violation_date: Optional[str] = None
    daily_timeline: Dict[str, DailyBalanceSnapshot] = field(default_factory=dict)
    total_income_projected: float = 0.0
    total_expenses_projected: float = 0.0
    violation_reasons: List[str] = field(default_factory=list)

    def get_balance_on(self, date_str: str) -> Optional[float]:
        snapshot = self.daily_timeline.get(date_str)
        return snapshot.closing_balance if snapshot else None

    def get_violations(self) -> List[DailyBalanceSnapshot]:
        return [s for s in self.daily_timeline.values() if s.is_minimum_breached]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "minimum_projected_balance": round(self.minimum_projected_balance, 2),
            "date_of_minimum_balance": self.date_of_minimum_balance,
            "protected_minimum": round(self.protected_minimum, 2),
            "minimum_margin": round(self.minimum_margin, 2),
            "first_violation_date": self.first_violation_date,
            "total_income_projected": round(self.total_income_projected, 2),
            "total_expenses_projected": round(self.total_expenses_projected, 2),
            "violations_count": len(self.get_violations()),
            "violation_reasons": self.violation_reasons,
        }


@dataclass
class FinancialState:
    """
    Formal internal financial state representation for a user and evaluation request.
    Retains granular semantics across income, expenses, commitments, and non-cash assets.
    """
    user_id: str
    home_currency: str
    current_cash_balance: float
    protected_minimum: float
    request_date: str

    # Categorized cash flow projections
    confirmed_income: List[ScheduledCashFlow] = field(default_factory=list)
    pending_income: List[ScheduledCashFlow] = field(default_factory=list)
    uncertain_income: List[ScheduledCashFlow] = field(default_factory=list)
    recurring_income: List[ScheduledCashFlow] = field(default_factory=list)

    essential_expenses: List[ScheduledCashFlow] = field(default_factory=list)
    flexible_expenses: List[ScheduledCashFlow] = field(default_factory=list)
    recurring_expenses: List[ScheduledCashFlow] = field(default_factory=list)

    pending_payments: List[ScheduledCashFlow] = field(default_factory=list)
    scheduled_payments: List[ScheduledCashFlow] = field(default_factory=list)
    failed_transactions: List[ScheduledCashFlow] = field(default_factory=list)
    cancelled_transactions: List[ScheduledCashFlow] = field(default_factory=list)
    transfers: List[ScheduledCashFlow] = field(default_factory=list)
    unrealized_assets: List[ScheduledCashFlow] = field(default_factory=list)

    # Baseline forecast (without new purchase)
    baseline_forecast: Optional[SafetyResult] = None

    def current_available_cash(self) -> float:
        """Liquid spendable cash today before optional spending changes."""
        return self.current_cash_balance

    def projected_balance(self, date_str: str) -> Optional[float]:
        """Closing balance projected on a given date under the baseline forecast."""
        if self.baseline_forecast:
            return self.baseline_forecast.get_balance_on(date_str)
        return None

    def minimum_projected_balance(self) -> float:
        """Lowest closing balance projected across the 90-day baseline horizon."""
        if self.baseline_forecast:
            return self.baseline_forecast.minimum_projected_balance
        return self.current_cash_balance

    def date_of_minimum_balance(self) -> str:
        """Date on which the baseline balance reaches its minimum."""
        if self.baseline_forecast:
            return self.baseline_forecast.date_of_minimum_balance
        return self.request_date

    def total_confirmed_income(self, start_date: str, end_date: str) -> float:
        """Total confirmed cash income scheduled between start_date and end_date inclusive."""
        total = 0.0
        for flow in self.confirmed_income:
            if start_date <= flow.date <= end_date:
                total += flow.amount
        return total

    def total_required_expenses(self, start_date: str, end_date: str) -> float:
        """Total essential/required expenses scheduled between start_date and end_date inclusive."""
        total = 0.0
        for flow in self.essential_expenses:
            if start_date <= flow.date <= end_date:
                total += flow.amount
        return total

    def total_flexible_expenses(self, start_date: str, end_date: str) -> float:
        """Total flexible/reducible expenses scheduled between start_date and end_date inclusive."""
        total = 0.0
        for flow in self.flexible_expenses:
            if start_date <= flow.date <= end_date:
                total += flow.amount
        return total

    def is_base_plan_safe(self) -> bool:
        """True if user maintains minimum balance across 90 days without any purchase."""
        if self.baseline_forecast:
            return self.baseline_forecast.is_safe
        return self.current_cash_balance >= self.protected_minimum

    def minimum_balance_violations(self) -> List[str]:
        """List of dates where the baseline balance violates the protected minimum."""
        if not self.baseline_forecast:
            return []
        return [v.date for v in self.baseline_forecast.get_violations()]
