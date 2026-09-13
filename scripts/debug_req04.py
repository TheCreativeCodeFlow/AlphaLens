from datetime import datetime
from alphalens.evaluation.decision_evaluator import DecisionEvaluator
from alphalens.normalization.event_normalizer import EventNormalizer
from alphalens.normalization.context_builder import ContextBuilder
from alphalens.engine.cash_flow_simulator import CashFlowSimulator
from scripts.test_experiment import ExperimentalDetector

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

ctx = builder.build_context('request_04')
det = ExperimentalDetector()
sim = CashFlowSimulator(det)
base = sim.simulate_baseline(ctx)

print("Baseline min balance:", base.minimum_projected_balance, "on", base.date_of_minimum_balance)
print("Minimum to keep:", ctx.profile.minimum_balance_to_keep)
print("Cur balance:", ctx.profile.current_available_balance)

for d, s in sorted(base.daily_timeline.items()):
    if d <= "2024-06-16":
        flows = [(f.amount, f.direction.value, f.category, f.description) for f in s.flows]
        print(f"{d} | open={s.opening_balance:10.2f} | close={s.closing_balance:10.2f} | margin={s.margin_above_minimum:10.2f} | flows={flows}")
