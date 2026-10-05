# Release / tag strategy

Proposal only. **No tag or release is created by this document or this phase.**

## Proposed tags

| Tag | Freezes | Points to |
|---|---|---|
| `v1.0.0` | The first public reproducibility release: the `V1_CORE` + `V1_SUPPORTING` scope (`docs/public_v1_scope.md`), built via `scripts/build_public_release.py --v1-core`. | Same repo history as every other tag below — see "shared history" note. |
| `genai4health-2026-camera-ready` | The exact state of `experiments/static_conflict/` + `papers/genai4health/` at the moment the GenAI4Health camera-ready PDF is ingested (`scripts/ingest_camera_ready.py --paper genai4health`). | Same repo history. |
| `agenticls-2026-camera-ready` | The exact state of `experiments/persistent_context/{gemini_persistent_260,gemini_aligned_control_40}/` + `papers/agenticls/` at the moment the AgenticLS camera-ready PDF is ingested. | Same repo history. |
| `gpt-oss-persistent-extension-v1` (potential, later) | A future state once the Groq GPT-OSS persistent-context extension is complete and canonicalized — explicitly **not proposed now**; the extension remains out of scope for this phase and for `v1.0.0`. | Same repo history, once it exists. |

## Same repo history, not separate release assets

**Recommendation: all tags point into the same repository's commit history**, not separate per-paper repos or orphan branches. Reasoning:
- The static-conflict benchmark is the shared foundation both papers build on (`experiments/static_conflict/` supports GenAI4Health directly and AgenticLS's methodology). Splitting it across separate histories would duplicate or fragment that foundation.
- `docs/result_provenance.csv` already cross-references both papers' results against the same artifact tree; separate histories would break those relative paths.
- A tag is cheap and precise (`git tag <name> <commit>`); it does not require separate release *assets* unless a paper-specific *subset* of files is wanted as a downloadable archive (see below), which GitHub Releases supports without needing a separate repo or branch.

A paper-specific tag can still carry its own **release asset** (e.g. a zip of just `experiments/static_conflict/` + `papers/genai4health/` at that commit) if a reviewer wants a minimal paper-scoped download, without requiring separate history.

## How manifests map to tags

Each tag's exact file set and hashes are fully determined by:
1. The commit it points to (ordinary git content-addressing).
2. `docs/public_release_manifest_draft.csv` as of that commit (which `PUBLIC_CORE`/`PUBLIC_OPTIONAL`/etc. files existed and their hashes).
3. For `v1.0.0` specifically, `docs/public_v1_scope.csv` as of that commit (which of those were `V1_CORE`/`V1_SUPPORTING` vs. `DEFER_FROM_V1`).

No new tracking mechanism is needed: `git show <tag>:docs/public_release_manifest_draft.csv` (once this is a git repo) reproduces exactly what that tag's public release contained.

## How camera-ready PDFs should be associated

Once `scripts/ingest_camera_ready.py` (Step 9) has been run for a paper with its final PDF:
1. The PDF lives at `papers/<paper>/paper/<paper>-camera-ready.pdf` (the canonical name written by the ingestion script; Phase 5B instructions that said `paper.pdf` were corrected to this) with its SHA256 recorded in the paper metadata JSON the ingestion script writes.
2. The commit that adds it is tagged `<paper>-2026-camera-ready`.
3. The PDF itself **should also be attached as a release asset** on that tag (not just committed to the repo), so a reader can download exactly the PDF without cloning the whole archive — standard practice for large binary artifacts alongside a reproducibility repo.
4. `CITATION.cff`'s `references` entries for that paper (currently `TODO` placeholders) get filled in from the same ingestion metadata, not guessed separately.

## What this phase does NOT do

No tag was created. No release was created. No branch was created or renamed (there is currently no git repository at all — this repo has not been initialized with `git init` in any phase so far). This document is a plan for when the authors are ready to act on it.


## Versioning policy (author decision, 2026-10-04)

Prepare the private GitHub repository now (first commit "Initial reproducibility release"). **Do not** create `v1.0.0`, paper-specific tags, a GitHub Release, or a Zenodo deposit until the GenAI4Health camera-ready is complete, unless the authors explicitly decide otherwise.

## Phase 5B status of each proposed tag (no tag created)

| Tag | Status | Frozen inputs (see `docs/tag_freeze_manifest.json`) |
|---|---|---|
| `agenticls-2026-camera-ready` | Inputs frozen locally (PDF SHA256 `1b7311a7…2758e5`); inputs frozen against the revised, re-ingested PDF (audit **PASS**); tag DEFERRED by author policy until the GenAI4Health camera-ready is complete | PDF + metadata, experiment manifests it depends on, `docs/camera_ready_provenance_mapping.csv`, number audit |
| `genai4health-2026-camera-ready` | **Waiting for the final camera-ready PDF** (only the anonymized submission was supplied) | none yet |
| `v1.0.0` | **Deferred (author policy, 2026-10-04)**: MIT selected; no `v1.0.0`, paper tags or GitHub Release until the GenAI4Health camera-ready is complete, unless the authors decide otherwise. The private repository and its first commit proceed now | public manifest + `public_v1_scope.csv` at the tagged commit |

The final commit hash for each tag cannot exist until a git repository does (`docs/git_initialization_plan.md`); the freeze manifest records it as `null`.
