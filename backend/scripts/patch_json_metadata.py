"""Patch accuracy_vs_budget.json with v3 training metadata fields."""
import json, datetime, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
ROOT = os.path.join(os.path.dirname(__file__), "..")

path  = os.path.join(ROOT, "data", "precomputed", "accuracy_vs_budget.json")
tmeta_path = os.path.join(ROOT, "model_weights", "training_metadata.json")

with open(path) as f:
    d = json.load(f)

with open(tmeta_path) as f:
    tmeta = json.load(f)

d["LOCK_STATUS"]       = "LOCKED"
d["lock_note"]         = (
    "Final version for CacheQuake hackathon submission. "
    "Do not regenerate without flagging to team lead. "
    "Generated with v3 checkpoint (focused answer-position loss, 5000 steps)."
)
d["training_version"]  = tmeta.get("training", {}).get(
    "version", "v3 (focused answer-position loss)")
d["model_checkpoint"]  = tmeta.get("checkpoint", "toy_transformer.pt")
d["generated_at"]      = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

with open(path, "w") as f:
    json.dump(d, f, indent=2)

with open(path) as f:
    d2 = json.load(f)

print("LOCK_STATUS:      ", d2["LOCK_STATUS"])
print("training_version: ", d2["training_version"])
print("model_checkpoint: ", d2["model_checkpoint"])
print("generated_at:     ", d2["generated_at"])
print()

fc = d2["policies"]["full_cache"]["data"][0]["accuracy"]
print(f"full_cache accuracy: {fc}")
for policy in ["sliding_window", "heavy_hitter", "bdh_inspired_state"]:
    entries = d2["policies"][policy]["data"]
    print(f"{policy}: {[(e['budget'], e['accuracy']) for e in entries]}")
