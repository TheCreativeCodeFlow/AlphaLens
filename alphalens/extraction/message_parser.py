import re
from typing import List, Optional, Dict, Any, Tuple
from ..models.evidence import MessageFact, FactType, FactStatus, Provenance


class MessageParser:
    """
    Parses unstructured financial notices (English and Bahasa Indonesia)
    into structured, traceable financial facts with temporal and status flags.
    """

    def parse_message(self, message_row: Dict[str, str]) -> MessageFact:
        msg_id = message_row.get("message_id", "").strip()
        u_id = message_row.get("user_id", "").strip()
        req_id = message_row.get("request_id", "").strip() or None
        ev_id = message_row.get("related_event_id", "").strip() or None
        source_type = message_row.get("source_type", "").strip()
        text = message_row.get("message_text", "").strip()

        provenance = Provenance(
            source_type="messages.csv",
            source_id=msg_id,
            raw_reference=f"user={u_id}, req={req_id}, ev={ev_id}",
            notes=f"Source: {source_type}",
        )

        # Check for prompt injection attempts
        is_suspicious, injection_reason = self._detect_prompt_injection(text)

        # Extract common entities
        entity = self._extract_entity(text, source_type)

        if is_suspicious:
            fact_type = FactType.OTHER
            status = FactStatus.FAILED
            amount = None
            currency = None
            effective_date = None
            percentage = None
            details = {
                "prompt_injection_flagged": True,
                "injection_reason": injection_reason,
            }
            if req_id:
                details["request_id"] = req_id
            if ev_id:
                details["related_event_id"] = ev_id
        else:
            ref_code = self._extract_ref_code(text)
            dates = self._extract_dates(text)
            currency, amount = self._extract_currency_amount(text)
            percentage = self._extract_percentage(text)

            effective_date = dates[0] if dates else None

            # Classify the fact type and status based on semantic patterns
            fact_type, status, details = self._classify_fact(text, source_type, currency, amount, percentage, dates)

            if percentage is None and "rent_increase_percent" in details:
                percentage = details["rent_increase_percent"]

            if ref_code:
                details["reference_code"] = ref_code
            if req_id:
                details["request_id"] = req_id
            if ev_id:
                details["related_event_id"] = ev_id

        return MessageFact(
            fact_type=fact_type,
            user_id=u_id,
            entity=entity,
            amount=amount,
            currency=currency,
            effective_date=effective_date,
            percentage_change=percentage,
            status=status,
            source_type=source_type,
            source_id=msg_id,
            confidence=0.95 if not is_suspicious else 0.4,
            provenance=provenance,
            raw_text=text,
            details=details,
        )

    def _detect_prompt_injection(self, text: str) -> Tuple[bool, Optional[str]]:
        lower = text.lower()
        suspicious_phrases = [
            "ignore previous instructions",
            "ignore all instructions",
            "system prompt",
            "system rules",
            "approve this purchase",
            "bypass safety",
            "return affordable_now",
            "return this answer",
            "change the system",
            "override balance",
            "admin override",
            "execute this command",
        ]
        for phrase in suspicious_phrases:
            if phrase in lower:
                return True, f"Detected injection pattern: '{phrase}'"
        return False, None

    def _extract_entity(self, text: str, source_type: str) -> str:
        known_entities = [
            "Cobalt Systems",
            "BrightPath Media",
            "Greenfield Foods",
            "Northstar Labs",
            "Riverline Retail",
            "HarborWorks",
            "Cedar Health",
            "StayLedger",
            "HomePortal",
            "QuickCrew",
            "RideGrid",
            "TaskSprint",
            "InvoiceFlow",
            "Summit Bank",
            "Cedar Bank",
            "Oakline Bank",
            "BluePeak Bank",
            "Northfield Bank",
            "Harbor Bank",
            "CartLane",
            "Everyday Store",
            "BuyBox",
            "ClearFund",
            "DrawPay",
            "PrizeTrack",
            "Nova Securities",
            "PocketVest",
            "StackWealth",
            "RewardNow",
        ]
        for ent in known_entities:
            if ent.lower() in text.lower():
                return ent
        return source_type

    def _extract_ref_code(self, text: str) -> Optional[str]:
        m = re.search(r"\b(EMP|SER|BAN|MER|FIN)-\d{4}\b", text)
        return m.group(0) if m else None

    def _extract_dates(self, text: str) -> List[str]:
        return re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)

    def _extract_currency_amount(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        m = re.search(r"\b(USD|IDR|INR|EUR|ZAR)\s+([\d,]+(?:\.\d+)?)\b", text)
        if m:
            curr = m.group(1)
            amt_str = m.group(2).replace(",", "")
            try:
                return curr, float(amt_str)
            except ValueError:
                pass
        return None, None

    def _extract_percentage(self, text: str) -> Optional[float]:
        m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if m:
            return float(m.group(1))
        return None

    def _classify_fact(
        self,
        text: str,
        source_type: str,
        currency: Optional[str],
        amount: Optional[float],
        percentage: Optional[float],
        dates: List[str],
    ) -> Tuple[FactType, FactStatus, Dict[str, Any]]:
        t = text.lower()
        details: Dict[str, Any] = {}

        # 1. Lease / Rent increase
        if "renewed lease increases" in t or "pembaruan sewa" in t or ("sewa" in t and "%" in t) or ("rent" in t and "%" in t):
            details["rent_increase_percent"] = percentage or 12.0
            return FactType.LEASE_RENT_INCREASE, FactStatus.CONFIRMED, details

        # 2. Account-to-account transfer
        if "transfer between your two accounts" in t or "transfer antara kedua rekening" in t or "transfer antara dua rekening" in t:
            details["is_internal_transfer"] = True
            details["exclude_from_income"] = True
            return FactType.ACCOUNT_TRANSFER, FactStatus.CONFIRMED, details

        # 3. Investment / Portfolio valuation (non-cash)
        if "portfolio" in t or "portofolio" in t or "no cash proceeds" in t or "nilai yang ditampilkan" in t or "tidak ada transaksi tunai" in t or "holding has not been sold" in t:
            details["is_liquid_cash"] = False
            details["status"] = "unrealized"
            return FactType.INVESTMENT_UNREALIZED, FactStatus.UNREALIZED, details

        # 4. Investment sale settled
        if "investment sale have settled" in t or "penjualan investasi telah diselesaikan" in t:
            details["is_settled_cash"] = True
            return FactType.CONFIRMED_INCOME, FactStatus.SETTLED, details

        # 5. Refund pending
        if "refund has been initiated" in t or "pengembalian dana anda telah dimulai" in t:
            details["is_settled_cash"] = False
            return FactType.REFUND_PENDING, FactStatus.PENDING, details

        # 6. Prize claims
        if "prize proceeds have reached" in t or "hasil hadiah telah masuk" in t or "claim is now closed" in t:
            details["is_recurring"] = False
            details["claim_closed"] = True
            return FactType.PRIZE_ONE_OFF, FactStatus.CLOSED, details
        if "prize claim" in t or "klaim hadiah" in t or "hadiah uang tunai" in t:
            details["is_settled_cash"] = False
            return FactType.PENDING_INCOME, FactStatus.PENDING, details

        # 7. Seasonal contract ended
        if "seasonal contract has ended" in t or "kontrak musiman saat ini telah berakhir" in t:
            details["future_salary_discontinued"] = True
            return FactType.SEASONAL_ENDED, FactStatus.CLOSED, details

        # 8. Gig platform pending payout
        if "payout is still pending" in t or "pembayaran berikutnya dari" in t or "not withdrawable until" in t:
            details["is_withdrawable"] = False
            return FactType.PENDING_INCOME, FactStatus.PENDING, details

        # 9. Invoice payment approved
        if "approved an invoice payment" in t or "menyetujui pembayaran faktur" in t:
            return FactType.CONFIRMED_INCOME, FactStatus.CONFIRMED, details

        # 10. Failed debit retry
        if "previous debit attempt failed" in t or "upaya pendebetan sebelumnya gagal" in t:
            details["will_retry_debit"] = True
            return FactType.DEBIT_RETRY, FactStatus.PENDING, details

        # 11. Card dispute open
        if "dispute is open" in t or "sengketa masih terbuka" in t or "still being investigated" in t or "masih dalam penyelidikan" in t:
            details["reversal_credited"] = False
            return FactType.DISPUTE_PENDING, FactStatus.PENDING, details

        # 12. Foreign currency note
        if "foreign currency" in t or "mata uang asing" in t:
            details["requires_settlement_rate"] = True
            return FactType.FOREIGN_CURRENCY_CHARGE, FactStatus.ANNOUNCED, details

        # 13. Bonus pending
        if "bonus" in t and ("pending" in t or "menunggu" in t or "belum disetujui" in t or "not approved" in t):
            details["is_confirmed"] = False
            return FactType.PENDING_INCOME, FactStatus.PENDING, details

        # 14. Commission unapproved
        if ("commission" in t or "komisi" in t) and ("unapproved" in t or "belum disetujui" in t):
            details["commission_unapproved"] = True
            return FactType.PENDING_INCOME, FactStatus.PENDING, details

        # 15. Regular salary resumes with new deduction
        if ("resumes on" in t or "dimulai kembali pada" in t) and ("childcare" in t or "penitipan anak" in t):
            details["new_recurring_deduction"] = "childcare"
            return FactType.CONFIRMED_INCOME, FactStatus.CONFIRMED, details

        # 16. Salary reduction / unpaid leave
        if "reduced to" in t or "dipotong menjadi" in t or "unpaid leave" in t or "cuti di luar tanggungan" in t or "temporary monthly pay" in t or "gaji sementara" in t:
            details["temporary_adjustment"] = True
            return FactType.SALARY_REDUCED, FactStatus.CONFIRMED, details

        # 17. Salary date change
        if "now expected on" in t or "bergeser ke" in t or "replaces the payroll date" in t:
            details["payroll_date_revised"] = True
            return FactType.SALARY_DATE_CHANGE, FactStatus.CONFIRMED, details

        # 18. General Salary update (e.g. increase or confirmation)
        if any(k in t for k in ["salary", "gaji", "payroll", "pay"]):
            if "naik menjadi" in t or "increases to" in t or "is now" in t:
                details["salary_increase"] = True
            return FactType.SALARY_UPDATE, FactStatus.CONFIRMED, details

        return FactType.OTHER, FactStatus.ANNOUNCED, details
