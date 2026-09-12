from typing import Dict, List, Any
from ..ingestion.loaders import DatasetLoader
from ..ingestion.currency import CurrencyNormalizer


class SchemaValidator:
    """Validates structural constraints and foreign key integrity across the datasets."""

    def __init__(self, loader: DatasetLoader, currency_normalizer: CurrencyNormalizer):
        self.loader = loader
        self.currency_normalizer = currency_normalizer

    def validate_all(self) -> Dict[str, Any]:
        profiles = self.loader.load_profiles()
        eval_requests = self.loader.load_requests()
        sample_requests, _ = self.loader.load_sample_requests()
        events = self.loader.load_events()
        options = self.loader.load_payment_options()
        images = self.loader.load_images_raw()
        messages = self.loader.load_messages_raw()

        all_requests = {**eval_requests, **sample_requests}
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Check User IDs in Requests
        for req_id, req in all_requests.items():
            if req.user_id not in profiles:
                errors.append(f"Request {req_id} references missing user_id '{req.user_id}'")

        # 2. Check User IDs in Events
        for ev_id, ev in events.items():
            if ev.user_id not in profiles:
                errors.append(f"Event {ev_id} references missing user_id '{ev.user_id}'")

        # 3. Check Payment Options foreign keys
        for req_id, opt_list in options.items():
            if req_id not in all_requests:
                errors.append(f"Payment options reference unknown request_id '{req_id}'")

        # 4. Check Linked Event IDs
        for ev_id, ev in events.items():
            if ev.linked_event_id and ev.linked_event_id not in events:
                errors.append(f"Event {ev_id} has broken linked_event_id '{ev.linked_event_id}'")

        # 5. Check Image references and missing amount events
        blank_amount_events = {ev_id for ev_id, ev in events.items() if ev.amount is None}
        image_related_events = set()
        for img in images:
            rel_ev = img["related_event_id"].strip()
            image_related_events.add(rel_ev)
            if rel_ev not in events:
                errors.append(f"Image {img['image_id']} references non-existent event '{rel_ev}'")
            elif events[rel_ev].amount is not None:
                warnings.append(f"Image {img['image_id']} references event '{rel_ev}' which already has an amount")

        if blank_amount_events != image_related_events:
            diff = blank_amount_events ^ image_related_events
            errors.append(f"Mismatch between blank amount events and image references: {diff}")

        # 6. Check Foreign Currency exchange rates
        missing_rates = 0
        for ev_id, ev in events.items():
            if not ev.is_cash_flow or ev.is_failed or ev.is_cancelled:
                continue
            u_curr = profiles[ev.user_id].home_currency
            if ev.currency != u_curr:
                eff_dt = ev.settlement_date or ev.event_date
                rate = self.currency_normalizer.get_rate(ev.currency, u_curr, eff_dt)
                if rate is None:
                    errors.append(
                        f"Missing exchange rate for event {ev_id}: {ev.currency} -> {u_curr} on {eff_dt}"
                    )
                    missing_rates += 1

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "profiles_count": len(profiles),
            "eval_requests_count": len(eval_requests),
            "sample_requests_count": len(sample_requests),
            "events_count": len(events),
            "blank_amount_events_count": len(blank_amount_events),
            "payment_options_count": sum(len(opts) for opts in options.values()),
            "messages_count": len(messages),
            "images_count": len(images),
        }
