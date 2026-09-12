from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from .request import FinancialRequest, PaymentOption
from .profile import FinancialProfile
from .event import FinancialEvent
from .evidence import MessageFact, ImageEvidence


@dataclass
class RequestContext:
    request: FinancialRequest
    profile: FinancialProfile
    events: List[FinancialEvent] = field(default_factory=list)
    payment_options: List[PaymentOption] = field(default_factory=list)
    messages: List[MessageFact] = field(default_factory=list)
    image_evidence: Optional[ImageEvidence] = None
    applicable_rates: Dict[Tuple[str, str, str], float] = field(default_factory=dict)
    
    # Metadata & flags
    has_image_evidence: bool = False
    has_message_updates: bool = False
    foreign_events_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "profile": self.profile.to_dict(),
            "events_count": len(self.events),
            "payment_options_count": len(self.payment_options),
            "messages_count": len(self.messages),
            "has_image_evidence": self.has_image_evidence,
            "has_message_updates": self.has_message_updates,
            "foreign_events_count": self.foreign_events_count,
            "payment_options": [opt.to_dict() for opt in self.payment_options],
            "messages": [msg.to_dict() for msg in self.messages],
            "image_evidence": self.image_evidence.to_dict() if self.image_evidence else None,
        }
