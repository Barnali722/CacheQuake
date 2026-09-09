# Citations

Primary sources backing the notes in `papers/`. All KV-cache-policy benchmarks referenced in our project (Full Cache, Sliding Window, H2O, SnapKV, StreamingLLM) are directly simulated in our interactive pipeline. BDH/BDH-GPU figures are published results from the original paper, not reproduced by us — see the disclaimer in `dragon_hatchling_bdh.md`.

## KV-Cache Management

1. **H2O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models**
   Zhang, Z., Sheng, Y., Zhou, T., Chen, T., Zheng, L., Cai, R., Song, Z., Tian, Y., Ré, C., Barrett, C., et al.
   *Advances in Neural Information Processing Systems (NeurIPS) 36*, 2023.
   arXiv:2306.14048 · Code: github.com/FMInference/H2O

2. **Efficient Streaming Language Models with Attention Sinks**
   Xiao, G., Tian, Y., Chen, B., Han, S., Lewis, M.
   *International Conference on Learning Representations (ICLR)*, 2024.
   arXiv:2309.17453

3. **SnapKV: LLM Knows What You Are Looking for Before Generation**
   Li, Y., Huang, Y., et al.
   arXiv:2404.14469, 2024.

4. **Quest: Query-Aware Sparsity for Efficient Long-Context LLM Inference**
   Tang, J., Zhao, Y., Zhu, K., Xiao, G., Kasikci, B., Han, S.
   *International Conference on Machine Learning (ICML)*, 2024.
   arXiv:2406.10774 · Code: github.com/mit-han-lab/quest

5. **KVzip: Query-Agnostic KV Cache Compression with Context Reconstruction**
   Kim, J.-H., Kim, J., Kwon, S., Lee, J. W., Yun, S., Song, H. O.
   *Advances in Neural Information Processing Systems (NeurIPS)*, 2025 (Oral).
   arXiv:2505.23416 · Code: github.com/snu-mllab/KVzip

## Architecture-Level Alternative

6. **The Dragon Hatchling: The Missing Link between the Transformer and Models of the Brain**
   Kosowski, A., Uznański, P., Chorowski, J., Stamirowska, Z., Bartoszkiewicz, M.
   arXiv:2509.26507, 2025.
   Code: github.com/pathwaycom/bdh

## Notes on Sourcing
- Entries 1–5 are used for the KV-cache-policy comparison table and the "Existing Approaches" sections of the One-Page Concept Summary and README.
- Entry 6 is the sole primary source for all BDH/BDH-GPU claims; any BDH-related numeric result elsewhere in this repo should trace back to it and be flagged "published, not reproduced."
- If a new KV-cache method is added to the comparison (e.g., PyramidKV, TOVA), add its arXiv entry here before referencing it in `papers/`.
