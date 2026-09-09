# KVzip — Query-Agnostic KV Cache Compression with Context Reconstruction

**Authors:** Kim, Kim, Kwon, Lee, Yun, Song
**Paper:** arXiv:2505.23416 (NeurIPS 2025, Oral) · Code: github.com/snu-mllab/KVzip

## Core Idea
Existing KV-eviction methods such as SnapKV and PyramidKV are **query-aware**: they score a KV pair's importance using attention from a specific query (or observation window tied to one query). That works well for a single query, but the compressed cache does not transfer well to a *different* follow-up query over the same context. KVzip instead asks: which KV pairs are needed to reconstruct the *entire original context*, independent of any one query?

## Problem
Long contexts blow up KV cache size and attention latency. In realistic multi-turn or multi-query use (e.g., a chat session that asks several questions about the same long document), a query-aware compressed cache built for the first question degrades badly when reused for later, different questions — forcing costly repeated prefill + compression per query.

## Observation
SnapKV attains high accuracy when it prefills and compresses separately for each new query, but accuracy drops sharply when the cache compressed for the *first* query is simply reused for later queries (shown empirically on the SQuAD multi-QA benchmark). This motivates a genuinely query-agnostic compression criterion.

## Method
- Quantifies the importance of each KV pair by testing how well the underlying LLM can **reconstruct the original context** from the cached KV pairs — pairs that contribute little to reconstruction are considered redundant.
- Evicts the lowest-importance KV pairs under this reconstruction-based scoring, producing a single compressed cache that is **reusable across diverse subsequent queries** without re-prefilling.
- Integrates with KV cache **quantization** (e.g., 4-bit) for additional compression on top of eviction.

## Key Result
- Reduces KV cache size by **3–4×** and FlashAttention decoding latency by roughly **2×**, with negligible performance loss on question-answering, retrieval, reasoning, and code-comprehension tasks.
- Evaluated on LLaMA3.1-8B, Qwen2.5-14B, and Gemma3-12B with contexts up to **170K tokens**.
- Near-lossless performance retained down to 20–30% KV cache budgets; in multi-query settings, existing query-aware baselines degrade even at a 90% budget while KVzip does not.

## Limitation
- The reconstruction-based importance scoring requires running the LLM itself to evaluate reconstruction quality, adding overhead at compression time compared to lightweight attention-score heuristics.
- Being query-agnostic is precisely its strength for multi-query reuse, but it may retain some KV pairs that a highly targeted single-query method (like SnapKV, prefiled per-query) would have safely dropped for that one query — i.e., there's a genuine single-query-optimality vs. multi-query-reusability trade-off.

## Relation to Other Methods
- Directly positions itself against SnapKV and PyramidKV, both query-aware, prefill-time eviction methods; KVzip's contribution is trading a bit of single-query optimality for much better multi-query reuse.
- Complementary rather than opposed to Quest: Quest keeps everything in memory and sparsifies which pages are *loaded* per query; KVzip actually *evicts* KV pairs once, up front, in a way meant to serve many future queries.
