# backend/scripts/train_toy.py
"""
Short training run for the CacheQuake toy Transformer.

HONESTY LABEL — read before using the output weights
-----------------------------------------------------
This is a MINIMAL TRAINING RUN on our own synthetic needle-haystack task.
It is NOT:
  - A pretrained language model
  - A benchmark-evaluated model
  - A serious pretraining run

It IS:
  - Enough training that the model learns to attend to the "vault code" pattern
    in short synthetic sequences, making the accuracy-vs-budget curves
    pedagogically meaningful for the demo.
  - Fully reproducible: running this script again with the same seed produces
    the same weights.

Training details (written into model_weights/training_metadata.json at end):
  - Task:       NeedleHaystackTask synthetic episodes (same task used in demo)
  - Steps:      3,000
  - Batch size: 8 episodes per step
  - Optimizer:  AdamW, lr=3e-3, weight_decay=1e-2
  - Loss:       Cross-entropy over all non-padding positions
  - Seq len:    120 tokens
  - n_facts:    random in {1, 2, 3} per episode
  - Duration:   measured and stored in metadata

Run from backend/:
    python scripts/train_toy.py
"""

import sys, os, time, json, random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import torch
import torch.nn.functional as F

from app.model.toy_transformer import ToyTransformer
from app.model.vocab import PAD_ID, VOCAB_SIZE
from app.tasks.needle_haystack import NeedleHaystackTask

# ── Reproducibility ────────────────────────────────────────────────────────
SEED = 42
torch.manual_seed(SEED)
random.seed(SEED)

# ── Hyperparameters ────────────────────────────────────────────────────────
STEPS      = 5_000   # 3k steps with full-sequence loss collapsed to '2' always;
                     # focused answer-position loss needs ~5k to converge reliably
BATCH_SIZE = 8
LR         = 3e-3
WD         = 1e-2
SEQ_LEN    = 120
LOG_EVERY  = 500    # print loss every N steps

# ── Paths ──────────────────────────────────────────────────────────────────
OUT_DIR      = os.path.join(os.path.dirname(__file__), "..", "model_weights")
CKPT_PATH    = os.path.join(OUT_DIR, "toy_transformer.pt")
META_PATH    = os.path.join(OUT_DIR, "training_metadata.json")
OUT_DIR      = os.path.normpath(OUT_DIR)
CKPT_PATH    = os.path.normpath(CKPT_PATH)
META_PATH    = os.path.normpath(META_PATH)

# ── Model ──────────────────────────────────────────────────────────────────
model = ToyTransformer(
    vocab_size  = VOCAB_SIZE,   # 44
    d_model     = 64,
    n_heads     = 4,
    n_layers    = 4,
    max_seq_len = 512,
)
model.train()

optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WD)


def make_batch(base_seed: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Generate a batch of (input_ids, target_ids) from synthetic episodes.

    Critical design note
    --------------------
    episode.token_ids ends at the '?' of the question; the answer digits are
    stored in episode.answer but NOT appended to token_ids.

    v2 fix: append answer[0] so the model sees '?' -> digit in the sequence.
    v3 fix (this version): focus the loss ONLY on the '?' -> answer position.
        v2 still had ~118 non-retrieval positions diluting the gradient, causing
        the model to collapse to always predicting the most-common digit ('2').
        Here we set all targets to PAD_ID (ignored by cross-entropy) except the
        position of '?' which must predict the answer digit.  This gives the
        model a clean, undiluted retrieval gradient at every step.

    input_ids  : int[BATCH_SIZE, SEQ_LEN]  — token ids (padded)
    target_ids : int[BATCH_SIZE, SEQ_LEN]  — ALL PAD except '?' position
    """
    from app.model.vocab import encode as vocab_encode
    all_inputs, all_targets = [], []
    for i in range(BATCH_SIZE):
        n_facts = random.randint(1, 3)
        qt      = random.randint(0, n_facts - 1)
        task    = NeedleHaystackTask(seed=base_seed * BATCH_SIZE + i)
        episode = task.generate(
            n_facts         = n_facts,
            seq_len         = SEQ_LEN,
            question_target = qt,
        )

        # ids_base ends with '?'; answer_tok is the first digit of the answer
        ids_base   = episode.token_ids[:SEQ_LEN - 1]   # ends with '?'
        answer_tok = vocab_encode(episode.answer[0])[0]
        q_pos      = len(ids_base) - 1                 # index of '?' in ids_base

        # Full input: [haystack + question? + answer_digit + PAD...]
        ids     = ids_base + [answer_tok]
        pad_len = SEQ_LEN - len(ids)
        ids_padded = ids + [PAD_ID] * pad_len           # length == SEQ_LEN

        # Focused targets: PAD everywhere EXCEPT '?' position -> answer_tok
        targets = [PAD_ID] * SEQ_LEN
        targets[q_pos] = answer_tok   # only this position contributes to loss

        all_inputs.append(ids_padded)
        all_targets.append(targets)

    inp = torch.tensor(all_inputs,  dtype=torch.long)
    tgt = torch.tensor(all_targets, dtype=torch.long)
    return inp, tgt




print(f"Training ToyTransformer for {STEPS} steps × batch {BATCH_SIZE} …")
print(f"Checkpoint will be saved to: {CKPT_PATH}\n")

t0          = time.time()
running_loss = 0.0

for step in range(1, STEPS + 1):
    inp, tgt = make_batch(base_seed=step)

    # Forward — no past cache during training (full teacher-forcing)
    logits, _ = model(inp)    # [B, T, vocab_size]

    # Flatten for cross-entropy; ignore PAD positions in target
    B, T, V = logits.shape
    logits_flat = logits.reshape(B * T, V)   # [B*T, V]
    tgt_flat    = tgt.reshape(B * T)         # [B*T]

    loss = F.cross_entropy(logits_flat, tgt_flat, ignore_index=PAD_ID)

    optimizer.zero_grad()
    loss.backward()
    # Gradient clip — prevents early blow-up with lr=3e-3
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()

    running_loss += loss.item()
    if step % LOG_EVERY == 0:
        avg = running_loss / LOG_EVERY
        elapsed = time.time() - t0
        print(f"  step {step:4d}/{STEPS}  loss={avg:.4f}  elapsed={elapsed:.1f}s")
        running_loss = 0.0

duration_s = round(time.time() - t0, 1)
print(f"\nTraining complete in {duration_s}s")

# ── Save checkpoint ────────────────────────────────────────────────────────
model.eval()
torch.save(model.state_dict(), CKPT_PATH)
print(f"Saved weights -> {CKPT_PATH}")

# ── Save metadata (loaded by main.py and embedded in accuracy JSON) ────────
metadata = {
    "HONESTY_LABEL": (
        "Lightly trained on synthetic needle-haystack episodes generated by "
        "CacheQuake's own NeedleHaystackTask. This is NOT a pretrained language "
        "model, NOT a benchmark-evaluated model, and NOT a serious pretraining run. "
        "It is the minimum training needed for the accuracy-vs-budget curves to "
        "be pedagogically meaningful in the demo."
    ),
    "training_fix_note": (
        "v1 training had a bug: episode.token_ids ends at '?' and the answer "
        "digits were truncated off, so the model never saw the '?' -> digit "
        "transition. v2 reserves 1 slot and appends episode.answer[0] to each "
        "training sequence so the model learns the correct prediction target."
    ),
    "model": {
        "vocab_size":   VOCAB_SIZE,
        "d_model":      64,
        "n_heads":      4,
        "n_layers":     4,
        "max_seq_len":  512,
    },
    "training": {
        "version":           "v3 (focused answer-position loss)",
        "steps":             STEPS,
        "batch_size":        BATCH_SIZE,
        "optimizer":         "AdamW",
        "lr":                LR,
        "weight_decay":      WD,
        "grad_clip":         1.0,
        "task":              "NeedleHaystackTask synthetic episodes",
        "seq_len":           SEQ_LEN,
        "n_facts_range":     "1-3 (random per episode)",
        "question_target":   "random per episode",
        "answer_in_seq":     True,
        "loss_masking":      "only '?' -> answer_digit position; all other positions PAD",
        "seed":              SEED,
        "duration_seconds":  duration_s,
        "final_loss":        round(running_loss / LOG_EVERY if running_loss > 0 else 0, 4),
    },
    "checkpoint": os.path.basename(CKPT_PATH),
}

with open(META_PATH, "w") as f:
    json.dump(metadata, f, indent=2)
print(f"Saved metadata  -> {META_PATH}")
