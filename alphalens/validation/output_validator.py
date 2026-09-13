import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from ..models.profile import FinancialProfile
from ..models.request import FinancialRequest
from ..models.event import FinancialEvent


VALID_STATUSES = {
    "affordable_now",
    "affordable_with_plan",
    "affordable_later",
    "not_affordable",
}

VALID_METHODS = {
    "full_payment",
    "partial_payment",
    "installments",
    "wait",
    "not_recommended",
}

REQUIRED_COLUMNS = [
    "request_id",
    "amount_safe_to_pay",
    "affordability_status",
    "recommended_payment_method",
    "payment_plan",
    "earliest_date_for_full_payment",
    "spending_changes_needed",
    "decision_explanation",
]


class OutputValidationError:
    def __init__(self, request_id: str, field: str, error_type: str, message: str):
        self.request_id = request_id
        self.field = field
        self.error_type = error_type
        self.message = message

    def __repr__(self) -> str:
        return f"[{self.request_id}] {self.field} ({self.error_type}): {self.message}"


class OutputValidator:
    """
    Independent validator that rigorously checks any generated output.csv against:
    1. Exact column headers and order
    2. Exact row count matching requests dataset
    3. Types, value ranges, and permissible enums
    4. Plan syntax, date formatting, and payment sums
    5. Partial payment and installment rules
    6. Spending changes format, count, and profile permissions
    7. Semantic coherence (e.g. affordable_now -> earliest_date == request_date)
    """

    def __init__(
        self,
        profiles: Optional[Dict[str, FinancialProfile]] = None,
        requests: Optional[Dict[str, FinancialRequest]] = None,
        events: Optional[Dict[str, FinancialEvent]] = None,
        payment_options: Optional[Dict[str, List[Any]]] = None,
    ):
        self.profiles = profiles or {}
        self.requests = requests or {}
        self.events = events or {}
        self.payment_options = payment_options or {}

    def validate_file(self, file_path: str, expected_count: Optional[int] = None) -> Tuple[bool, List[OutputValidationError]]:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return False, [OutputValidationError("FILE", "header", "EMPTY_FILE", "The output file is completely empty")]

        header = rows[0]
        if header != REQUIRED_COLUMNS:
            return False, [
                OutputValidationError(
                    "FILE",
                    "header",
                    "INVALID_HEADER",
                    f"Expected columns {REQUIRED_COLUMNS}, got {header}",
                )
            ]

        dict_rows = []
        for i, r in enumerate(rows[1:], start=2):
            if len(r) != len(REQUIRED_COLUMNS):
                return False, [
                    OutputValidationError(
                        f"ROW_{i}",
                        "columns",
                        "COLUMN_COUNT_MISMATCH",
                        f"Row {i} has {len(r)} columns, expected {len(REQUIRED_COLUMNS)}",
                    )
                ]
            dict_rows.append(dict(zip(REQUIRED_COLUMNS, r)))

        return self.validate_rows(dict_rows, expected_count=expected_count)

    def validate_rows(
        self, rows: List[Dict[str, str]], expected_count: Optional[int] = None
    ) -> Tuple[bool, List[OutputValidationError]]:
        errors: List[OutputValidationError] = []

        if expected_count is not None and len(rows) != expected_count:
            errors.append(
                OutputValidationError(
                    "DATASET",
                    "row_count",
                    "ROW_COUNT_MISMATCH",
                    f"Expected {expected_count} rows, found {len(rows)}",
                )
            )

        seen_ids: Set[str] = set()
        for i, row in enumerate(rows):
            req_id = row.get("request_id", f"ROW_{i+1}").strip()
            if not req_id:
                errors.append(OutputValidationError(f"ROW_{i+1}", "request_id", "MISSING_ID", "Empty request_id"))
                continue

            if req_id in seen_ids:
                errors.append(OutputValidationError(req_id, "request_id", "DUPLICATE_ID", f"Duplicate request_id: {req_id}"))
            seen_ids.add(req_id)

            req = self.requests.get(req_id)
            user = self.profiles.get(req.user_id) if req else None

            # 1. amount_safe_to_pay
            safe_str = row.get("amount_safe_to_pay", "").strip()
            try:
                safe_amt = float(safe_str)
                if safe_amt < 0.0:
                    errors.append(OutputValidationError(req_id, "amount_safe_to_pay", "NEGATIVE_AMOUNT", f"amount_safe_to_pay cannot be negative: {safe_amt}"))
                if req and safe_amt > req.requested_amount + 0.01:
                    errors.append(OutputValidationError(req_id, "amount_safe_to_pay", "EXCEEDS_REQUESTED", f"amount_safe_to_pay {safe_amt} exceeds requested amount {req.requested_amount}"))
            except ValueError:
                errors.append(OutputValidationError(req_id, "amount_safe_to_pay", "INVALID_FLOAT", f"Invalid float for amount_safe_to_pay: '{safe_str}'"))

            # 2. affordability_status
            status = row.get("affordability_status", "").strip()
            if status not in VALID_STATUSES:
                errors.append(OutputValidationError(req_id, "affordability_status", "INVALID_ENUM", f"Invalid status: '{status}'. Must be one of {VALID_STATUSES}"))

            # 3. recommended_payment_method
            method = row.get("recommended_payment_method", "").strip()
            if method not in VALID_METHODS:
                errors.append(OutputValidationError(req_id, "recommended_payment_method", "INVALID_ENUM", f"Invalid method: '{method}'. Must be one of {VALID_METHODS}"))

            # 4. earliest_date_for_full_payment
            earliest_date = row.get("earliest_date_for_full_payment", "").strip()
            if status == "affordable_now":
                if req and earliest_date != req.request_date:
                    errors.append(OutputValidationError(req_id, "earliest_date_for_full_payment", "DATE_MISMATCH", f"affordable_now must have earliest_date equal to request_date ({req.request_date}), got '{earliest_date}'"))
            elif status == "not_affordable":
                if earliest_date != "":
                    errors.append(OutputValidationError(req_id, "earliest_date_for_full_payment", "NON_EMPTY_DATE", f"not_affordable must have empty earliest_date_for_full_payment, got '{earliest_date}'"))
            elif earliest_date:
                try:
                    datetime.strptime(earliest_date, "%Y-%m-%d")
                except ValueError:
                    errors.append(OutputValidationError(req_id, "earliest_date_for_full_payment", "INVALID_DATE_FORMAT", f"Invalid date format for earliest_date: '{earliest_date}'"))

            # 5. payment_plan
            plan_str = row.get("payment_plan", "").strip()
            if status == "not_affordable" or method == "not_recommended":
                if plan_str != "none":
                    errors.append(OutputValidationError(req_id, "payment_plan", "PLAN_NOT_NONE", f"Status '{status}' / method '{method}' must have payment_plan='none', got '{plan_str}'"))
            else:
                if plan_str == "none":
                    errors.append(OutputValidationError(req_id, "payment_plan", "UNEXPECTED_NONE", f"Affordable status '{status}' must have a valid payment_plan, not 'none'"))
                else:
                    items = plan_str.split("|")
                    total_plan_amt = 0.0
                    parsed_dates = []
                    valid_plan_syntax = True
                    for item in items:
                        parts = item.split(":")
                        if len(parts) != 2:
                            errors.append(OutputValidationError(req_id, "payment_plan", "INVALID_PLAN_SYNTAX", f"Item '{item}' not in YYYY-MM-DD:amount format"))
                            valid_plan_syntax = False
                            continue
                        d_str, a_str = parts[0].strip(), parts[1].strip()
                        try:
                            d_val = datetime.strptime(d_str, "%Y-%m-%d").date()
                            parsed_dates.append(d_val)
                        except ValueError:
                            errors.append(OutputValidationError(req_id, "payment_plan", "INVALID_PLAN_DATE", f"Invalid date in plan: '{d_str}'"))
                            valid_plan_syntax = False
                        try:
                            a_val = float(a_str)
                            total_plan_amt += a_val
                            if a_val <= 0.0:
                                errors.append(OutputValidationError(req_id, "payment_plan", "NON_POSITIVE_PAYMENT", f"Payment amount must be positive: {a_val}"))
                        except ValueError:
                            errors.append(OutputValidationError(req_id, "payment_plan", "INVALID_PLAN_AMOUNT", f"Invalid amount in plan: '{a_str}'"))
                            valid_plan_syntax = False

                    if valid_plan_syntax:
                        # Check chronological ordering
                        if parsed_dates != sorted(parsed_dates):
                            errors.append(OutputValidationError(req_id, "payment_plan", "NOT_CHRONOLOGICAL", f"Payment dates are not strictly chronological: {plan_str}"))

                        # Check sum matches requested_amount (or option payable amount for installments)
                        if req:
                            if method == "installments" and req_id in self.payment_options:
                                matched_opt = False
                                for opt in self.payment_options[req_id]:
                                    if opt.is_installment() and abs(total_plan_amt - opt.total_payable_amount) <= 1.0:
                                        matched_opt = True
                                        break
                                if not matched_opt:
                                    errors.append(OutputValidationError(req_id, "payment_plan", "INSTALLMENT_OPTION_MISMATCH", f"Total installment plan amount {total_plan_amt} does not match any available installment option for request {req_id}"))
                            else:
                                if abs(total_plan_amt - req.requested_amount) > 1.0:
                                    errors.append(OutputValidationError(req_id, "payment_plan", "SUM_MISMATCH", f"Total plan amount {total_plan_amt} != requested amount {req.requested_amount}"))

                        # Partial payment checks
                        if method == "partial_payment":
                            if len(items) != 2:
                                errors.append(OutputValidationError(req_id, "payment_plan", "INVALID_PARTIAL_COUNT", f"partial_payment must have exactly 2 installments, got {len(items)}"))
                            elif req and user:
                                p1_date, p1_amt = items[0].split(":")
                                p2_date, p2_amt = items[1].split(":")
                                if p1_date != req.request_date:
                                    errors.append(OutputValidationError(req_id, "payment_plan", "PARTIAL_DATE1_MISMATCH", f"First partial payment must be on request_date {req.request_date}, got {p1_date}"))
                                if p2_date != earliest_date:
                                    errors.append(OutputValidationError(req_id, "payment_plan", "PARTIAL_DATE2_MISMATCH", f"Second partial payment must be on earliest_date {earliest_date}, got {p2_date}"))
                                if p2_date > req.desired_completion_date:
                                    errors.append(OutputValidationError(req_id, "payment_plan", "PARTIAL_DEADLINE_BREACH", f"Second partial payment {p2_date} is after desired_completion_date {req.desired_completion_date}"))

            # 6. spending_changes_needed
            sc_str = row.get("spending_changes_needed", "").strip()
            if sc_str != "none":
                actions = sc_str.split("|")
                if len(actions) > 3:
                    errors.append(OutputValidationError(req_id, "spending_changes_needed", "TOO_MANY_ACTIONS", f"Max 3 spending changes allowed, got {len(actions)}"))
                for act in actions:
                    act = act.strip()
                    if act.startswith("stop:"):
                        ev_id = act.split(":")[1].strip()
                        if self.events and ev_id not in self.events:
                            errors.append(OutputValidationError(req_id, "spending_changes_needed", "UNKNOWN_EVENT", f"Stop event {ev_id} not found in financial_events"))
                        elif self.events and user:
                            ev = self.events[ev_id]
                            if ev.category in user.expense_categories_to_protect:
                                errors.append(OutputValidationError(req_id, "spending_changes_needed", "PROTECTED_CATEGORY", f"Cannot stop protected category {ev.category} in event {ev_id}"))
                            if ev.category not in user.expense_categories_user_is_willing_to_stop:
                                errors.append(OutputValidationError(req_id, "spending_changes_needed", "DISALLOWED_CATEGORY", f"Category {ev.category} not in willing_to_stop list for event {ev_id}"))
                    elif act.startswith("reduce_to:"):
                        parts = act.split(":")
                        if len(parts) != 3:
                            errors.append(OutputValidationError(req_id, "spending_changes_needed", "INVALID_REDUCE_SYNTAX", f"reduce_to syntax invalid: '{act}'"))
                        else:
                            ev_id, new_amt_str = parts[1].strip(), parts[2].strip()
                            if self.events and ev_id not in self.events:
                                errors.append(OutputValidationError(req_id, "spending_changes_needed", "UNKNOWN_EVENT", f"Reduce event {ev_id} not found in financial_events"))
                            elif self.events and user:
                                ev = self.events[ev_id]
                                if ev.category in user.expense_categories_to_protect:
                                    errors.append(OutputValidationError(req_id, "spending_changes_needed", "PROTECTED_CATEGORY", f"Cannot reduce protected category {ev.category} in event {ev_id}"))
                                if ev.category not in user.expense_categories_user_is_willing_to_reduce:
                                    errors.append(OutputValidationError(req_id, "spending_changes_needed", "DISALLOWED_CATEGORY", f"Category {ev.category} not in willing_to_reduce list for event {ev_id}"))
                    else:
                        errors.append(OutputValidationError(req_id, "spending_changes_needed", "INVALID_ACTION_TYPE", f"Unknown action: '{act}'"))

            # 7. decision_explanation
            exp_str = row.get("decision_explanation", "").strip()
            if not exp_str:
                errors.append(OutputValidationError(req_id, "decision_explanation", "EMPTY_EXPLANATION", "Explanation is empty"))
            elif len(exp_str) > 500:
                errors.append(OutputValidationError(req_id, "decision_explanation", "EXPLANATION_TOO_LONG", f"Explanation exceeds 500 characters: {len(exp_str)}"))

        return len(errors) == 0, errors
