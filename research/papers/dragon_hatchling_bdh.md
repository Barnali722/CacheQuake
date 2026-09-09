# Dragon Hatchling (BDH) — The Missing Link between the Transformer and Models of the Brain

**Authors:** Adrian Kosowski, Przemysław Uznański, Jan Chorowski, Zuzanna Stamirowska, Michał Bartoszkiewicz (Pathway, Palo Alto)
**Paper:** arXiv:2509.26507 (2025) · Code: github.com/pathwaycom/bdh

## Why BDH Matters
Transformer-based models perform well but do not systematically generalize reasoning to sequences longer than what they were trained on, and their structure has no clear correspondence to how the brain reasons. BDH is a new architecture that attempts to bridge this gap — the paper frames the relationship between computing systems and the brain as a question going back to von Neumann and Turing, with generalization over time as "the main barrier for Machine Learning on the path to Universal Reasoning Models."

## Core Concept
BDH is a **scale-free, biologically-inspired network of locally-interacting neuron particles**. It reframes attention as **local graph dynamics** — edge-reweighting between neurons and synapses — showing a macro-to-micro correspondence between Transformer attention and attention mechanisms observed in the brain. Its working memory relies on **Hebbian learning** and **spiking neurons**; dynamics are governed by a local, biologically-plausible "edge-reweighting kernel" rather than by dense matrix multiplication.

## BDH vs. BDH-GPU vs. Transformer
- **BDH**: the conceptual, graph-based biological model — a distributed system of *n* locally-interacting neuron particles.
- **BDH-GPU**: a GPU-friendly, tensor-based reformulation of BDH, using a **state-space system with linear attention**. It scales primarily in a single, high neuronal dimension (*n*), uses a distinctive ReLU-lowrank feed-forward block, and produces activations that are sparse and positive by construction.
- **Transformer**: for comparison, BDH-GPU uses fewer parameter matrices than a comparable Transformer, has no fixed context-length limit (being a state-space formulation), and — unlike standard Transformer activations — produces sparse, positive activation vectors that the authors argue are more directly interpretable.

## Key Results
BDH-GPU matches GPT2-architecture Transformer performance on language and translation tasks at equal parameter counts (10M–1B), often learning faster per training token, while also showing interpretable, sparse internal states. The authors describe BDH as "a practical, performant state-of-the-art attention-based state space sequence learning architecture" that, in addition to being a graph model, "admits a GPU-friendly formulation" (Kosowski et al., 2025).

## Limitations
- Tested only up to **1B parameters** — no evidence yet at frontier-model scale.
- The brain-correspondence claims are a **theoretical/empirical hypothesis**, not a proven biological mechanism; the authors themselves note they "do not provide direct explanations for effects at shorter time scales and scheduler primitives" (Kosowski et al., 2025, §discussion of time scales).

## Diagram Plan (for our project)
- **Diagram 1** — Architecture comparison: Transformer vs. BDH-GPU vs. Brain model (attention representation, memory location, scaling dimension).
- **Diagram 2** — BDH-GPU single-layer flow: input → ReLU → Linear → Linear Attention/state update → output.
- **Diagram 3 (optional)** — Sparse activation visual: bar/heatmap showing ~5% neuron activation per token.

## Status Note
Per our project's results disclaimer: all BDH/BDH-GPU figures used in our materials are **published, not reproduced** — taken directly from Kosowski et al. (2025) rather than measured by our own pipeline, unlike the KV-cache policy benchmarks (Full Cache, Sliding Window, H2O, SnapKV, StreamingLLM), which we do simulate directly.
