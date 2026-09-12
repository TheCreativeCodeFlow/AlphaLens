from typing import Dict, List, Optional, Tuple
from ..models.event import FinancialEvent
from ..models.profile import FinancialProfile
from ..models.evidence import ImageEvidence, Provenance
from ..ingestion.currency import CurrencyNormalizer
from ..extraction.image_extractor import ImageEvidenceExtractor


class EventNormalizer:
    """
    Normalizes financial events by resolving missing amounts from image evidence,
    converting foreign-currency events using fixed exchange rates, and attaching provenance.
    """

    def __init__(
        self,
        currency_normalizer: CurrencyNormalizer,
        image_extractor: ImageEvidenceExtractor,
    ):
        self.currency_normalizer = currency_normalizer
        self.image_extractor = image_extractor

    def normalize_events(
        self,
        events: Dict[str, FinancialEvent],
        profiles: Dict[str, FinancialProfile],
        images_raw: List[Dict[str, str]],
    ) -> Tuple[Dict[str, FinancialEvent], Dict[str, ImageEvidence]]:
        """
        Normalizes all events in-place and returns the dictionary of normalized events
        and the extracted image evidence mapping.
        """
        # Map related_event_id -> image row
        event_to_image: Dict[str, Dict[str, str]] = {}
        for img_row in images_raw:
            rel_ev = img_row["related_event_id"].strip()
            event_to_image[rel_ev] = img_row

        image_evidences: Dict[str, ImageEvidence] = {}

        for ev_id, ev in events.items():
            u_id = ev.user_id
            profile = profiles.get(u_id)
            if not profile:
                continue
            home_currency = profile.home_currency

            # 1. Resolve missing amounts from linked images
            if ev.amount is None and ev_id in event_to_image:
                img_info = event_to_image[ev_id]
                img_id = img_info["image_id"].strip()
                evidence = self.image_extractor.extract_evidence(
                    image_id=img_id,
                    event_id=ev_id,
                    user_id=u_id,
                    request_id=img_info.get("request_id", ""),
                    event_context=ev.to_dict(),
                )
                ev.amount = evidence.amount
                ev.is_amount_from_image = True
                ev.provenance = Provenance(
                    source_type="images.csv+media",
                    source_id=img_id,
                    raw_reference=f"{img_id}.png linked to {ev_id}",
                    notes=f"Extracted amount: {evidence.amount} {evidence.currency}",
                )
                image_evidences[img_id] = evidence

            # 2. Normalize currency conversion to user home_currency
            if ev.amount is not None:
                if ev.currency == home_currency:
                    ev.converted_amount = ev.amount
                    ev.conversion_rate = 1.0
                    ev.conversion_rate_date = ev.settlement_date or ev.event_date
                else:
                    eff_date = ev.settlement_date or ev.event_date
                    converted, rate, rate_dt = self.currency_normalizer.convert(
                        amount=ev.amount,
                        from_currency=ev.currency,
                        to_currency=home_currency,
                        rate_date=eff_date,
                    )
                    ev.converted_amount = converted
                    ev.conversion_rate = rate
                    ev.conversion_rate_date = rate_dt

        return events, image_evidences
