# StreamingLLM — Efficient Streaming Language Models with Attention Sinks

**Authors:** Xiao, Tian, Chen, Han, Lewis
**Paper:** arXiv:2309.17453 (ICLR 2024)

## Core Idea
LLMs deployed for long or infinite streaming dialogue break down once the sequence exceeds the cache size used at training time, or once early tokens are evicted from a sliding-window cache. StreamingLLM identifies why this happens and fixes it cheaply.

## Problem
KV cache growth with increasing input length creates memory and time-efficiency challenges for long-context LLMs — and naively using a plain sliding window (dropping the earliest tokens once the cache is full) causes a sharp quality collapse rather than a graceful one.

## Observation
The quality collapse under naive sliding-window caching comes from losing the **"attention sink"**: models learn to dump a disproportionate amount of attention onto the first few tokens of a sequence (regardless of their semantic content), likely because the softmax in attention needs somewhere to put "leftover" probability mass. Evicting these initial tokens destabilizes attention distributions for everything that comes after.

## Method
- Retains a small fixed number of **initial "sink" tokens** (e.g., the first 4) permanently in the cache.
- Combines them with a **sliding window of the most recent tokens**.
- Requires **no retraining** of the base model to apply at inference time (though the paper also shows a model can be pre-trained with a dedicated sink token for even better results).

## Key Result
- Enables stable, coherent generation over **very long / effectively unbounded streaming input** using only a small, constant-size cache.
- Matches sliding-window-with-recomputation quality without the cost of recomputation, giving substantial speedups for streaming deployment.

## Limitation
- The retained set (sinks + recent window) is **fixed and content-independent** — it cannot adapt to which tokens are actually semantically important for a given query, unlike H2O or SnapKV.
- Designed primarily for **streaming/generation stability**, not for maximizing task accuracy on tasks that require recalling specific facts from the middle of a long context (its passkey/needle-in-haystack retrieval accuracy is weak compared to query-aware methods like Quest).

## Relation to Other Methods
- StreamingLLM's "keep the important ones + the recent ones" structure is the same shape as H2O's, but it replaces H2O's *learned* importance (heavy hitters) with a *fixed structural prior* (initial sink tokens) — cheaper, but less adaptive.
- SnapKV cites StreamingLLM directly as the baseline it improves on by choosing content-dependent positions instead of just recency + sinks.
