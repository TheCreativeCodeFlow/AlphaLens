import pytest
from alphalens.extraction.image_extractor import ImageEvidenceExtractor


def test_image_extraction_payslip():
    extractor = ImageEvidenceExtractor()
    evidence = extractor.extract_evidence(
        image_id="image_01",
        event_id="event_253",
        user_id="user_03",
        request_id="request_03",
    )
    assert evidence.amount == 4365000.0
    assert evidence.currency == "IDR"
    assert evidence.confidence >= 0.95
    assert evidence.provenance is not None
    assert evidence.provenance.source_id == "image_01"


def test_image_extraction_rent_receipt():
    extractor = ImageEvidenceExtractor()
    evidence = extractor.extract_evidence(
        image_id="image_02",
        event_id="event_1442",
        user_id="user_16",
        request_id="request_16",
        event_context={"description": "Outstanding rent balance"},
    )
    assert evidence.amount == 100000.0
    assert evidence.currency == "INR"
    assert evidence.confidence >= 0.95


def test_image_extraction_telecom_bill():
    extractor = ImageEvidenceExtractor()
    evidence = extractor.extract_evidence(
        image_id="image_05",
        event_id="event_1786",
        user_id="user_20",
        request_id="request_20",
    )
    assert evidence.amount == 704.05
    assert evidence.currency == "INR"


def test_image_extraction_taxi():
    extractor = ImageEvidenceExtractor()
    evidence = extractor.extract_evidence(
        image_id="image_12",
        event_id="event_7307",
        user_id="user_78",
        request_id="request_78",
    )
    assert evidence.amount == 33.50
    assert evidence.currency == "USD"


def test_image_evidence_does_not_determine_affordability():
    """
    Regression test verifying architectural separation:
    Image evidence strictly extracts document attributes (amount, currency, provenance)
    and has zero authority/fields for affordability status, payment plans, or recommendations.
    """
    extractor = ImageEvidenceExtractor()
    evidence = extractor.extract_evidence(
        image_id="image_01",
        event_id="event_253",
        user_id="user_03",
        request_id="request_03",
    )
    # Evidence must ONLY contain factual document attributes
    assert hasattr(evidence, "amount")
    assert hasattr(evidence, "currency")
    assert hasattr(evidence, "provenance")
    assert evidence.amount == 4365000.0

    # Evidence object MUST NOT possess decision engine fields
    assert not hasattr(evidence, "affordability_status")
    assert not hasattr(evidence, "amount_safe_to_pay")
    assert not hasattr(evidence, "recommended_payment_method")
    assert not hasattr(evidence, "payment_plan")
    assert not hasattr(evidence, "spending_changes_needed")
