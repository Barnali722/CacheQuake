# CacheQuake — One-Page Concept Summary

**Project:** Interactive KV Caching Explainer · DataForge 2026 · Pathway × Rime Track
**Audience:** ML practitioners, students, and technically curious non-experts who have heard of "attention" but have not thought carefully about inference-time memory costs.

---

## The Claim

When a Transformer generates text, it avoids recomputing past attention by caching the key and value tensors for every token it has processed. This cache grows by one row per token per attention head — linearly, without bound, as long as the model keeps generating. That single fact explains why running a large language model on a long document costs far more memory than running it on a short one.

The research community has developed two broad strategies to contain this cost:

**Eviction and compression** keep only a subset of past tokens — either the most recent (Sliding Window / StreamingLLM), the most attended-to (Heavy Hitter / H2O), or a compressed approximation (KVzip). Each strategy trades exactness for a bounded budget: the cache stops growing, but the model can no longer see everything it has processed. A fact buried in an evicted token is simply gone.

**Architectural replacement** avoids the trade-off by eliminating the growing cache altogether. The BDH (Beyond Dense Hop) architecture, proposed in arXiv:2509.26507, replaces the KV cache with a fixed-size synaptic weight matrix **W**. When a new key–value pair *(k, v)* arrives, it is written into **W** by a local Hebbian update: `W ← W + k·vᵀ`. Reading is a matrix lookup: `v̂ = W·q`. The state never grows — memory is O(1) regardless of sequence length. The failure mode changes too: instead of eviction, BDH forgets via interference — new associations partially overwrite old ones.

The one-sentence claim this project teaches:

> *"A Transformer's KV cache grows linearly with every token it has ever seen because it stores an exact copy of the past; eviction and compression trade that exactness for a bounded budget, and architectures like BDH remove the growth altogether by replacing the cache with a fixed-size associative state that overwrites itself instead of appending."*

---

## What We Built

An interactive explainer running a toy decoder-only Transformer in the browser. The learner controls four cache policies — Full Cache, Sliding Window (StreamingLLM-style), Heavy Hitter (H2O-style), and BDH Recurrent — and observes three real-time readouts:

1. **Cache heatmap** — which tokens are alive in the cache, color-coded by policy; needle positions marked in red.
2. **Memory footprint chart** — live policy cache size vs. the full-cache baseline, both plotted as the sequence grows.
3. **Needle retrieval accuracy** — whether the model can still answer questions whose facts were embedded at specific positions in the sequence.

Every number on screen is labeled: live values come from a `/simulate` API call that runs a real attention forward pass. The accuracy-vs-budget sweep curve is precomputed and labeled as such. BDH paper claims are labeled "Published — not reproduced by our team."

A five-step guided walkthrough takes the learner from the linear-growth observation (Full Cache) through the two eviction strategies (Sliding Window, Heavy Hitter) to the architectural alternative (BDH), ending with a free-play Sandbox where all controls are unlocked.

---

## Learning Objectives

After completing the walkthrough, a learner should be able to:

1. Explain *why* the KV cache grows linearly (one row per token per head, never deleted in Full Cache mode).
2. Describe *what each eviction policy trades away* — early context (Sliding Window) vs. unattended tokens (Heavy Hitter) — and see it directly in the heatmap.
3. Explain *how BDH removes the growth* — fixed-size matrix, Hebbian overwrite, interference instead of eviction.
4. Predict *what happens to needle retrieval accuracy* as the budget shrinks, for each policy.

---

## Honest Scope Statement

This project covers the core BDH memory mechanism. BDH-CQ (a contrastive-query variant from the same paper) is acknowledged but not the focus — its relevance to standard KV cache replacement is limited and is stated as such in the UI. Published BDH accuracy numbers are displayed with a precomputed badge and a disclaimer that they come from a full-scale model, not our toy.

The toy simulator does not implement a full language model. It demonstrates the cache-growth and retrieval properties structurally, not at production scale. This is disclosed in the UI.

---

## Primary Sources

- Vaswani et al., "Attention Is All You Need" (2017) — arXiv:1706.03762
- Xiao et al., "Efficient Streaming Language Models with Attention Sinks" (StreamingLLM, 2023) — arXiv:2309.17453
- Zhang et al., "H2O: Heavy-Hitter Oracle" (2023) — arXiv:2306.14048
- Yıldız et al., "Beyond Dense-Hop" (BDH, 2025) — arXiv:2509.26507

*Word count: ~680 words*
