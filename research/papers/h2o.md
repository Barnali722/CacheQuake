# H2O — Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models

**Authors:** Zhang, Sheng, Zhou, Chen, Zheng, Cai, Song, Tian, Ré, Barrett, et al.
**Paper:** arXiv:2306.14048 (NeurIPS 2023)

## Core Idea
Attention matrices in pretrained LLMs are over 95% sparse. A small set of tokens — "Heavy Hitters" (H2) — account for most of the attention score at any given step.

## Problem
KV cache size grows linearly with sequence length and batch size, creating a major memory bottleneck during long-context generation.

## Observation
Heavy-Hitter tokens follow a power-law distribution and strongly correlate with frequent token co-occurrence in the text. Because they keep receiving high attention across steps, they can be identified and protected cheaply.

## Method
H2O formulates KV cache eviction as a **dynamic submodular optimization** problem. At every decoding step, it runs a greedy algorithm that retains a balance of:
- **Heavy-Hitter tokens** (highest cumulative attention scores so far), and
- **Recent tokens** (local window),
evicting the rest of the cache.

The authors prove a theoretical guarantee for the eviction policy under mild assumptions, and validate it empirically on OPT, LLaMA, and GPT-NeoX.

## Key Result
- Matches full-cache accuracy with only ~20% of the KV cache budget.
- Improves throughput by up to **29×** over DeepSpeed Zero-Inference and Hugging Face Accelerate, and up to 3× over FlexGen.
- Reduces latency by up to **1.9×** at the same batch size.

## Limitation
- Has a **recency/accumulation bias**: because importance is scored cumulatively, older tokens can keep accruing high scores even if they're no longer relevant, so the eviction policy can be slow to "forget."
- The method targets the KV cache only; MLP-block parameters are not optimized, so overall memory savings are bounded by attention-cache size alone.
- Being a greedy, per-step heuristic, it offers no hard guarantee against evicting a token that becomes critical much later (no re-admission mechanism).

## Relation to Other Methods
- **StreamingLLM** simplifies the same "keep a few important + recent tokens" intuition, but fixes the important set to the first few "attention sink" tokens instead of learning it dynamically.
- **SnapKV** replaces H2O's online, per-step cumulative scoring with a one-time, prompt-side "observation window" vote — trading H2O's adaptivity during generation for a much cheaper prefill-time decision.
