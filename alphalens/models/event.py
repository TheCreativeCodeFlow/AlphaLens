from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from .evidence import Provenance


class EventStatus(str, Enum):
    SETTLED = "settled"
    PENDING = "pending"
    SCHEDULED = "scheduled"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNREALIZED = "unrealized"


class EventDirection(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    NON_CASH = "non_cash"


class EventFlexibility(str, Enum):
    FIXED = "fixed"
    STOPPABLE = "stoppable"
    REDUCIBLE = "reducible"
    REDUCIBLE_OR_STOPPABLE = "reducible_or_stoppable"


@dataclass
class FinancialEvent:
    event_id: str
    user_id: str
    event_type: str
    description: str
    category: str
    direction: EventDirection
    amount: Optional[float]
    currency: str
    event_date: str
    settlement_date: Optional[str]
    status: EventStatus
    linked_event_id: Optional[str] = None
    flexibility: EventFlexibility = EventFlexibility.FIXED
    minimum_allowed_amount: Optional[float] = None
    
    # Normalized fields
    converted_amount: Optional[float] = None
    conversion_rate: Optional[float] = None
    conversion_rate_date: Optional[str] = None
    is_amount_from_image: bool = False
    
    # Traceability
    provenance: Optional[Provenance] = None
    raw_row: Dict[str, str] = field(default_factory=dict)

    @property
    def effective_date(self) -> str:
        """Settlement date takes precedence; fallback to event_date."""
        return self.settlement_date if self.settlement_date else self.event_date

    @property
    def is_cash_flow(self) -> bool:
        """Non-cash valuations and unrealized items never count as liquid cash flow."""
        if self.direction == EventDirection.NON_CASH or self.status == EventStatus.UNREALIZED:
            return False
        return True

    @property
    def is_settled(self) -> bool:
        return self.status == EventStatus.SETTLED

    @property
    def is_pending(self) -> bool:
        return self.status == EventStatus.PENDING

    @property
    def is_scheduled(self) -> bool:
        return self.status == EventStatus.SCHEDULED

    @property
    def is_failed(self) -> bool:
        return self.status == EventStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        return self.status == EventStatus.CANCELLED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "description": self.description,
            "category": self.category,
            "direction": self.direction.value,
            "amount": self.amount,
            "currency": self.currency,
            "event_date": self.event_date,
            "settlement_date": self.settlement_date,
            "status": self.status.value,
            "linked_event_id": self.linked_event_id,
            "flexibility": self.flexibility.value,
            "minimum_allowed_amount": self.minimum_allowed_amount,
            "converted_amount": self.converted_amount,
            "conversion_rate": self.conversion_rate,
            "conversion_rate_date": self.conversion_rate_date,
            "is_amount_from_image": self.is_amount_from_image,
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }
