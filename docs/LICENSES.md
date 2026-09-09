# CacheQuake Licenses and Attributions

This document outlines the licensing, attribution, and third-party dependencies for the **CacheQuake** repository.

## Project Code
**CacheQuake** is released under the **MIT License**.
Please refer to the `LICENSE` file in the root directory for the complete and authoritative text of the MIT License applied to all original code in this repository.

## Third-Party Dependencies

### Python Dependencies (Backend)
All Python dependencies utilized in this project are declared in `backend/requirements.txt`. These packages are governed by their respective open-source licenses (such as MIT, Apache 2.0, or BSD), which can be verified via the Python Package Index (PyPI).

### npm/Frontend Dependencies
All frontend dependencies are declared in `frontend/package.json` and `frontend/package-lock.json`. These packages are governed by their respective open-source licenses, which can be verified via the npm registry.

## Project Materials & Assets

### Datasets (Synthetic & Precomputed)
* `backend/data/performance_results.json` - MIT License (Project Code)
* `backend/data/precomputed/accuracy_vs_budget.json` - MIT License (Project Code)
* `backend/data/precomputed/bdh_published_claims.json` - **PUBLISHED RESULT — NOT REPRODUCED** (Data sourced from external academic claims strictly for educational comparison).

### Model Weights
* `backend/model_weights/toy_transformer.pt` - MIT License (Project Code)
* `backend/model_weights/training_metadata.json`[cite: 1] - MIT License (Project Code)

### Images and Diagrams
* `assets/diagrams/architecture-overview.svg`[cite: 1] - MIT License (Project Code)
* `assets/diagrams/bdh-concept.svg`[cite: 1] - MIT License (Project Code)
* `assets/diagrams/cache-policy-comparison.svg`[cite: 1] - MIT License (Project Code)

### Research Papers & Documentation
* `research/citations.md`[cite: 1] - MIT License (Project Code)
* `research/papers/Research Notes H2o,Snapkv.docx`[cite: 1] - Educational notes summarizing third-party academic literature.