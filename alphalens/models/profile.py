from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class FinancialProfile:
    user_id: str
    home_currency: str
    current_available_balance: float
    minimum_balance_to_keep: float
    financial_priorities: List[str] = field(default_factory=list)
    expense_categories_to_protect: List[str] = field(default_factory=list)
    expense_categories_user_is_willing_to_reduce: List[str] = field(default_factory=list)
    expense_categories_user_is_willing_to_stop: List[str] = field(default_factory=list)
    payment_methods_user_will_consider: List[str] = field(default_factory=list)
    max_installment_months: Optional[int] = None

    def accepts_full_payment(self) -> bool:
        return "full_payment" in self.payment_methods_user_will_consider

    def accepts_partial_payment(self) -> bool:
        return "partial_payment" in self.payment_methods_user_will_consider

    def accepts_installments(self) -> bool:
        return "installments" in self.payment_methods_user_will_consider and self.max_installment_months is not None

    def is_category_protected(self, category: str) -> bool:
        return category.lower() in [c.lower() for c in self.expense_categories_to_protect]

    def is_category_reducible(self, category: str) -> bool:
        if self.is_category_protected(category):
            return False
        return category.lower() in [c.lower() for c in self.expense_categories_user_is_willing_to_reduce]

    def is_category_stoppable(self, category: str) -> bool:
        if self.is_category_protected(category):
            return False
        return category.lower() in [c.lower() for c in self.expense_categories_user_is_willing_to_stop]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "home_currency": self.home_currency,
            "current_available_balance": self.current_available_balance,
            "minimum_balance_to_keep": self.minimum_balance_to_keep,
            "financial_priorities": self.financial_priorities,
            "expense_categories_to_protect": self.expense_categories_to_protect,
            "expense_categories_user_is_willing_to_reduce": self.expense_categories_user_is_willing_to_reduce,
            "expense_categories_user_is_willing_to_stop": self.expense_categories_user_is_willing_to_stop,
            "payment_methods_user_will_consider": self.payment_methods_user_will_consider,
            "max_installment_months": self.max_installment_months,
        }
