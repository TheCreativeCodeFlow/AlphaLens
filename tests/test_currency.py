import pytest
from alphalens.ingestion.currency import CurrencyNormalizer


def test_currency_conversion_identity():
    norm = CurrencyNormalizer()
    converted, rate, dt = norm.convert(100.0, "EUR", "EUR", "2024-01-15")
    assert converted == 100.0
    assert rate == 1.0


def test_currency_conversion_dated():
    norm = CurrencyNormalizer()
    # 2023-10-15: USD -> EUR rate is 0.92
    converted, rate, dt = norm.convert(100.0, "USD", "EUR", "2023-10-15")
    assert converted == 92.0
    assert rate == 0.92
    assert dt == "2023-10-15"

    # 2023-10-15: EUR -> ZAR rate is 20.0
    converted_zar, rate_zar, _ = norm.convert(50.0, "EUR", "ZAR", "2023-10-15")
    assert converted_zar == 1000.0
    assert rate_zar == 20.0


def test_currency_conversion_missing_rate():
    norm = CurrencyNormalizer()
    with pytest.raises(ValueError, match="No exchange rate found"):
        norm.convert(100.0, "EUR", "JPY", "2024-01-15")
