import csv
import os
from typing import Dict, List, Optional, Tuple, Any
from ..models.profile import FinancialProfile
from ..models.event import FinancialEvent, EventStatus, EventDirection, EventFlexibility
from ..models.request import FinancialRequest, PaymentOption
from ..models.evidence import Provenance


class DatasetLoader:
    """Loads and validates all challenge CSV files into strongly-typed models."""

    def __init__(self, dataset_dir: str = "dataset"):
        self.dataset_dir = dataset_dir

    def load_profiles(self) -> Dict[str, FinancialProfile]:
        file_path = os.path.join(self.dataset_dir, "financial_profiles.csv")
        profiles: Dict[str, FinancialProfile] = {}
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                u_id = row["user_id"].strip()
                max_inst = row["max_installment_months"].strip()
                profiles[u_id] = FinancialProfile(
                    user_id=u_id,
                    home_currency=row["home_currency"].strip(),
                    current_available_balance=float(row["current_available_balance"].strip()),
                    minimum_balance_to_keep=float(row["minimum_balance_to_keep"].strip()),
                    financial_priorities=[
                        p.strip() for p in row["financial_priorities"].split("|") if p.strip()
                    ],
                    expense_categories_to_protect=[
                        c.strip() for c in row["expense_categories_to_protect"].split("|") if c.strip()
                    ],
                    expense_categories_user_is_willing_to_reduce=[
                        c.strip() for c in row["expense_categories_user_is_willing_to_reduce"].split("|") if c.strip()
                    ],
                    expense_categories_user_is_willing_to_stop=[
                        c.strip() for c in row["expense_categories_user_is_willing_to_stop"].split("|") if c.strip()
                    ],
                    payment_methods_user_will_consider=[
                        m.strip() for m in row["payment_methods_user_will_consider"].split("|") if m.strip()
                    ],
                    max_installment_months=int(max_inst) if max_inst else None,
                )
        return profiles

    def load_requests(self, filename: str = "requests.csv") -> Dict[str, FinancialRequest]:
        file_path = os.path.join(self.dataset_dir, filename)
        requests: Dict[str, FinancialRequest] = {}
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                req_id = row["request_id"].strip()
                allows_partial = row["allows_partial_payment"].strip().lower() in ("true", "1", "yes")
                requests[req_id] = FinancialRequest(
                    request_id=req_id,
                    user_id=row["user_id"].strip(),
                    request_date=row["request_date"].strip(),
                    request_type=row["request_type"].strip(),
                    requested_amount=float(row["requested_amount"].strip()),
                    desired_completion_date=row["desired_completion_date"].strip(),
                    allows_partial_payment=allows_partial,
                    request_text=row["request_text"].strip(),
                )
        return requests

    def load_sample_requests(self) -> Tuple[Dict[str, FinancialRequest], Dict[str, Dict[str, str]]]:
        file_path = os.path.join(self.dataset_dir, "sample_requests.csv")
        requests: Dict[str, FinancialRequest] = {}
        expected_outputs: Dict[str, Dict[str, str]] = {}
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                req_id = row["request_id"].strip()
                allows_partial = row["allows_partial_payment"].strip().lower() in ("true", "1", "yes")
                requests[req_id] = FinancialRequest(
                    request_id=req_id,
                    user_id=row["user_id"].strip(),
                    request_date=row["request_date"].strip(),
                    request_type=row["request_type"].strip(),
                    requested_amount=float(row["requested_amount"].strip()),
                    desired_completion_date=row["desired_completion_date"].strip(),
                    allows_partial_payment=allows_partial,
                    request_text=row["request_text"].strip(),
                )
                expected_outputs[req_id] = {
                    "amount_safe_to_pay": row["amount_safe_to_pay"].strip(),
                    "affordability_status": row["affordability_status"].strip(),
                    "recommended_payment_method": row["recommended_payment_method"].strip(),
                    "payment_plan": row["payment_plan"].strip(),
                    "earliest_date_for_full_payment": row["earliest_date_for_full_payment"].strip(),
                    "spending_changes_needed": row["spending_changes_needed"].strip(),
                    "decision_explanation": row["decision_explanation"].strip(),
                }
        return requests, expected_outputs

    def load_events(self) -> Dict[str, FinancialEvent]:
        file_path = os.path.join(self.dataset_dir, "financial_events.csv")
        events: Dict[str, FinancialEvent] = {}
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ev_id = row["event_id"].strip()
                amt_str = row["amount"].strip()
                amt = float(amt_str) if amt_str else None
                settlement = row["settlement_date"].strip()
                min_amt_str = row["minimum_allowed_amount"].strip()
                min_amt = float(min_amt_str) if min_amt_str else None
                linked_id = row["linked_event_id"].strip() or None

                events[ev_id] = FinancialEvent(
                    event_id=ev_id,
                    user_id=row["user_id"].strip(),
                    event_type=row["event_type"].strip(),
                    description=row["description"].strip(),
                    category=row["category"].strip(),
                    direction=EventDirection(row["direction"].strip()),
                    amount=amt,
                    currency=row["currency"].strip(),
                    event_date=row["event_date"].strip(),
                    settlement_date=settlement if settlement else None,
                    status=EventStatus(row["status"].strip()),
                    linked_event_id=linked_id,
                    flexibility=EventFlexibility(row["flexibility"].strip()),
                    minimum_allowed_amount=min_amt,
                    provenance=Provenance(source_type="financial_events.csv", source_id=ev_id),
                    raw_row=dict(row),
                )
        return events

    def load_payment_options(self) -> Dict[str, List[PaymentOption]]:
        file_path = os.path.join(self.dataset_dir, "request_payment_options.csv")
        options: Dict[str, List[PaymentOption]] = {}
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                req_id = row["request_id"].strip()
                freq = row["payment_frequency_days"].strip()
                opt = PaymentOption(
                    payment_option_id=row["payment_option_id"].strip(),
                    request_id=req_id,
                    payment_method=row["payment_method"].strip(),
                    payment_amount=float(row["payment_amount"].strip()),
                    number_of_payments=int(row["number_of_payments"].strip()),
                    first_payment_date=row["first_payment_date"].strip(),
                    payment_frequency_days=int(freq) if freq else None,
                    financing_fee=float(row["financing_fee"].strip()),
                    total_payable_amount=float(row["total_payable_amount"].strip()),
                )
                if req_id not in options:
                    options[req_id] = []
                options[req_id].append(opt)
        return options

    def load_messages_raw(self) -> List[Dict[str, str]]:
        file_path = os.path.join(self.dataset_dir, "messages.csv")
        with open(file_path, mode="r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def load_images_raw(self) -> List[Dict[str, str]]:
        file_path = os.path.join(self.dataset_dir, "images.csv")
        with open(file_path, mode="r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
