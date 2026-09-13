from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any


@dataclass
class CandidatePlan:
    """
    Represents a concrete, simulated financial strategy for fulfilling a request.
    Includes all metadata required for validation, deterministic ranking, and output generation.
    """
    strategy_id: str
    payment_method: str  # full_payment, installments, partial_payment, wait, not_recommended
    affordability_status: str  # affordable_now, affordable_with_plan, affordable_later, not_affordable
    payment_plan: str  # YYYY-MM-DD:amount|... or none
    payments: List[Tuple[str, float]] = field(default_factory=list)
    total_amount: float = 0.0
    start_date: str = ""
    completion_date: str = ""
    spending_changes: str = "none"
    spending_change_list: List[Tuple[str, str, Optional[float]]] = field(default_factory=list)  # (action, event_id, amount)
    
    # Simulation audit
    is_safe: bool = False
    minimum_projected_balance: float = 0.0
    minimum_balance_date: str = ""
    violations: List[str] = field(default_factory=list)
    
    # Ranking metrics
    number_of_payments: int = 1
    option_id: Optional[str] = None  # payment_option_id if from request_payment_options
    is_within_desired_completion: bool = True
    requires_spending_changes: bool = False
    preference_compatible: bool = True
    
    # Generated explanation
    decision_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "payment_method": self.payment_method,
            "affordability_status": self.affordability_status,
            "payment_plan": self.payment_plan,
            "payments": self.payments,
            "total_amount": round(self.total_amount, 2),
            "start_date": self.start_date,
            "completion_date": self.completion_date,
            "spending_changes": self.spending_changes,
            "is_safe": self.is_safe,
            "minimum_projected_balance": round(self.minimum_projected_balance, 2),
            "minimum_balance_date": self.minimum_balance_date,
            "number_of_payments": self.number_of_payments,
            "option_id": self.option_id,
            "is_within_desired_completion": self.is_within_desired_completion,
            "requires_spending_changes": self.requires_spending_changes,
            "decision_explanation": self.decision_explanation,
        }
