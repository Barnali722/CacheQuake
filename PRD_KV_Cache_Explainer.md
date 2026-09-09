# PRD — "Why Your Chatbot Forgets: KV Caching, Its Limits, and the Alternatives"
**DataForge 2026 · Pathway x Rime Track**
**Team size:** 4 · **Timeline:** 5 days

---

## 1. Topic & Framing

**Approved topic:** Key–Value Caching, Limitations, and Alternate Approaches

**Why this topic:** every LLM chat product a judge or learner has used is bottlenecked by this exact mechanism. It's the cleanest bridge from "something I already use" to "a frontier architectural debate" (BDH included), and it decomposes naturally into a simulate-able toy system — which is what the rubric rewards most (Interactive substrate = 15 pts, Learning effectiveness = 15 pts).

**One-sentence falsifiable claim (the whole artifact teaches this one sentence):**
> "A Transformer's KV cache grows linearly with every token it has ever seen because it stores an exact copy of the past; eviction and compression trade that exactness for a bounded budget, and architectures like BDH remove the growth altogether by replacing the cache with a fixed-size associative state that overwrites itself instead of appending."

A learner should be able to test this directly: crank up sequence length, watch cache size explode; cap the budget, watch quality degrade in a specific, visible way; swap in the fixed-size recurrent variant, watch memory flatten while a different failure mode (interference) appears instead.

---

## 2. Target Audience & Prerequisites

- **Audience:** an "average data scientist" (per the judging rubric) — knows what attention and a Transformer forward pass are, has never derived why KV caching exists or looked at an eviction policy.
- **Prerequisites stated up front in the artifact:** attention mechanism basics, what "autoregressive generation" means. Nothing about BDH, state-space models, or eviction heuristics is assumed.

## 3. Learning Objectives

By the end, a learner should be able to:
1. Explain why decoding needs a KV cache at all (why can't you just recompute attention every step).
2. State why cache size scales with `sequence_length × layers × heads × head_dim`, not with model size.
3. Predict what eviction/compression trade away, and in what situations that trade-off breaks (e.g. instruction leakage, "lost in the middle").
4. Explain how BDH's fixed-shape recurrent synaptic state sidesteps the growth problem, and what it gives up in return.
5. State one real limitation or misconception (e.g. "compression is free" — it isn't; "recurrent state = infinite context" — it isn't, it forgets via interference).

---

## 4. What We're Building

### 4.1 The interactive substrate (must be real, not scripted)
A small **from-scratch toy decoder-only Transformer** (2–4 layers, tiny vocab, e.g. character-level or a small synthetic "needle" vocabulary) run **live in-browser or via a lightweight backend**, instrumented so every generation step exposes its actual KV cache. This is the "substrate" the rubric requires — the concept must visibly behave before the learner touches anything.

**Core interactive view — "CacheQuake":**
- Feed the toy model a long synthetic sequence containing a few "needle" facts (a classic needle-in-haystack setup, small enough to be real-time).
- Learner controls (few, each mapped to one real variable, per the design standards):
  - **Cache policy**: Full cache / Sliding-window eviction (StreamingLLM-style) / Heavy-hitter eviction (H2O-style) / Fixed-size recurrent state (linear-attention/BDH-style toy layer).
  - **Budget size** (for eviction/compression policies).
  - **Sequence length / number of needles.**
- Live readouts, side by side ("truth beside estimate"): actual memory footprint (tokens × KV bytes) vs. a ground-truth flat baseline; retrieval accuracy on the needle question vs. the correct answer; a visual heat-map of which past tokens are still "alive" in the cache at each policy.
- Fast feedback: all four policies precompute-able at small scale so interaction stays sub-second; label anything precomputed clearly per the "no hidden limits" rule.

### 4.2 The BDH module (must-have, woven in — not bolted on)
Positioned as the fourth "cache policy" option above, with its own dedicated explainer step:
- Diagram (from the BDH paper, arXiv:2509.26507) of how attention is reformulated as a **synaptic, Hebbian-updating edge-reweighting kernel** over a scale-free neuron graph, instead of an appended KV list.
- Explicit statement of what's changing: not a growing list of past keys/values, but a **fixed-size, sparse, non-negative activation state that is overwritten via local update rules as new tokens arrive** — i.e., the same "memory vs. compute" trade-off as eviction, but architected in from the start rather than patched on afterward.
- One clearly-labeled **precomputed** comparison panel: our toy simulator's own eviction/compression accuracy-vs-budget curve, placed next to BDH's *published* claims (e.g. reported long-context/generalization-over-time behavior from the paper), explicitly marked "published result, not reproduced by us" — honoring the "toy model ≠ official BDH" rule.
- One paragraph distinguishing BDH from BDH-CQ for this topic: BDH-CQ's relevance here is secondary (its main contribution is test-time skill acquisition without weight updates, not KV-cache reduction per se) — the README will say this plainly rather than inventing a forced connection, as instructed.

### 4.3 Guided path, then sandbox
1. **Hook (10s):** open with a preset already running — full cache blowing past a memory budget on a long sequence.
2. **Guided walkthrough (3–5 steps):** the one-sentence claim → try eviction → try compression → try the BDH-style fixed state → see the trade-off table.
3. **Sandbox:** all controls unlocked, learner free-plays.
4. **Checkpoint:** a 2-question inline check ("what would happen if you evicted the needle token?") before unlocking the "explain it back" free-text box.

### 4.4 Explicit non-goals
- Not reproducing or fine-tuning an actual BDH checkpoint (explicitly not required by the brief).
- Not covering every eviction paper — three representative families only (sliding window, heavy-hitter, quantization mentioned but not simulated).
- Not a general "how Transformers work" tutorial — attention basics are assumed, not taught.

---

## 5. Deliverables Checklist (mapped to submission requirements)

| Deliverable | Owner (see §7) |
|---|---|
| Public artifact URL, no sign-in | Frontend/Interaction lead |
| Public source code repo | Simulation/Backend lead |
| Blog as PDF | Research/Content lead |
| One-page concept summary PDF (500–950 words) | Research/Content lead |
| Complete README (claim, audience, objectives, architecture, live/precomputed/animated breakdown, repro steps, credits/licenses) | Docs/Design/Ops lead (compiled from all four) |
| ≥3 recent primary papers (2022–2026), cited beside claims | Research/Content lead |
| Source & license record (code, data, fonts, graphics) | Docs/Design/Ops lead |
| AI-assistance disclosure | All (logged daily), compiled by Docs/Design/Ops lead |

**Primary sources locked in (verify + expand during Day 1 research):**
- Zhang et al., *H2O: Heavy-Hitter Oracle for Efficient Generative Inference of LLMs*, arXiv:2306.14048 (NeurIPS 2023) — eviction by cumulative attention score.
- Xiao et al., *Efficient Streaming Language Models with Attention Sinks (StreamingLLM)*, arXiv:2309.17453 (ICLR 2024) — sliding window + sink tokens.
- Li et al., *SnapKV*, 2024 — prefill-stage compression via an observation window.
- Tang et al., *Quest: Query-Aware Sparsity for Efficient Long-Context LLM Inference*, arXiv:2406.10774 (2024).
- Kim et al., *KVzip: Query-Agnostic KV Cache Compression with Context Reconstruction*, NeurIPS 2025 — recent (2025) query-agnostic angle, good for "why this is still moving right now."
- Kosowski, Uznański, Chorowski, Stamirowska, Bartoszkiewicz, *The Dragon Hatchling: The Missing Link Between the Transformer and Models of the Brain*, arXiv:2509.26507 — primary BDH source; note Adrian Kosowski's own comment thread on the Hugging Face paper page as a secondary framing source per the brief.

---

## 6. Success Metrics (mapped to the 100-point rubric)

| Criterion | Pts | What "done" looks like for us |
|---|---|---|
| Technical correctness & depth | 25 | Every eviction/compression claim traced to its primary paper; BDH mechanism description checked against arXiv:2509.26507 directly, not a secondary summary |
| Technical ownership & live defense | 15 | Every team member can trace the toy simulator's forward pass and predict what a budget change does, live, unaided |
| Learning effectiveness | 15 | ≥3 outside testers (non-teammates) can restate the one-sentence claim correctly after a 60-second run |
| Interactive substrate & honesty | 15 | Toy model genuinely computes attention/cache live; every precomputed or illustrative element is labeled as such |
| BDH/BDH-CQ integration | 10 | BDH module has its own learning objective and diagram; BDH-CQ's limited relevance to this topic is stated honestly, not forced |
| Craft, robustness, accessibility, provenance | 10 | Works on mobile, loads with a running preset, full license/credit table in README |
| One-page concept summary | 10 | Passes the "hand it to someone cold" test — reviewed by a non-team member before submission |

---

## 7. Team & Roles (4 people)

1. **Research & Content Lead** — owns the one-sentence claim, the ≥3 primary papers and citation placement, the one-page concept summary, first draft of the BDH module text, accuracy pass on every technical claim in the README/blog.
2. **Simulation/Backend Engineer** — owns the toy Transformer, the KV-cache instrumentation, and the four cache-policy implementations (full / sliding-window / heavy-hitter / fixed-size recurrent), plus any precomputed result generation.
3. **Frontend/Interaction Engineer** — owns the interactive UI, the controls-to-variables mapping, the truth-vs-estimate readouts, the guided-then-sandbox flow, mobile responsiveness.
4. **Docs, Design & Ops Lead** — owns README structure, blog PDF assembly, source/license tracking, AI-assistance disclosure log, deployment (public URL + repo hygiene), and coordinates the live-defense rehearsal and outside-tester feedback loop.

Roles are primary ownership, not silos — expect cross-over, especially Days 3–5.

---

## 8. 5-Day Timeline

### Day 1 — Scope, claim, architecture
- **All:** Read primary sources together (BDH paper §attention-as-synapse; H2O; StreamingLLM). Lock the one-sentence claim and audience/prerequisites.
- **Research lead:** Draft claim + learning objectives; start the ≥3-paper source list with exact citation placement plan.
- **Simulation engineer:** Decide toy model size/vocab/task (needle-in-haystack synthetic data); scaffold repo, pick stack (e.g. Python/NumPy or PyTorch backend + a thin API, or a fully client-side JS simulator if feasible for speed).
- **Frontend engineer:** Wireframe the "CacheQuake" view; define the control set and readouts; set up project skeleton.
- **Docs/Design lead:** Set up repo structure, README skeleton, license/AI-disclosure tracker, deployment target.
- **End of day:** written one-sentence claim + wireframe + architecture doc agreed by all four.

### Day 2 — Build the substrate
- **Simulation engineer:** Implement toy Transformer forward pass with live KV cache; implement full-cache and sliding-window eviction policies; expose per-step cache state via API/data structure.
- **Frontend engineer:** Build core visualization shell (cache heat-map, memory readout) against mocked data; start control wiring.
- **Research lead:** Deepen paper notes for H2O/heavy-hitter and SnapKV/compression; draft BDH module content outline with diagram plan.
- **Docs/Design lead:** Draft README architecture section in parallel with real build decisions; begin source/license log.
- **End of day:** sliding-window policy demonstrably running end-to-end (even if UI is rough).

### Day 3 — Complete policies + BDH module + real UI wiring
- **Simulation engineer:** Implement heavy-hitter eviction and the fixed-size recurrent ("BDH-style") toy layer; generate/label any precomputed comparison data.
- **Frontend engineer:** Wire all four policies into the live UI; implement truth-vs-estimate display and guided walkthrough steps 1–3.
- **Research lead:** Finalize BDH module text and diagram; draft the precomputed-BDH-comparison panel copy with explicit "published, not reproduced" labeling; start one-page concept summary draft.
- **Docs/Design lead:** Draft blog PDF outline; continue AI-assistance disclosure log; check accessibility basics (contrast, mobile breakpoints) on the in-progress UI.
- **End of day:** all four cache policies interactive end-to-end; BDH module content ready for integration.

### Day 4 — Integrate, polish, write
- **All:** Integrate BDH module into the guided flow; run the full walkthrough as if a first-time learner and fix friction points.
- **Frontend engineer:** Sandbox mode, mobile polish, response-time tuning (precompute anything slow).
- **Simulation engineer:** Lock and label all precomputed results; write reproduction instructions (setup steps for the repo).
- **Research lead:** Finalize one-page concept summary; finalize ≥3-paper citations placed beside specific claims in README/blog; internal fact-check pass against primary sources.
- **Docs/Design lead:** Assemble blog PDF; complete README (claim, audience, objectives, architecture, live/precomputed/animated breakdown, credits/licenses); compile AI-assistance disclosure.
- **End of day:** feature-complete build + drafts of all written deliverables.

### Day 5 — Test, defend, submit
- **All:** Run the "60-second test" with ≥3 outside testers each; fix the top comprehension blockers found.
- **All:** Rehearse live defense — each member must be able to trace any component and predict the effect of a change, unaided (per the "Technical ownership" rubric item).
- **Frontend/Simulation:** Final performance pass, deploy to public URL, verify it opens without sign-in on a clean device/network.
- **Docs/Design lead:** Final README/license/citation check; give the one-page summary a cold read by a non-team member; package the submission (artifact URL, repo, blog PDF, one-page summary PDF, README).
- **Research lead:** Final accuracy sweep — no overclaiming, every BDH/BDH-CQ statement checked against primary sources one more time.
- **End of day:** submitted.

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Toy model too slow for "sub-second" interaction | Precompute the expensive sweeps (accuracy vs. budget curves) as data; keep only the single live generation step interactive |
| BDH module reads as "bolted on" | Give it its own guided-walkthrough step and its own learning objective from Day 1, not appended after eviction/compression |
| Overclaiming BDH's KV-cache relevance | State explicitly in README/summary that BDH's fixed-size state is a *design alternative* to KV caching, not a claimed drop-in replacement validated at production scale — cite the paper's actual claims only |
| Team can't defend a component live | Day 5 rehearsal is mandatory for all four, not just the person who built it |
| Scope creep (trying to cover too many eviction papers) | Hard cap at 3 simulated policies + BDH; anything else is "further reading" links only |

---

*Prepared for the DataForge 2026 Pathway Track. Topic: Key–Value Caching, Limitations, and Alternate Approaches.*
