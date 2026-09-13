import os
import pytest
from alphalens.ingestion.loaders import DatasetLoader
from alphalens.ingestion.currency import CurrencyNormalizer
from alphalens.extraction.image_extractor import ImageEvidenceExtractor
from alphalens.extraction.message_parser import MessageParser
from alphalens.normalization.event_normalizer import EventNormalizer
from alphalens.normalization.context_builder import ContextBuilder
from alphalens.engine.recurrence_detector import RecurrenceDetector
from alphalens.engine.cash_flow_simulator import CashFlowSimulator
from alphalens.engine.affordability_engine import AffordabilityEngine
from alphalens.validation.output_validator import OutputValidator, OutputValidationError, REQUIRED_COLUMNS
from alphalens.pipeline.production_runner import ProductionRunner


@pytest.fixture(scope="module")
def setup_engine():
    dataset_dir = "dataset"
    loader = DatasetLoader(dataset_dir)
    currency_norm = CurrencyNormalizer(os.path.join(dataset_dir, "exchange_rates.csv"))
    img_extractor = ImageEvidenceExtractor(os.path.join(dataset_dir, "media", "images"))
    msg_parser = MessageParser()

    profiles = loader.load_profiles()
    sample_requests, gt = loader.load_sample_requests()
    events = loader.load_events()
    options = loader.load_payment_options()
    images_raw = loader.load_images_raw()
    messages_raw = loader.load_messages_raw()

    en = EventNormalizer(currency_norm, img_extractor)
    norm_events, image_evidences = en.normalize_events(events, profiles, images_raw)
    message_facts = [msg_parser.parse_message(m) for m in messages_raw]

    builder = ContextBuilder(
        profiles=profiles,
        requests=sample_requests,
        events=norm_events,
        payment_options=options,
        message_facts=message_facts,
        image_evidences=image_evidences,
        currency_normalizer=currency_norm,
    )
    detector = RecurrenceDetector()
    sim = CashFlowSimulator(detector)
    engine = AffordabilityEngine(sim)

    return {
        "builder": builder,
        "engine": engine,
        "profiles": profiles,
        "requests": sample_requests,
        "events": norm_events,
        "options": options,
        "gt": gt,
    }


def test_invariant_affordable_now_earliest_date(setup_engine):
    """affordability_status == affordable_now must have earliest_date == request_date."""
    engine = setup_engine["engine"]
    builder = setup_engine["builder"]
    ctx = builder.build_context("request_01")
    res = engine.evaluate_request(ctx)
    if res["affordability_status"] == "affordable_now":
        assert res["earliest_date_for_full_payment"] == ctx.request.request_date


def test_invariant_not_affordable_fields(setup_engine):
    """affordability_status == not_affordable must have empty earliest_date, none plan, not_recommended method."""
    engine = setup_engine["engine"]
    builder = setup_engine["builder"]
    ctx = builder.build_context("request_05")
    res = engine.evaluate_request(ctx)
    assert res["affordability_status"] == "not_affordable"
    assert res["earliest_date_for_full_payment"] == ""
    assert res["payment_plan"] == "none"
    assert res["recommended_payment_method"] == "not_recommended"


def test_invariant_partial_payment_structure(setup_engine):
    """partial_payment must have exactly two payments adding to requested_amount."""
    engine = setup_engine["engine"]
    builder = setup_engine["builder"]
    ctx = builder.build_context("request_19")
    res = engine.evaluate_request(ctx)
    if res["recommended_payment_method"] == "partial_payment":
        parts = res["payment_plan"].split("|")
        assert len(parts) == 2
        p1_date, p1_amt = parts[0].split(":")
        p2_date, p2_amt = parts[1].split(":")
        assert p1_date == ctx.request.request_date
        assert float(p1_amt) + float(p2_amt) == pytest.approx(ctx.request.requested_amount, abs=1e-2)


def test_output_validator_detects_invalid_headers():
    """OutputValidator rejects corrupted or missing header columns."""
    validator = OutputValidator()
    rows = [
        {"wrong_id": "req_1", "amount_safe_to_pay": "100"}
    ]
    # via validate_file with wrong header
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("wrong_col1,wrong_col2\n1,2\n")
        tmp_path = f.name
    try:
        valid, errors = validator.validate_file(tmp_path)
        assert not valid
        assert any(e.error_type == "INVALID_HEADER" for e in errors)
    finally:
        os.remove(tmp_path)


def test_output_validator_detects_invalid_enums():
    """OutputValidator rejects unapproved enums for status and method."""
    validator = OutputValidator()
    rows = [
        {
            "request_id": "test_01",
            "amount_safe_to_pay": "100",
            "affordability_status": "maybe_affordable",
            "recommended_payment_method": "credit_card",
            "payment_plan": "none",
            "earliest_date_for_full_payment": "",
            "spending_changes_needed": "none",
            "decision_explanation": "Test explanation.",
        }
    ]
    valid, errors = validator.validate_rows(rows)
    assert not valid
    error_types = [e.error_type for e in errors]
    assert "INVALID_ENUM" in error_types


def test_output_validator_detects_non_chronological_plan():
    """OutputValidator rejects out-of-order payment plan dates."""
    validator = OutputValidator()
    rows = [
        {
            "request_id": "test_01",
            "amount_safe_to_pay": "100",
            "affordability_status": "affordable_with_plan",
            "recommended_payment_method": "installments",
            "payment_plan": "2026-05-15:50|2026-04-15:50",
            "earliest_date_for_full_payment": "2026-05-15",
            "spending_changes_needed": "none",
            "decision_explanation": "Test plan.",
        }
    ]
    valid, errors = validator.validate_rows(rows)
    assert not valid
    assert any(e.error_type == "NOT_CHRONOLOGICAL" for e in errors)


def test_production_runner_output_validity_and_row_count():
    """Production runner produces exactly 250 rows in dataset/output.csv with 0 validation errors."""
    runner = ProductionRunner(dataset_dir="dataset")
    count, md5, valid, errors = runner.run(validate=True)
    assert count == 250
    assert valid is True
    assert len(errors) == 0
    assert len(md5) == 32
