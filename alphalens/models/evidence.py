from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class FactType(str, Enum):
    SALARY_UPDATE = "salary_update"
    SALARY_DATE_CHANGE = "salary_date_change"
    SALARY_REDUCED = "salary_reduced"
    PENDING_INCOME = "pending_income"
    CONFIRMED_INCOME = "confirmed_income"
    LEASE_RENT_INCREASE = "lease_rent_increase"
    NEW_RECURRING_EXPENSE = "new_recurring_expense"
    ACCOUNT_TRANSFER = "account_transfer"
    REFUND_PENDING = "refund_pending"
    INVESTMENT_UNREALIZED = "investment_unrealized"
    DEBIT_RETRY = "debit_retry"
    PRIZE_ONE_OFF = "prize_one_off"
    SEASONAL_ENDED = "seasonal_ended"
    DISPUTE_PENDING = "dispute_pending"
    FOREIGN_CURRENCY_CHARGE = "foreign_currency_charge"
    OTHER = "other"


class FactStatus(str, Enum):
    ANNOUNCED = "announced"
    CONFIRMED = "confirmed"
    PENDING = "pending"
    RECEIVED = "received"
    CLOSED = "closed"
    FAILED = "failed"
    UNREALIZED = "unrealized"
    SETTLED = "settled"


@dataclass(frozen=True)
class Provenance:
    source_type: str
    source_id: str
    raw_reference: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "raw_reference": self.raw_reference,
            "notes": self.notes,
        }


@dataclass
class MessageFact:
    fact_type: FactType
    user_id: str
    entity: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    effective_date: Optional[str] = None
    percentage_change: Optional[float] = None
    status: FactStatus = FactStatus.ANNOUNCED
    source_type: str = "messages.csv"
    source_id: str = ""
    confidence: float = 1.0
    provenance: Optional[Provenance] = None
    raw_text: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_type": self.fact_type.value,
            "user_id": self.user_id,
            "entity": self.entity,
            "amount": self.amount,
            "currency": self.currency,
            "effective_date": self.effective_date,
            "percentage_change": self.percentage_change,
            "status": self.status.value,
            "source_id": self.source_id,
            "confidence": self.confidence,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "details": self.details,
        }


@dataclass
class ImageEvidence:
    image_id: str
    event_id: str
    user_id: str
    request_id: str
    amount: float
    currency: Optional[str] = None
    doc_date: Optional[str] = None
    confidence: float = 1.0
    provenance: Optional[Provenance] = None
    raw_snippets: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_id": self.image_id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "amount": self.amount,
            "currency": self.currency,
            "doc_date": self.doc_date,
            "confidence": self.confidence,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "raw_snippets": self.raw_snippets,
        }
