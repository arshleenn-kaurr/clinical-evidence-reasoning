# Phase 4 release-readiness report

Date: 2026-10-04. Scope: reproducibility/release engineering around the two accepted-paper archives. **No API calls.** Nothing under any `historical_package/` was modified (verified repeatedly below). Nothing was committed, pushed, or published.

## 1. Pinned environment status

Python **3.12.15**, numpy **2.5.3**, pandas **3.0.6**, scipy **1.16.3** (the version Phase 3 showed reproduces all 8 archived post-hoc CSVs byte-for-byte). Pinned via `.python-version`, `requirements-reproduction.txt`, and a fully hashed `requirements-reproduction.lock.txt` (`uv pip compile --generate-hashes`). This is a **verified reproduction environment**, explicitly not claimed as the historical one (`docs/reproduction_environment.md`, `docs/environment_validation.md`). A separate `requirements-reconstructed.txt` (matplotlib) is optional, only for `scripts/reconstructed/`.

**Status: PASS.**

## 2. Clean-environment reproduction status

A **fresh** venv was built from `requirements-reproduction.lock.txt` via `uv venv --python 3.12` + `uv pip install` in an isolated scratch location (not the repo's own `validation/.venv312`), with no prior state. From that fresh interpreter:

- `python scripts/validate_accepted_papers.py` → **OVERALL: PASS**, exit 0.
- `python -m pytest tests/` → **37 passed**, 0 failed.
- `python scripts/verify_hashes.py` → **ALL HASHES OK**, both before and after.

**Status: PASS.**

## 3. pytest results

37 tests across `tests/test_data_integrity.py`, `test_genai4health_structure.py`, `test_agenticls_structure.py`, `test_analysis_reproduction.py`, `test_provenance.py`: **37 passed, 0 failed**, run twice (pinned local venv and a from-scratch venv). Coverage: cohort/anchor hashes, expected case/prompt counts, per-experiment structural verification (duplicate/missing IDs, condition coverage, raw↔canonical mapping, attempt-status counts, arm-order balance, branch-point links), live re-execution of all four archived analysis scripts compared byte-for-byte against the archive, and result-provenance schema/path validation.

**Status: PASS.**

## 4. CI workflow status

`.github/workflows/reproducibility.yml`: two jobs, `fast-integrity` (hashes, structure, provenance schema) and `full-reproduction` (the single validation command + pytest + a `git status` check that nothing under `historical_package/` changed). No secrets required; never contacts Gemini/Groq/any external API; the Groq extension is never built or analyzed. Not executed inside GitHub Actions during this phase (no network submission was made, per the "do not publish" rule) — validated by running the equivalent commands locally in a clean environment (§2), which is what each CI step runs.

**Status: PASS (locally validated equivalent; not dispatched to GitHub).**

## 5. Figure 1 reconstruction status

**DATA_EXACT / PLOT_RECONSTRUCTED.** `scripts/reconstructed/plot_genai4health_figure1.py` (clearly labeled, new Phase 4 code) redraws both panels from the archived, Phase-3-reproduced post-hoc CSVs. Every annotated value matches the archived figure; layout, labels, and displayed statistics match; exact pixel/visual reproduction was not attempted (not required). See `docs/figure1_reconstruction.md`.

## 6. Canonical-reference reconstruction status

**EXACT_MATCH (byte-identical).** `scripts/reconstructed/build_canonical_results_reference.py` (new, clearly labeled) regenerates `canonical_results_reference.md` from archived CSVs; the output hashes identically to the archive (`5ba79e10…`). Three sections' cohort ordering could not be derived from any recovered file and was hardcoded as a documented presentation choice. See `docs/canonical_reference_reconstruction.md`.

## 7. Result-provenance validation

`docs/result_provenance.csv`: **122 rows, 122 unique `result_id`s**, all required columns present, every path reference resolved (`scripts/validate_result_provenance.py`, run standalone and inside `validate_accepted_papers.py` and `tests/test_provenance.py`). Reserved `camera_ready_location` / `table_number` / `figure_number` / `section` columns added, all `TODO` — nothing guessed.

**Status: PASS.**

## 8. Public release manifest status

`docs/public_release_manifest_draft.csv`: **429 files classified**, `source_sha256` recorded for every non-ignored file:

| Tier | Count |
|---|---|
| PUBLIC_CORE | 161 |
| PUBLIC_OPTIONAL | 162 |
| LICENSE_REVIEW | 64 |
| ARCHIVAL_ONLY | 38 |
| SCRATCH_IGNORE | 4 |

`scripts/build_public_release.py` (dry run) copied the 323 `PUBLIC_CORE` + `PUBLIC_OPTIONAL` files into `dist/public_release_preview/` with a `MANIFEST.csv` recording source/copied sha256 per file: **0 mismatches**. `dist/` is gitignored; nothing was published.

**Status: PASS (preview only).**

## 9. Licensing blockers

64 files remain `LICENSE_REVIEW`: raw MEDAL Cochrane/AHA source text, frozen cohorts and generated prompts built from it, candidate/audit CSVs, and raw/clean model outputs across all three accepted-paper packages (provider-output redistribution terms also unresolved). None of this is included in the `PUBLIC_CORE`/`PUBLIC_OPTIONAL` preview. See `docs/public_release_audit.md`, `docs/public_artifact_plan.md`.

**Status: BLOCKED for those 64 files specifically; does not block the rest of the preview.**

## 10. Archival/public separation

Every experiment keeps an intact `historical_package/`; the public-facing layer (`README.md`s, `experiment_manifest.json`s, `docs/`, `scripts/`, `tests/`) sits beside it without duplicating data. The Groq extension's entire `historical_package/` is `ARCHIVAL_ONLY` by explicit rule (its own navigational docs stay `PUBLIC_OPTIONAL` so the boundary is visible). `scripts/build_public_release_manifest.py` encodes this separation as data (the CSV), not as ad hoc judgment calls scattered through the tree.

## 11. Known provenance limitations (full list: `docs/limitations.md`)

1. `posthoc_contrasts.py` script-hash mismatch — unresolved, documented, not "fixed."
2. Figure 1 plotting code — missing, reconstructed (new code).
3. `canonical_results_reference.md` generator — missing, reconstructed (new code, byte-identical output).
4. Historical numpy/pandas/scipy versions — unknown; current pin is a verified-reproducing environment, not a historical claim.
5. Static Gemini primary/veto — no attempt logs.
6. Camera-ready manuscripts — pending (see §12).
7. Data/provider-output redistribution rights — pending review (§9).
8. Latent v1 and the dominant-evidence analysis — unknown relationship to either paper.
9. Groq extension — separate, incomplete, out of scope everywhere in this repo's tooling.

## 12. Camera-ready TODOs

Both papers marked `CAMERA-READY PENDING` throughout (`papers/*/README.md`, `papers/*/paper/README.md`, `CITATION.cff`, `docs/recovery_status.md`). No PDF, DOI, page numbers, proceedings volume, or final author ordering is guessed anywhere. `docs/result_provenance.csv`'s 4 reserved columns are ready to fill in once available.

## 13. Groq extension status

**POST-ACCEPTANCE CROSS-MODEL EXTENSION. STATUS: IN PROGRESS / NOT CANONICALIZED.** Explicitly excluded from `scripts/validate_accepted_papers.py`, `tests/`, CI, and the public-release manifest (`ARCHIVAL_ONLY` wholesale). Not analyzed, not canonicalized, not touched in this phase beyond re-confirming its scope labeling.

## 14. Remaining blockers before public GitHub release

1. License review for the 64 `LICENSE_REVIEW` files (§9) — human decision required, not automatable.
2. Camera-ready manuscripts and final citation metadata.
3. Resolve or formally accept the `posthoc_contrasts.py` provenance gap as a disclosed limitation in the paper text.
4. Decide the fate of latent v1 and the dominant-evidence analysis (reported / superseded / archive-only).
5. A repository license has not been chosen (`LICENSE` is a TODO placeholder).
6. Dispatch `.github/workflows/reproducibility.yml` on an actual GitHub Actions runner at least once before relying on it (locally equivalent-validated only, §4).
7. Decide what, if anything, to do with the Groq extension once it completes and is canonicalized (separately, out of scope here).

## PHASE 4 STATUS: **PASS WITH DOCUMENTED BLOCKERS**

All reproducibility-engineering goals (pinned environment, automated tests, CI config, two faithful reconstructions, formalized provenance, public/archival separation, documentation, byte-for-byte preservation of every historical artifact) were met and verified. The remaining blockers (§14) are release/licensing/editorial decisions outside this phase's scope, not reproducibility failures — none of them was "fixed" by altering historical material.
