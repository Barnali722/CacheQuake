# The Cost of Perfect Memory: Why KV Caches Grow and How BDH Stops It

*By the CacheQuake Team*
*DataForge 2026 — Pathway × Rime Track*

## The Linear Growth Problem

If you've ever used a large language model to summarize a long PDF or write code over a massive repository, you might have noticed the system slowing down or running out of memory. This bottleneck is fundamentally tied to the **Key-Value (KV) Cache**. 

Every time a Transformer generates a new token, it pays attention to every token it has previously processed. To avoid recomputing these states from scratch, the model saves the "Key" and "Value" tensors for each token in a cache. 

The problem? **This cache grows linearly with sequence length.** Every new token adds one row to the cache, per attention head, per layer. For a 100,000-token document, the memory footprint of the KV cache can easily exceed the size of the model weights themselves. This is the cost of "perfect memory."

## The Band-Aid: Eviction and Compression

To prevent the KV cache from consuming all available VRAM, researchers have devised various ways to bound its size. 

1. **Sliding Window (e.g., StreamingLLM)**: This policy acts like a goldfish, only keeping the most recent *N* tokens in the cache. It strictly bounds memory, but anything outside the window is forgotten entirely. 
2. **Heavy Hitter (e.g., H2O)**: This policy notices that some tokens (like punctuation or crucial entities) receive disproportionately high attention scores. It selectively evicts the "least attended" tokens. 

While these methods bound memory, they still fundamentally rely on a tabular, row-by-row storage mechanism. They trade exactness for a bounded budget. If a crucial fact is buried in an evicted token, the model simply cannot retrieve it.

## The Architectural Cure: BDH Recurrent

What if we didn't store rows of past tokens at all? 

The **BDH (Beyond Dense-Hop)** architecture, proposed in late 2025 (Yıldız et al., arXiv:2509.26507), takes a radically different approach. Instead of a growing table, BDH replaces the KV cache with a **fixed-size synaptic weight matrix**.

When a new key-value pair arrives, it isn't appended to a list. Instead, it is written directly into this state matrix via a local Hebbian update. Reading from the memory becomes a simple matrix-vector multiplication.

Because the matrix size is fixed, the memory footprint is **$O(1)$** with respect to sequence length. The cache never grows. 

### Forgetting via Interference

If the cache never grows, how does it handle an infinite stream of new information? Rather than strictly *evicting* old tokens, BDH *overwrites* itself. New associations partially write over older ones, leading to "forgetting via interference" rather than deletion. 

In our **CacheQuake** simulator, you can see this live. If you shrink the state budget for the BDH policy, you'll see retrieval accuracy drop, not because the token fell out of a window, but because the finite matrix capacity was exceeded by overlapping associations.

## Try It Yourself

We built [CacheQuake](https://github.com/CacheQuake) to let you feel this mechanics directly. You can drag a slider to watch the Full Cache memory footprint climb linearly, and then switch to Sliding Window, Heavy Hitter, or BDH to see how each policy trades off memory against retrieval accuracy. 

It's one thing to read a math equation about linear growth—it's another to watch the memory chart spike in real-time. Give it a spin, and see for yourself what happens when perfect memory meets a finite budget!
