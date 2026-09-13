from datetime import datetime
from alphalens.evaluation.decision_evaluator import DecisionEvaluator
from alphalens.normalization.event_normalizer import EventNormalizer
from alphalens.normalization.context_builder import ContextBuilder
from alphalens.engine.cash_flow_simulator import CashFlowSimulator
from scripts.test_experiment import ExperimentalDetector, FastAffordabilityEngine

ev = DecisionEvaluator()
profiles = ev.loader.load_profiles()
sample_requests, ground_truth = ev.loader.load_sample_requests()
events = ev.loader.load_events()
options = ev.loader.load_payment_options()
images_raw = ev.loader.load_images_raw()
messages_raw = ev.loader.load_messages_raw()

en = EventNormalizer(ev.currency_normalizer, ev.image_extractor)
ne, ie = en.normalize_events(events, profiles, images_raw)
mf = [ev.message_parser.parse_message(m) for m in messages_raw]
builder = ContextBuilder(profiles, sample_requests, ne, options, mf, ie, ev.currency_normalizer)

det = ExperimentalDetector()
sim = CashFlowSimulator(det)
eng = FastAffordabilityEngine(sim)

for rid in ['request_05', 'request_10', 'request_14', 'request_15', 'request_20', 'request_24', 'request_25']:
    ctx = builder.build_context(rid)
    pred = eng.evaluate_request(ctx)
    gt = ground_truth[rid]
    print(f"{rid} -> pred safe: {pred['amount_safe_to_pay']} | gt safe: {gt['amount_safe_to_pay']}")
