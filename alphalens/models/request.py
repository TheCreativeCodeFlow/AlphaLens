from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class FinancialRequest:
    request_id: str
    user_id: str
    request_date: str
    request_type: str
    requested_amount: float
    desired_completion_date: str
    allows_partial_payment: bool
    request_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "request_date": self.request_date,
            "request_type": self.request_type,
            "requested_amount": self.requested_amount,
            "desired_completion_date": self.desired_completion_date,
            "allows_partial_payment": self.allows_partial_payment,
            "request_text": self.request_text,
        }


@dataclass
class PaymentOption:
    payment_option_id: str
    request_id: str
    payment_method: str
    payment_amount: float
    number_of_payments: int
    first_payment_date: str
    payment_frequency_days: Optional[int]
    financing_fee: float
    total_payable_amount: float

    def is_installment(self) -> bool:
        return self.payment_method == "installments"

    def is_full_payment(self) -> bool:
        return self.payment_method == "full_payment"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payment_option_id": self.payment_option_id,
            "request_id": self.request_id,
            "payment_method": self.payment_method,
            "payment_amount": self.payment_amount,
            "number_of_payments": self.number_of_payments,
            "first_payment_date": self.first_payment_date,
            "payment_frequency_days": self.payment_frequency_days,
            "financing_fee": self.financing_fee,
            "total_payable_amount": self.total_payable_amount,
        }
