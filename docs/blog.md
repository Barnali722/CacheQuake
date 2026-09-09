# Why Your Chatbot Forgets: Building CacheQuake

*Team Game of Codes — DataForge 2026, Pathway × Rime track*

## The bug that isn't a bug

Every time a large language model generates the next word of a long conversation, it has to look back at everything it has already produced. Recomputing that lookup from scratch at every step would make long conversations unusably slow — so instead, models cache the Key and Value projections from every past token, and reuse them. This is the **KV cache**, and it's one of the quiet, load-bearing mechanisms behind every chatbot you've used.

The catch: that cache doesn't shrink. It grows by one entry per token, per layer, per attention head, for as long as the model keeps generating. Ask it to hold a whole codebase or a long document in context, and the memory bill scales linearly with how much you've asked it to remember. This isn't a bug to be patched — it's a direct, structural consequence of how attention caching works. The only real options are: pay the growing cost, decide what to throw away, or change the architecture so there's nothing to throw away in the first place.

We built **CacheQuake** to make that trade-off something you can *see*, not just read about.

## What we built

CacheQuake runs a small, real, from-scratch decoder-only Transformer — four layers, 64-dimensional, character-level vocabulary — behind a FastAPI backend. You feed it a synthetic "haystack" sequence with a few hidden facts buried inside, pick one of four cache strategies, and watch what happens:

- **Full Cache** — keep everything. The baseline. Memory grows in a straight line.
- **Sliding Window** — keep only a recent window, plus a handful of "sink" tokens at the very start (an approach inspired by StreamingLLM). Memory is bounded, but old context is gone.
- **Heavy Hitter** — keep only the tokens that have accumulated the most attention "weight" over time (inspired by H2O). Memory is bounded differently — by importance rather than recency.
- **BDH-Inspired State** — instead of keeping *any* individual tokens, maintain a small, fixed-size memory matrix that gets overwritten, not appended to, on every step. Memory never grows at all, no matter how long the sequence gets.

That fourth policy is inspired by a real, recent architecture — **BDH ("Dragon Hatchling")**, from a September 2025 paper by researchers at Pathway (arXiv:2509.26507) — which proposes replacing the KV cache entirely with a synaptic, Hebbian-updating memory state. We want to be very clear about scope here: our `bdh_inspired_state.py` policy borrows BDH's *conceptual idea* — a fixed-size state that overwrites instead of appends — using a hand-designed update rule we wrote ourselves. It is not a reproduction of BDH's actual scale-free neuron-particle graph, its spiking dynamics, or its learned synaptic weights. We say this in the code, in our docs, and we're saying it here again on purpose, because the difference between "inspired by" and "reproducing" a paper's architecture matters, and it's easy to blur under hackathon time pressure.

## What we found (with appropriate caveats)

We precomputed one accuracy-vs-memory-budget sweep across all four policies, using our own lightly-trained toy model — 80 episodes per policy, per budget, all clearly labeled as "our precomputed result," never mixed in with the BDH paper's published claims. Some of what showed up:

- At small budgets, every eviction policy struggles — there just isn't room to keep the fact that matters.
- At mid-range budgets, our **Heavy Hitter** policy actually **beat** the unbounded Full Cache baseline. Selectively discarding irrelevant filler tokens seems to help this tiny model focus, even though it has strictly less information available.
- Our BDH-inspired policy's accuracy stayed roughly flat regardless of state size — consistent with the idea that "bigger fixed state" doesn't behave like "bigger token budget." It forgets by interference, not by eviction, and that's a genuinely different failure mode.

We want to underline: this is a 4-layer toy model on a synthetic task, evaluated once, at one configuration. It is not a benchmark claim about any real cache policy at production scale, and we don't present it as one anywhere in the project.

## What we were careful about

The rubric for this track cares a lot about not blurring "the concept truly behaves live" with "here's a number we made up or found in a table." So we drew a hard structural line: anything computed live during your interaction comes straight from a running attention forward pass. Anything precomputed lives in a separate `data/precomputed/` folder, physically apart from the live code, and is labeled everywhere it shows up in the UI. Anything from the BDH paper itself is labeled as a **published claim, not reproduced by us** — and where we didn't have verified access to the paper's exact benchmark numbers, we left that field empty rather than guess. An empty field with an honest explanation felt more defensible to us than a plausible-looking number we couldn't stand behind.

## What's still missing

We're not going to pretend this is finished. `POST /step`, a planned real-time single-token streaming endpoint, still returns "not implemented." Our comprehension-check questions are placeholder text — we ran out of time to write real ones before submission. And one of our own planning documents originally misnamed the BDH paper (an old working title, wrong author list) — a mistake we caught and corrected while writing this documentation, and a good reminder that "we cited a paper" and "we double-checked the citation" are not the same step.

## Why this topic, and why now

Every KV-cache strategy we simulated, and the architectural alternative we simulated a shadow of, are all things researchers are actively arguing about *right now* — StreamingLLM, H2O, SnapKV, Quest, and KVzip all appeared within the last three years, and BDH is a matter of months old at the time we built this. That's the frontier this project tries to explain: not a settled textbook fact, but a live design space, made concrete enough to poke at with your own hands.
