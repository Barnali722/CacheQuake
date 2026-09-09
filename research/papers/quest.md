# Quest — Query-Aware Sparsity for Efficient Long-Context LLM Inference

**Authors:** Tang, Zhao, Zhu, Xiao, Kasikci, Han
**Paper:** arXiv:2406.10774 (ICML 2024) · Code: github.com/mit-han-lab/quest

## Core Idea
The criticality of a token in the KV cache is not fixed — it depends heavily on the **current query**. A token that matters for one query may be irrelevant for the next, so a single static importance score (as used by H2O or SnapKV) is fundamentally limited.

## Problem
For long-context LLMs (128K–1M token windows), inference slows sharply as context grows because loading the full KV cache dominates self-attention latency — e.g., a 32K-context Llama-7B model can spend over half its inference time just loading a ~16GB KV cache.

## Observation
Prior "small set of critical tokens dominates attention" findings (as in H2O) are only part of the picture: *which* tokens are critical shifts with the query, so query-agnostic eviction risks discarding tokens that a later query actually needs.

## Method
Quest manages the KV cache at **page granularity** (blocks of tokens) rather than per-token, and works in two stages:
1. **Criticality estimation:** for each page, Quest stores the per-channel **min and max Key vectors**. It takes the element-wise product of the current **Query vector** with both the Min-Key and Max-Key vectors, then sums the per-channel maximum to estimate that page's criticality for this specific query.
2. **Sparse attention:** only the **Top-K critical pages** are loaded from memory, and self-attention is computed just over those pages.

This is done at every decoding step, so the selected pages can change from query to query and step to step — nothing is permanently evicted the way H2O/SnapKV/StreamingLLM evict tokens.

## Key Result
- Up to **7.03×** speedup in self-attention.
- Up to **2.23×** reduction in end-to-end decode-phase latency.
- Near-perfect (99–100%) passkey-retrieval accuracy with very small token budgets (e.g., 64 tokens at 10K context, 1024 tokens at 100K context) — substantially outperforming H2O, TOVA, and StreamingLLM, which the paper reports near 0–10% accuracy on the same task under comparable budgets.

## Limitation
- Because pages are never truly evicted (all KV data is kept in memory; only *loading* is sparsified), Quest saves attention latency and memory *bandwidth*, but not memory *capacity*, the way an eviction method like H2O or SnapKV does.
- Adds page-level metadata (min/max Key vectors) and a per-step scoring computation, which is extra overhead relative to static-window methods like StreamingLLM.
- Query-aware scoring must be recomputed at every step, so gains depend on the KV cache being memory-bandwidth-bound rather than compute-bound.

## Relation to Other Methods
- Directly targets the weakness Quest's authors identify in H2O/SnapKV/StreamingLLM: those methods commit to a fixed retained set that does not adapt per query.
- KVzip takes almost the opposite stance — it deliberately seeks a **query-agnostic** compressed cache so it can be reused across many queries without Quest's per-step recomputation.
