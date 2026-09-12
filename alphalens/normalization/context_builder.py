from typing import Dict, List, Optional, Tuple
from ..models.request import FinancialRequest, PaymentOption
from ..models.profile import FinancialProfile
from ..models.event import FinancialEvent
from ..models.evidence import MessageFact, ImageEvidence
from ..models.context import RequestContext
from ..ingestion.currency import CurrencyNormalizer


class ContextBuilder:
    """
    Hydrates and contextualizes requests by attaching relevant profiles,
    normalized financial events, payment options, messages, and image evidence.
    """

    def __init__(
        self,
        profiles: Dict[str, FinancialProfile],
        requests: Dict[str, FinancialRequest],
        events: Dict[str, FinancialEvent],
        payment_options: Dict[str, List[PaymentOption]],
        message_facts: List[MessageFact],
        image_evidences: Dict[str, ImageEvidence],
        currency_normalizer: CurrencyNormalizer,
    ):
        self.profiles = profiles
        self.requests = requests
        self.events = events
        self.payment_options = payment_options
        self.message_facts = message_facts
        self.image_evidences = image_evidences
        self.currency_normalizer = currency_normalizer

        # Index events by user_id
        self.events_by_user: Dict[str, List[FinancialEvent]] = {}
        for ev in self.events.values():
            if ev.user_id not in self.events_by_user:
                self.events_by_user[ev.user_id] = []
            self.events_by_user[ev.user_id].append(ev)

        # Index messages by user_id and request_id
        self.messages_by_user: Dict[str, List[MessageFact]] = {}
        self.messages_by_req: Dict[str, List[MessageFact]] = {}
        for mf in self.message_facts:
            u_id = mf.user_id
            if u_id not in self.messages_by_user:
                self.messages_by_user[u_id] = []
            self.messages_by_user[u_id].append(mf)
            req_ref = mf.details.get("request_id")
            if req_ref:
                if req_ref not in self.messages_by_req:
                    self.messages_by_req[req_ref] = []
                self.messages_by_req[req_ref].append(mf)

        # Index images by user_id and request_id
        self.images_by_user: Dict[str, ImageEvidence] = {}
        self.images_by_req: Dict[str, ImageEvidence] = {}
        for img in self.image_evidences.values():
            self.images_by_user[img.user_id] = img
            if img.request_id:
                self.images_by_req[img.request_id] = img

    def build_context(self, request_id: str) -> RequestContext:
        """
        Builds a comprehensive, deterministic RequestContext for the given request_id.
        """
        if request_id not in self.requests:
            raise KeyError(f"Request ID '{request_id}' not found in loaded requests.")

        req = self.requests[request_id]
        u_id = req.user_id
        if u_id not in self.profiles:
            raise KeyError(f"User ID '{u_id}' not found in loaded profiles.")

        profile = self.profiles[u_id]
        user_events = self.events_by_user.get(u_id, [])
        options = self.payment_options.get(request_id, [])

        # Relevance filtering for messages
        # Prioritize request-specific messages, then user-level notices
        user_messages = self.messages_by_user.get(u_id, [])

        # Match image evidence
        image_ev = self.images_by_req.get(request_id) or self.images_by_user.get(u_id)

        # Applicable exchange rates for any foreign currency events for this user
        applicable_rates: Dict[Tuple[str, str, str], float] = {}
        foreign_count = 0
        for ev in user_events:
            if ev.currency != profile.home_currency:
                foreign_count += 1
                eff_dt = ev.settlement_date or ev.event_date
                key = (eff_dt, ev.currency, profile.home_currency)
                rate = self.currency_normalizer.get_rate(ev.currency, profile.home_currency, eff_dt)
                if rate is not None:
                    applicable_rates[key] = rate

        return RequestContext(
            request=req,
            profile=profile,
            events=user_events,
            payment_options=options,
            messages=user_messages,
            image_evidence=image_ev,
            applicable_rates=applicable_rates,
            has_image_evidence=image_ev is not None,
            has_message_updates=len(user_messages) > 0,
            foreign_events_count=foreign_count,
        )
