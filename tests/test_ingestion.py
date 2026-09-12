import pytest
from alphalens.ingestion.loaders import DatasetLoader
from alphalens.ingestion.currency import CurrencyNormalizer
from alphalens.validation.schema_validator import SchemaValidator


def test_load_profiles():
    loader = DatasetLoader()
    profiles = loader.load_profiles()
    assert len(profiles) == 275
    assert "user_01" in profiles
    user1 = profiles["user_01"]
    assert user1.home_currency == "ZAR"
    assert user1.current_available_balance == 58481.1
    assert user1.minimum_balance_to_keep == 18000.0
    assert "full_payment" in user1.payment_methods_user_will_consider
    assert user1.accepts_full_payment() is True


def test_load_requests():
    loader = DatasetLoader()
    eval_requests = loader.load_requests()
    assert len(eval_requests) == 250
    assert "request_26" in eval_requests

    sample_requests, expected = loader.load_sample_requests()
    assert len(sample_requests) == 25
    assert len(expected) == 25
    assert "request_01" in sample_requests
    assert expected["request_01"]["affordability_status"] == "affordable_now"


def test_load_events():
    loader = DatasetLoader()
    events = loader.load_events()
    assert len(events) == 25342
    
    # Exactly 16 events have missing amounts in the raw CSV
    missing_count = sum(1 for e in events.values() if e.amount is None)
    assert missing_count == 16

    # Check known event
    e = events["event_01"]
    assert e.user_id == "user_01"
    assert e.direction.value == "debit"


def test_load_payment_options():
    loader = DatasetLoader()
    options = loader.load_payment_options()
    assert len(options) == 275  # 250 eval + 25 samples
    total_options = sum(len(opts) for opts in options.values())
    assert total_options == 790
    assert len(options["request_01"]) == 4


def test_schema_validator_passes():
    loader = DatasetLoader()
    currency_norm = CurrencyNormalizer()
    validator = SchemaValidator(loader, currency_norm)
    result = validator.validate_all()
    assert result["valid"] is True
    assert len(result["errors"]) == 0
