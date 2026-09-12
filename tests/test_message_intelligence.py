import pytest
from alphalens.extraction.message_parser import MessageParser
from alphalens.models.evidence import FactType, FactStatus


def test_parse_english_salary_increase():
    parser = MessageParser()
    row = {
        "message_id": "msg_test_01",
        "user_id": "user_99",
        "request_id": "",
        "related_event_id": "",
        "source_type": "employer",
        "message_text": "Your monthly salary increases to ZAR 34,980 effective from 2026-04-15. Ref payroll EMP-0099.",
    }
    fact = parser.parse_message(row)
    assert fact.fact_type == FactType.SALARY_UPDATE
    assert fact.status == FactStatus.CONFIRMED
    assert fact.amount == 34980.0
    assert fact.currency == "ZAR"
    assert fact.effective_date == "2026-04-15"
    assert fact.provenance.source_id == "msg_test_01"


def test_parse_indonesian_salary_increase():
    parser = MessageParser()
    row = {
        "message_id": "msg_test_02",
        "user_id": "user_02",
        "request_id": "",
        "related_event_id": "",
        "source_type": "employer",
        "message_text": "Rincian penggajian Anda di Cobalt Systems telah berubah. Gaji bulanan Anda naik menjadi IDR 42750000. Perubahan ini berlaku mulai 2025-08-15. Ref payroll EMP-0001.",
    }
    fact = parser.parse_message(row)
    assert fact.fact_type == FactType.SALARY_UPDATE
    assert fact.status == FactStatus.CONFIRMED
    assert fact.amount == 42750000.0
    assert fact.currency == "IDR"
    assert fact.effective_date == "2025-08-15"
    assert fact.entity == "Cobalt Systems"


def test_parse_rent_lease_increase():
    parser = MessageParser()
    row = {
        "message_id": "msg_test_03",
        "user_id": "user_16",
        "request_id": "request_16",
        "related_event_id": "",
        "source_type": "service_provider",
        "message_text": "StayLedger wanted to let you know about a change on your account. The renewed lease increases monthly rent by 12%. The new amount will be used for the next rent payment. Case ref SER-0012.",
    }
    fact = parser.parse_message(row)
    assert fact.fact_type == FactType.LEASE_RENT_INCREASE
    assert fact.percentage_change == 12.0
    assert fact.entity == "StayLedger"


def test_parse_account_transfer():
    parser = MessageParser()
    row = {
        "message_id": "msg_test_04",
        "user_id": "user_18",
        "request_id": "request_18",
        "related_event_id": "",
        "source_type": "bank",
        "message_text": "There’s an update from Summit Bank on your recent account activity. The matching debit and credit came from a transfer between your two accounts. Both accounts are registered under the same account holder. Txn ref BAN-0013.",
    }
    fact = parser.parse_message(row)
    assert fact.fact_type == FactType.ACCOUNT_TRANSFER
    assert fact.details.get("is_internal_transfer") is True


def test_parse_unrealized_portfolio():
    parser = MessageParser()
    row = {
        "message_id": "msg_test_05",
        "user_id": "user_22",
        "request_id": "request_22",
        "related_event_id": "event_1960",
        "source_type": "financial_service",
        "message_text": "Here’s the latest account information from ClearFund. Your portfolio’s displayed market value has increased substantially. No units have been sold and no cash proceeds have been generated. Account ref FIN-0015.",
    }
    fact = parser.parse_message(row)
    assert fact.fact_type == FactType.INVESTMENT_UNREALIZED
    assert fact.status == FactStatus.UNREALIZED
    assert fact.details.get("is_liquid_cash") is False


def test_parse_pending_gig_payout():
    parser = MessageParser()
    row = {
        "message_id": "msg_test_06",
        "user_id": "user_10",
        "request_id": "request_10",
        "related_event_id": "",
        "source_type": "service_provider",
        "message_text": "Here’s the latest service update from QuickCrew. The next QuickCrew payout is still pending. The weekly earnings shown in the QuickCrew app can change until the payout is closed. The balance isn’t withdrawable until the payout shows as completed. Case ref SER-0007.",
    }
    fact = parser.parse_message(row)
    assert fact.fact_type == FactType.PENDING_INCOME
    assert fact.status == FactStatus.PENDING
    assert fact.details.get("is_withdrawable") is False
