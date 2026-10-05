# Data and artifact rights (draft)

This file exists so a reader never has to guess whether the code license (MIT, see `LICENSE`) also covers the data files in this repository. **It does not.**

**Scope of the MIT License.** The MIT License in [`LICENSE`](LICENSE) applies to **project-authored code only** (and the project-authored documentation and synthetic evidence cards described in `THIRD_PARTY_NOTICES.md`). It does **not** grant any right to redistribute: MEDAL-derived material; Cochrane-derived material; AHA-derived material; provider-generated (Gemini/Groq) model outputs; any artifact classified `LICENSE_REVIEW`; or the camera-ready paper PDFs (unless separately permitted by their copyright holders). Those remain under separate, unresolved review and are excluded from the public release.

## The short version

The software license (MIT, `LICENSE`) covers **code only**: everything under `scripts/`, `src/`, `tests/`, and the frozen runner/analysis code preserved inside `historical_package/`. It does **not** extend to:

- the frozen cohorts, generated prompts, or raw/canonical model outputs (64 files currently classified `LICENSE_REVIEW` — see `docs/licensing_decision_matrix.md`), whose redistribution status is under review and unresolved;
- any paper PDF (the AgenticLS camera-ready is ingested locally but classified `PUBLIC_RELEASE_PENDING_PERMISSION` and not part of any public build), which is governed by the workshop/publisher's own copyright policy and the authors' permission, neither of which has been established here.

## Why this separation matters here specifically

This repository's data has a documented, non-uniform provenance chain (`docs/data_provenance.md`): MEDAL exports → Cochrane/AHA-derived anchors → project-constructed cohorts → project-authored prompts wrapping that cohort text → provider-generated model outputs that may restate it. A single blanket statement ("this repo is licensed under X") would be actively misleading about which layer of that chain X actually covers. See `THIRD_PARTY_NOTICES.md` for the per-layer breakdown.

## What is NOT claimed here

- This file does not claim the project authors hold copyright over MEDAL, Cochrane, or AHA content.
- This file does not claim a right to redistribute any `LICENSE_REVIEW` file.
- This file does not claim Google's or Groq's terms permit or forbid redistributing their model outputs — that determination has not been made.
- This file does not grant any rights itself; it documents the *question*, not an answer.

## What public release actually does today, regardless of this file

Independent of any legal determination, `scripts/build_public_release.py` (and its `--v1-core` variant) **mechanically excludes** every file classified `LICENSE_REVIEW` or `ARCHIVAL_ONLY` from any build — verified by `scripts/validate_public_release.py` step 6 ("no LICENSE_REVIEW / ARCHIVAL_ONLY file is present") on every run, including from an isolated copy outside this repository. This is an engineering control that holds regardless of how the legal questions above are eventually resolved.

## Project-authored synthetic content

The lower-tier conflicting/aligned evidence cards used in every experiment are explicitly **not** claimed to be real studies (`analysis_contract.md`: "Synthetic lower-tier cards are perturbations, not claimed real studies"). This synthetic content, and the prompt template/schema wrapping it, is project-authored and not subject to the review above.

## Resolution path

See `docs/licensing_decision_matrix.md` (per-group disposition and confidence), `docs/restricted_artifact_substitutes.md` (what's already public in place of each restricted group), and `docs/final_release_checklist.md` (LEGAL / LICENSING section) for the concrete next steps. This is explicitly an author/legal decision, not something resolved by this document.
