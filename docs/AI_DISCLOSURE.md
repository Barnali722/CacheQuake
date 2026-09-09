# AI Disclosure — CacheQuake

**Team:** Game of Codes (Barnali Tanti — Team Leader, Sangramjeet Choudhury, MD Aftab Hossain, Jayita Jana) · DataForge 2026.

## Summary statement

AI assistance supported development and documentation of CacheQuake. The team remained responsible for implementation decisions, code review, technical verification, research interpretation, testing, and all final decisions submitted for judging.

## What is verified from the repository itself

The codebase contains direct, first-party evidence of AI-assisted development:

- `backend/README.md` and `backend/SETUP.md` explicitly document iterative debugging sessions (e.g., the v1 → v2 → v3 training-loss bug history, the Python 3.14 / pydantic wheel-compatibility investigation), consistent with an AI-assisted, fast-iteration workflow during a timed hackathon.
- Code comments throughout `backend/app/cache_policies/` explicitly document *why* certain approximations were made relative to published papers (e.g., the proxy dot-product score in `heavy_hitter.py` instead of true softmax attention weights) — the kind of self-aware, written-out reasoning trail that is easier to produce with AI pair-programming support under time pressure.
- `backend/data/precomputed/bdh_published_claims.json` contains an explicit `"how_accessed"` field stating the team worked from public abstracts and summaries rather than the full paper PDF, and an explicit refusal to fabricate quantitative BDH figures it could not verify — a documented instance of AI-assisted content generation being constrained by an explicit accuracy requirement.

Beyond these first-party artifacts, the repository does not contain a change-by-change log of which specific tool produced which specific line, so a fully itemized, tool-by-tool, commit-by-commit disclosure is not reconstructable from the code alone. `[VERIFY IMPLEMENTATION]` — the team should supplement this file with their own daily AI-usage log if one was kept, as the original `PRD_KV_Cache_Explainer.md` instructs ("AI-assistance disclosure ... logged daily").

## Categories of AI assistance evident in or consistent with the repository

- **AI-assisted coding** — implementing the cache policies, FastAPI endpoint, and React components, consistent with the density and consistency of docstrings and comments across the codebase.
- **AI-assisted debugging** — the documented training-loss iteration history (v1/v2/v3) and the pydantic/Python-3.14 wheel-compatibility troubleshooting in `SETUP.md`.
- **AI-assisted documentation** — this documentation set (`README.md`, `ARCHITECTURE.md`, `docs/README.md`, `docs/LICENSES.md`, this file, and `research/citations.md`) was produced with AI assistance, based on a direct inspection of the uploaded repository archive and independent web verification of the cited papers' abstracts. No implementation code was modified as part of producing this documentation.
- **AI-assisted research organization** — compiling and cross-checking the citation list in `research/citations.md` against each paper's public abstract.

## What AI assistance was **not** used for, per this documentation pass

- No benchmark numbers, accuracy percentages, or performance figures in `backend/data/precomputed/accuracy_vs_budget.json` were generated or altered by this documentation pass — they were read directly from the repository's existing, locked file.
- No paper text, figures, or tables were reproduced verbatim; all citations in `research/citations.md` are paraphrased and independently checked against each paper's public abstract page.
- No team member's individual contribution was invented; where per-member contribution detail was not present in the repository, this documentation marks it `[VERIFY CONTRIBUTIONS]` rather than guessing.

## Team responsibility

Per the project's own `PRD_KV_Cache_Explainer.md`, AI-assistance logging was intended to be a daily, all-team practice compiled by the Docs/Design/Ops lead. This file reflects what can be verified from the delivered repository and the process of producing this documentation pass; it should be reviewed and expanded by the team with their own first-hand account of tool usage before final submission.
