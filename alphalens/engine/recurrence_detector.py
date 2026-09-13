import calendar
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Set, Tuple

from ..models.event import FinancialEvent, EventDirection, EventFlexibility
from ..models.evidence import MessageFact, FactType
from ..models.state import ScheduledCashFlow


@dataclass
class RecurringSeries:
    """
    Represents a recognized recurring cash flow series with cadence and projection rules.
    """
    series_id: str
    category: str
    description: str
    direction: EventDirection
    cadence: str  # "monthly" or "interval"
    interval_days: int  # 7, 10, 14, 21, 28, 30
    day_of_month: Optional[int]
    base_amount: float
    original_amount: float
    original_currency: str
    flexibility: EventFlexibility
    minimum_allowed_amount: Optional[float]
    source_event_id: str
    latest_event_date: str
    occurrence_count: int
    confidence: float
    amendment_type: Optional[str] = None
    amended_amount: Optional[float] = None
    amendment_effective_date: Optional[str] = None
    is_halted: bool = False


class RecurrenceDetector:
    """
    Detects recurring commitments from historical transactions and applies
    evidence-based message amendments (salary revisions, rent lease increases, etc.).
    """

    def detect_series(
        self,
        events: List[FinancialEvent],
        request_date_str: str,
        messages: Optional[List[MessageFact]] = None,
    ) -> List[RecurringSeries]:
        """
        Identifies recurring series from historical settled transactions and confirmed scheduled salary.
        """
        # Include settled cash flows and confirmed scheduled salary events
        hist_events = [
            e for e in events
            if (e.is_settled or (e.status.value == "scheduled" and e.category == "salary"))
            and e.is_cash_flow
            and e.amount is not None
        ]

        # Group by category, isolating regular primary salary from bonuses, arrears, and secondary income
        grouped: Dict[str, List[FinancialEvent]] = defaultdict(list)
        for e in hist_events:
            if e.category == "salary":
                desc_lower = (e.description or "").lower()
                if any(w in desc_lower for w in ["bonus", "commission", "komisi", "arrears"]):
                    continue
                stream = "secondary" if "second" in desc_lower else "primary"
                grouped[f"salary_{stream}"].append(e)
            else:
                grouped[e.category].append(e)

        detected: List[RecurringSeries] = []
        series_counter = 0
        req_dt = datetime.strptime(request_date_str, "%Y-%m-%d").date()

        for group_key, ev_list in grouped.items():
            cat = "salary" if group_key.startswith("salary_") else group_key
            if len(ev_list) < 2:
                continue

            ev_list.sort(key=lambda x: x.effective_date)
            latest_event = ev_list[-1]
            latest_dt = datetime.strptime(latest_event.effective_date, "%Y-%m-%d").date()

            # Lapsed series check: if a monthly series has not occurred in > 45 days, it has lapsed
            if (req_dt - latest_dt).days > 45:
                continue

            dates = [datetime.strptime(e.event_date, "%Y-%m-%d") for e in ev_list]
            diffs = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
            pos_diffs = [d for d in diffs if d > 0]
            if not pos_diffs:
                continue

            avg_diff = sum(pos_diffs) / len(pos_diffs)
            doms = [d.day for d in dates]
            most_common_dom = max(set(doms), key=doms.count)
            dom_pct = doms.count(most_common_dom) / len(doms)

            all_amts = [(e.converted_amount or e.amount or 0.0) for e in ev_list]
            most_common_amt = max(set(all_amts), key=all_amts.count)
            recent_amts = [
                (e.converted_amount or e.amount or 0.0) for e in ev_list[-2:]
            ]
            if len(set(recent_amts)) == 1:
                effective_base_amt = recent_amts[-1]
            else:
                effective_base_amt = most_common_amt

            # Check if employment has terminated (e.g. "Final employer payroll")
            is_final_payroll = any(
                "final" in (e.description or "").lower() and "payroll" in (e.description or "").lower()
                for e in ev_list
            )

            # 1. Monthly series: same day of month (>= 70%) or average interval 27-33 days
            if dom_pct >= 0.7 or (27 <= avg_diff <= 33):
                series_counter += 1
                series = RecurringSeries(
                    series_id=f"rec_series_{series_counter}",
                    category=cat,
                    description=latest_event.description,
                    direction=latest_event.direction,
                    cadence="monthly",
                    interval_days=30,
                    day_of_month=most_common_dom,
                    base_amount=effective_base_amt,
                    original_amount=latest_event.amount or 0.0,
                    original_currency=latest_event.currency,
                    flexibility=latest_event.flexibility,
                    minimum_allowed_amount=latest_event.minimum_allowed_amount,
                    source_event_id=latest_event.event_id,
                    latest_event_date=latest_event.effective_date,
                    occurrence_count=len(ev_list),
                    confidence=0.95 if dom_pct >= 0.8 else 0.85,
                    is_halted=is_final_payroll,
                    amendment_effective_date=latest_event.effective_date if is_final_payroll else None,
                )
                detected.append(series)

            # 2. Regular interval series (groceries, transport, dining every 5, 7, 10, 14, 21 days)
            elif 4 <= avg_diff <= 25 and len(ev_list) >= 3:
                # Interval series: calculate median positive recent interval
                recent_pos = [d for d in diffs[-6:] if d > 0]
                interval = round(statistics.median(recent_pos)) if recent_pos else round(avg_diff)
                # Base amount: median of recent occurrences
                recent_amts = [
                    (e.converted_amount or e.amount or 0.0)
                    for e in ev_list[-6:]
                ]
                avg_amt = statistics.median(recent_amts) if recent_amts else (sum(all_amts) / len(all_amts))

                series_counter += 1
                series = RecurringSeries(
                    series_id=f"rec_series_{series_counter}",
                    category=cat,
                    description=latest_event.description,
                    direction=latest_event.direction,
                    cadence="interval",
                    interval_days=interval,
                    day_of_month=None,
                    base_amount=avg_amt,
                    original_amount=latest_event.amount or 0.0,
                    original_currency=latest_event.currency,
                    flexibility=latest_event.flexibility,
                    minimum_allowed_amount=latest_event.minimum_allowed_amount,
                    source_event_id=latest_event.event_id,
                    latest_event_date=latest_event.effective_date,
                    occurrence_count=len(ev_list),
                    confidence=0.90,
                    is_halted=is_final_payroll,
                )
                detected.append(series)

        # Apply message-derived amendments
        if messages:
            self._apply_message_amendments(detected, messages)

        # Exclude non-contractual discretionary spending categories from ongoing recurring commitments
        discretionary = {"dining", "shopping", "entertainment", "travel"}
        detected = [s for s in detected if s.category not in discretionary]

        return detected

    def _apply_message_amendments(
        self, series_list: List[RecurringSeries], messages: List[MessageFact]
    ):
        """
        Applies structured message amendments (salary updates, rent increases, cancellations)
        to the matching recurring series.
        """
        for fact in messages:
            if fact.fact_type == FactType.SALARY_UPDATE or fact.fact_type == FactType.SALARY_REDUCED:
                for s in series_list:
                    if s.category == "salary" and fact.amount is not None:
                        s.amendment_type = fact.fact_type.value
                        s.amended_amount = fact.amount
                        s.amendment_effective_date = fact.effective_date

            elif fact.fact_type == FactType.SEASONAL_ENDED:
                for s in series_list:
                    if s.category == "salary":
                        s.is_halted = True
                        s.amendment_effective_date = fact.effective_date

            elif fact.fact_type == FactType.PENDING_INCOME:
                # Gig / freelance earnings that are pending and unwithdrawable
                for s in series_list:
                    desc = (s.description or "").lower()
                    if s.category in ("freelance", "gig") or any(
                        w in desc for w in ["platform", "marketplace", "payout", "driver", "crew", "gig", "freelance"]
                    ):
                        s.is_halted = True
                        s.amendment_effective_date = fact.effective_date

            elif fact.fact_type == FactType.SALARY_DATE_CHANGE and fact.effective_date:
                try:
                    new_dom = int(fact.effective_date.split("-")[2])
                    for s in series_list:
                        if s.category == "salary":
                            s.day_of_month = new_dom
                except Exception:
                    pass

            elif fact.fact_type == FactType.LEASE_RENT_INCREASE:
                for s in series_list:
                    if s.category == "rent":
                        pct = fact.percentage_change or 0.0
                        new_amt = round(s.base_amount * (1.0 + (pct / 100.0)), 2)
                        s.amendment_type = "lease_rent_increase"
                        s.amended_amount = new_amt
                        s.amendment_effective_date = fact.effective_date


    def project_flows(
        self,
        series_list: List[RecurringSeries],
        request_date_str: str,
        horizon_days: int = 90,
        existing_scheduled_dates: Optional[Set[Tuple[str, str]]] = None,
    ) -> List[ScheduledCashFlow]:
        """
        Projects future cash flows for each series across [request_date, request_date + horizon_days].
        Skips dates where an event is already explicitly scheduled in financial_events.csv.
        """
        scheduled_set = existing_scheduled_dates or set()
        req_date = datetime.strptime(request_date_str, "%Y-%m-%d").date()
        end_date = req_date + timedelta(days=horizon_days)

        projected: List[ScheduledCashFlow] = []

        for s in series_list:
            if s.is_halted and (not s.amendment_effective_date or s.amendment_effective_date <= request_date_str):
                continue

            if s.cadence == "monthly" and s.day_of_month is not None:
                # Project monthly on day_of_month for up to 4 calendar months
                current_year = req_date.year
                current_month = req_date.month
                applied_reduced = False

                for m_offset in range(5):
                    month = current_month + m_offset
                    year = current_year + (month - 1) // 12
                    month = ((month - 1) % 12) + 1

                    # Clamp day of month to maximum days in month
                    max_day = calendar.monthrange(year, month)[1]
                    day = min(s.day_of_month, max_day)
                    target_dt = date(year, month, day)

                    if target_dt < req_date:
                        continue
                    if target_dt > end_date:
                        break

                    dt_str = target_dt.strftime("%Y-%m-%d")

                    # Avoid duplicate if already explicitly scheduled
                    if (dt_str, s.category) in scheduled_set:
                        continue

                    # Determine effective amount (accounting for message amendments)
                    amt = s.base_amount
                    if s.amendment_type == "salary_reduced":
                        if not applied_reduced:
                            amt = s.amended_amount if s.amended_amount is not None else s.base_amount
                            applied_reduced = True
                        else:
                            amt = s.base_amount
                    elif s.amended_amount is not None:
                        if not s.amendment_effective_date or dt_str >= s.amendment_effective_date:
                            amt = s.amended_amount

                    if s.is_halted and (not s.amendment_effective_date or dt_str >= s.amendment_effective_date):
                        continue

                    flow = ScheduledCashFlow(
                        flow_id=f"proj_{s.source_event_id}_{dt_str}",
                        date=dt_str,
                        amount=amt,
                        original_amount=s.original_amount,
                        original_currency=s.original_currency,
                        direction=s.direction,
                        category=s.category,
                        description=s.description,
                        source_event_id=s.source_event_id,
                        is_confirmed=True,
                        is_recurring=True,
                        flexibility=s.flexibility,
                        minimum_allowed_amount=s.minimum_allowed_amount,
                    )
                    projected.append(flow)

            elif s.cadence == "interval" and s.interval_days > 0:
                # Step forward from latest historical event date
                latest_dt = datetime.strptime(s.latest_event_date, "%Y-%m-%d").date()
                curr_dt = latest_dt + timedelta(days=s.interval_days)

                while curr_dt <= end_date:
                    dt_str = curr_dt.strftime("%Y-%m-%d")
                    if s.is_halted and (not s.amendment_effective_date or dt_str >= s.amendment_effective_date):
                        break
                    if curr_dt >= req_date:
                        if (dt_str, s.category) not in scheduled_set:
                            flow = ScheduledCashFlow(
                                flow_id=f"proj_{s.source_event_id}_{dt_str}",
                                date=dt_str,
                                amount=s.base_amount,
                                original_amount=s.original_amount,
                                original_currency=s.original_currency,
                                direction=s.direction,
                                category=s.category,
                                description=s.description,
                                source_event_id=s.source_event_id,
                                is_confirmed=True,
                                is_recurring=True,
                                flexibility=s.flexibility,
                                minimum_allowed_amount=s.minimum_allowed_amount,
                            )
                            projected.append(flow)
                    curr_dt += timedelta(days=s.interval_days)

        projected.sort(key=lambda x: x.date)
        return projected
