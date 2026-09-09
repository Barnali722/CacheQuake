# SnapKV — LLM Knows What You Are Looking for Before Generation

**Authors:** Li, Huang, et al.
**Paper:** arXiv:2404.14469

## Core Idea
Each attention head consistently focuses on the same specific prompt features throughout generation — i.e., the pattern of "what matters" is largely set by the prompt itself and stays stable once generation begins.

## Problem
KV cache growth with increasing input length creates memory and time-efficiency challenges for long-context LLMs (same underlying bottleneck as H2O, approached from the prefill side instead of the decode side).

## Observation
The attention pattern that will matter during generation can be captured from an **"observation window"** at the end of the prompt, before generation even starts — so the important KV positions can be selected once, up front, rather than tracked online at every decode step.

## Method
- **Fine-tuning-free.**
- Uses a **voting mechanism** that aggregates attention weights from the observation window (the last portion of the prompt) across heads.
- Selects the **top-k clustered important KV positions per attention head**, applying a pooling/clustering step so the retained positions capture coherent spans rather than scattered isolated tokens.
- Compresses the cache immediately after prefill, then generation proceeds against the compressed cache.

## Key Result
- **3.6×** increase in generation speed.
- **8.2×** improvement in memory efficiency at 16K tokens.
- Can process up to **380K context tokens** on a single A100-80GB GPU.

## Limitation
- Compression is decided from a **single observation window**, so it may miss importance shifts that emerge later in generation (no re-evaluation once decoding starts).
- Depends on the **consistency of per-head attention patterns** between the observation window and the rest of generation — if a head's focus shifts substantially, the pre-selected cache can miss what's actually needed.
- Because selection is query/prompt-driven at prefill time, a compressed cache tuned for one query does not necessarily generalize well to a different follow-up query over the same context (see KVzip, which was designed specifically to address this multi-query weakness).

## Relation to Other Methods
- Compared to H2O, SnapKV trades per-step adaptive eviction for a cheaper, one-shot, prefill-time selection — much faster, but less able to react to changing needs during generation.
- Compared to StreamingLLM, SnapKV chooses *content-dependent* important positions rather than a fixed structural set (sinks + recency window).
