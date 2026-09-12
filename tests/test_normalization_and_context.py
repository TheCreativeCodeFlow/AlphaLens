import pytest
from alphalens.ingestion.loaders import DatasetLoader
from alphalens.ingestion.currency import CurrencyNormalizer
from alphalens.extraction.image_extractor import ImageEvidenceExtractor
from alphalens.extraction.message_parser import MessageParser
from alphalens.normalization.event_normalizer import EventNormalizer
from alphalens.normalization.context_builder import ContextBuilder


def test_event_normalization_and_hydration():
    loader = DatasetLoader()
    currency_norm = CurrencyNormalizer()
    image_extractor = ImageEvidenceExtractor()
    message_parser = MessageParser()

    profiles = loader.load_profiles()
    sample_requests, _ = loader.load_sample_requests()
    events = loader.load_events()
    options = loader.load_payment_options()
    images_raw = loader.load_images_raw()
    messages_raw = loader.load_messages_raw()

    message_facts = [message_parser.parse_message(m) for m in messages_raw]

    normalizer = EventNormalizer(currency_norm, image_extractor)
    norm_events, image_evidences = normalizer.normalize_events(events, profiles, images_raw)

    # Verify that the 16 missing amounts are all populated
    missing_count = sum(1 for e in norm_events.values() if e.amount is None)
    assert missing_count == 0

    # Verify event_253 has image amount extracted
    ev_253 = norm_events["event_253"]
    assert ev_253.amount == 4365000.0
    assert ev_253.is_amount_from_image is True
    assert ev_253.provenance.source_type == "images.csv+media"

    # Verify foreign currency conversion
    # event_106 (user_12, home_curr=ZAR, event curr=USD, 2024-04-15)
    # Check that converted_amount exists
    for ev in norm_events.values():
        if ev.currency != profiles[ev.user_id].home_currency and ev.is_cash_flow and not ev.is_failed and not ev.is_cancelled:
            assert ev.converted_amount is not None
            assert ev.conversion_rate is not None

    # Context Builder test
    builder = ContextBuilder(
        profiles=profiles,
        requests=sample_requests,
        events=norm_events,
        payment_options=options,
        message_facts=message_facts,
        image_evidences=image_evidences,
        currency_normalizer=currency_norm,
    )

    ctx_01 = builder.build_context("request_01")
    assert ctx_01.request.request_id == "request_01"
    assert ctx_01.profile.user_id == "user_01"
    assert len(ctx_01.events) == 103
    assert len(ctx_01.payment_options) == 4

    ctx_03 = builder.build_context("request_03")
    assert ctx_03.has_image_evidence is True
    assert ctx_03.image_evidence.image_id == "image_01"
    assert ctx_03.image_evidence.amount == 4365000.0
