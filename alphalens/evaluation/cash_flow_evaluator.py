from typing import Dict, Any, List
from ..ingestion.loaders import DatasetLoader
from ..ingestion.currency import CurrencyNormalizer
from ..extraction.image_extractor import ImageEvidenceExtractor
from ..extraction.message_parser import MessageParser
from ..normalization.event_normalizer import EventNormalizer
from ..normalization.context_builder import ContextBuilder
from ..engine.state_reconstructor import StateReconstructor
from ..engine.recurrence_detector import RecurrenceDetector
from ..engine.cash_flow_simulator import CashFlowSimulator


class CashFlowEvaluator:
    """
    Evaluates the Phase 2 Financial State Reconstruction & 90-Day Cash Flow Engine.
    Executes baseline forecasts across all 275 requests and produces sample-level diagnostics.
    """

    def __init__(self, dataset_dir: str = "dataset"):
        self.dataset_dir = dataset_dir
        self.loader = DatasetLoader(dataset_dir)
        self.currency_normalizer = CurrencyNormalizer(f"{dataset_dir}/exchange_rates.csv")
        self.image_extractor = ImageEvidenceExtractor(f"{dataset_dir}/media/images")
        self.message_parser = MessageParser()

    def evaluate(self) -> Dict[str, Any]:
        # 1. Ingestion and hydration
        profiles = self.loader.load_profiles()
        eval_requests = self.loader.load_requests("requests.csv")
        sample_requests, sample_ground_truth = self.loader.load_sample_requests()
        all_requests = {**eval_requests, **sample_requests}
        events = self.loader.load_events()
        options = self.loader.load_payment_options()
        images_raw = self.loader.load_images_raw()
        messages_raw = self.loader.load_messages_raw()

        # 2. Normalization
        event_normalizer = EventNormalizer(self.currency_normalizer, self.image_extractor)
        norm_events, image_evidences = event_normalizer.normalize_events(events, profiles, images_raw)

        message_facts = [self.message_parser.parse_message(m) for m in messages_raw]

        builder = ContextBuilder(
            profiles=profiles,
            requests=all_requests,
            events=norm_events,
            payment_options=options,
            message_facts=message_facts,
            image_evidences=image_evidences,
            currency_normalizer=self.currency_normalizer,
        )

        detector = RecurrenceDetector()
        simulator = CashFlowSimulator(detector)
        reconstructor = StateReconstructor(detector, simulator)

        total_requests = len(all_requests)
        baseline_forecasts_generated = 0
        forecast_failures = 0
        baseline_violations_detected = 0
        total_recurring_series_detected = 0
        total_projected_flows = 0
        total_confirmed_income_flows = 0
        total_pending_income_excluded = 0
        message_amendments_applied = 0
        image_events_incorporated = len(image_evidences)
        foreign_conversions_performed = sum(1 for e in norm_events.values() if e.conversion_rate and e.conversion_rate != 1.0)
        invariant_violations = 0

        sample_diagnostics: List[Dict[str, Any]] = []

        for req_id, req in all_requests.items():
            try:
                ctx = builder.build_context(req_id)
                state = reconstructor.reconstruct_state(ctx)

                if state.baseline_forecast is not None:
                    baseline_forecasts_generated += 1
                    total_projected_flows += len(state.recurring_expenses) + len(state.recurring_income)
                    total_confirmed_income_flows += len(state.confirmed_income)
                    total_pending_income_excluded += len(state.pending_income)

                    if not state.is_base_plan_safe():
                        baseline_violations_detected += 1

                    # Verify invariant: opening balance of day d+1 equals closing balance of day d
                    timeline_dates = sorted(state.baseline_forecast.daily_timeline.keys())
                    for i in range(len(timeline_dates) - 1):
                        d1 = timeline_dates[i]
                        d2 = timeline_dates[i + 1]
                        if round(state.baseline_forecast.daily_timeline[d1].closing_balance, 2) != round(
                            state.baseline_forecast.daily_timeline[d2].opening_balance, 2
                        ):
                            invariant_violations += 1

                    # If this is a sample request, record diagnostic metrics
                    if req_id in sample_requests:
                        diag = {
                            "request_id": req_id,
                            "user_id": req.user_id,
                            "currency": state.home_currency,
                            "current_balance": state.current_cash_balance,
                            "protected_minimum": state.protected_minimum,
                            "baseline_minimum_balance": state.minimum_projected_balance(),
                            "baseline_minimum_date": state.date_of_minimum_balance(),
                            "future_confirmed_income": round(
                                state.total_confirmed_income(req.request_date, "2030-01-01"), 2
                            ),
                            "future_required_expenses": round(
                                state.total_required_expenses(req.request_date, "2030-01-01"), 2
                            ),
                            "future_flexible_expenses": round(
                                state.total_flexible_expenses(req.request_date, "2030-01-01"), 2
                            ),
                            "potential_minimum_balance": state.minimum_projected_balance(),
                            "violations": state.minimum_balance_violations(),
                        }
                        sample_diagnostics.append(diag)

            except Exception as ex:
                forecast_failures += 1

        return {
            "requests_simulated": total_requests,
            "baseline_forecasts_generated": baseline_forecasts_generated,
            "forecast_failures": forecast_failures,
            "baseline_violations_detected": baseline_violations_detected,
            "total_projected_flows": total_projected_flows,
            "total_confirmed_income_flows": total_confirmed_income_flows,
            "total_pending_income_excluded": total_pending_income_excluded,
            "image_events_incorporated": image_events_incorporated,
            "foreign_conversions_performed": foreign_conversions_performed,
            "invariant_violations": invariant_violations,
            "sample_diagnostics": sample_diagnostics,
            "status": "PASS" if (forecast_failures == 0 and invariant_violations == 0) else "FAIL",
        }
