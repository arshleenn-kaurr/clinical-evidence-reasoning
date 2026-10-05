# Phase 4.1 public validation report

Date: 2026-10-04. Scope: resolving the public-release architecture problem identified at the end of Phase 4 (the stripped public preview could not run the full accepted-paper reproduction pipeline) and making the public/archive distinction explicit and technically correct, without weakening the full archival reproduction path or altering any historical artifact or scientific result.

## 1. Public dependency audit

`docs/public_dependency_audit.md` (Phase 4.1, Step 1; not repeated in this phase). Finding: every pre-existing full-archive tool (`verify_hashes.py`, the `phase3_*.py` family, `validate_accepted_papers.py`, the original test suite, both CI jobs, and the README's single reproduction command) required at least one `LICENSE_REVIEW` input, so none of them worked unmodified against the stripped preview.

## 2. Public validator status

`scripts/validate_public_release.py`, now 13 steps (added step 13 in this phase; see §9 "hardening"). Runs clean against the full repo (step 6 excepted — expected, since the full repo legitimately contains restricted files) and against an isolated copy of the built preview (0 problems, 0 notes).

## 3. Stripped-preview validation status

Rebuilt `dist/public_release_preview/` (`scripts/build_public_release.py`), copied it to a location **outside** this repository, and ran `scripts/validate_public_release.py` from there — no parent-repo fallback possible. Result: **PASS, 0 problems.** See `validation/public_preview_validation/logs/` and §FINAL ACCEPTANCE TEST below for the exact commands/exit codes from this phase's run.

## 4. Public-safe pytest status

`python -m pytest -m public`: all public-marked tests pass, run both inside this repo and from the isolated preview copy. Coverage: manifest/hash integrity, repo structure, experiment-manifest parsing, public-safe provenance-path checks, no-restricted-file and no-unmanifested-file checks, the two reconstructed-code artifacts (built into a scratch temp dir — see §9), doc-link resolution, `CITATION.cff`, required-docs presence, secret scan, and the end-to-end CLI exit code.

## 5. Archive-only pytest status

`python -m pytest -m archive`: unchanged and still passing — data integrity, GenAI4Health/AgenticLS structural checks, live re-execution and byte-for-byte comparison of all four archived analysis scripts, and archive-scope provenance checks (hash report, experiment-manifest path references). Not weakened in this phase.

## 6. CI split status

`.github/workflows/reproducibility.yml` unchanged from Phase 4.1 Step 5 (not repeated): `public-integrity` always runs; `full-archive-reproduction` self-detects the presence of a known `LICENSE_REVIEW` marker file and skips cleanly, not failing, when absent.

## 7. README wording changes

Unchanged from Phase 4.1 Step 7 (not repeated): the Reproducibility section presents the two explicit levels and commands. This phase additionally reworded the posthoc-discrepancy bullet to the concise public-facing disclosure language (§11) and left everything else as written.

## 8. Public manifest changes (Phase 4.1, Step 9)

Regenerated `docs/public_release_manifest_draft.csv` and `dist/public_release_preview/MANIFEST.csv`. All hashes re-verified (`scripts/verify_hashes.py`: ALL HASHES OK; `scripts/build_public_release.py`: 334 files copied, 0 mismatches).

Reassessed classifications, per the three options given (A: public but documented as archive-only; B: `PUBLIC_OPTIONAL` instead of misleading `PUBLIC_CORE`; C: exclude):

| Category | Before | After | Option chosen | Why |
|---|---|---|---|---|
| Level-1 tooling (`build_public_release_manifest.py`, `build_public_release.py`, `validate_public_release.py`, `scripts/reconstructed/*.py`) | `PUBLIC_CORE` | `PUBLIC_CORE` (unchanged) | — | These actually work on the stripped preview; the classification was already accurate. |
| Level-2-only tools (`verify_hashes.py`, `validate_accepted_papers.py`, the `phase3_*.py` family, `validate_result_provenance.py`, `canonicalize_results.py`, `validate_environment.py`) | `PUBLIC_CORE` (misleading: implied they run out of the box) | `PUBLIC_OPTIONAL` | **B** | Each file's own header/docstring already says "requires the complete archive"; downgrading to `PUBLIC_OPTIONAL` stops the manifest itself from implying otherwise, while still shipping the code for transparency/auditability (not excluded — Option C was rejected: hiding the methodology would reduce, not improve, public trust). |
| Archive-only test files (`test_data_integrity.py`, `test_genai4health_structure.py`, `test_agenticls_structure.py`, `test_analysis_reproduction.py`, `test_artifact_hashes.py`) | `PUBLIC_CORE` | `PUBLIC_OPTIONAL` | **B** | Exclusively `@pytest.mark.archive`; shipped for transparency, not claimed runnable under `pytest -m public`. |
| `conftest.py`, `test_public_release.py`, `test_provenance.py` | `PUBLIC_CORE` | `PUBLIC_CORE` (unchanged) | **A** | Needed for `pytest -m public` itself to be a complete, runnable suite (shared fixtures; `test_provenance.py` contains one genuinely public test). Documented accordingly. |
| CI workflow | `PUBLIC_CORE` | `PUBLIC_CORE` (unchanged) | **A** | The workflow file itself documents and enforces the public/archive split — it is the mechanism, not something that "fails" on the public repo. |
| `docs/**` | `PUBLIC_CORE` | `PUBLIC_CORE` (unchanged; judgment call) | **A** | Contains no `LICENSE_REVIEW` content (only hashes, paths, and derived summaries); some files describe Level-2 findings but none of them are executable, so "cannot function in the stripped public repo" does not apply the same way it does to scripts/tests. Kept public for transparency rather than reclassified. |
| Scientific data (cohorts, prompts, raw/canonical results, candidate/audit CSVs) | `LICENSE_REVIEW` | `LICENSE_REVIEW` (unchanged) | — | Not touched. Classification of scientific data was never changed to satisfy tooling, in either direction. |
| Latent v1 artifacts | `ARCHIVAL_ONLY` | `ARCHIVAL_ONLY` (unchanged; reason text corrected) | — | See §10. Already correctly archival; only the documented *reason* changed from "paper role unknown" to the corrected status. |

Net effect: `PUBLIC_CORE` 171 → 154, `PUBLIC_OPTIONAL` 162 → 180, `LICENSE_REVIEW` 64 → 64 (unchanged), `ARCHIVAL_ONLY` 38 → 38 (unchanged), `SCRATCH_IGNORE` 4 → 4 (unchanged). Total files classified: 440.

## 9. Hardening improvements applied in this phase

1. **Reconstructed-artifact checks no longer touch the checkout.** `scripts/reconstructed/plot_genai4health_figure1.py` and `scripts/reconstructed/build_canonical_results_reference.py` each gained an output-path override (`--out-dir` / `--out`; default unchanged for direct standalone use — verified still byte-identical). `scripts/validate_public_release.py` steps 7 and 8 now pass a `tempfile.TemporaryDirectory()` path, so running the public validator never writes into `validation/reconstructed_figures/` or `validation/reconstructed_reference/` inside the checkout being validated.
2. **Unmanifested-file check (new Step 13).** Every ordinary file under the checkout must either be a row in `docs/public_release_manifest_draft.csv` or belong to a two-item allowlist of files `scripts/build_public_release.py` itself generates at preview-build time (`MANIFEST.csv`, `PREVIEW_ONLY.txt`). `.git/`, `__pycache__/`, `.pytest_cache/`, `dist/`, and local scratch/venv directories are never treated as release artifacts (reused from `build_public_release_manifest.py`'s own ignore rules, not redefined). Verified by planting a throwaway unclassified file and confirming the check fails, then removing it and confirming it passes again.

## 10. LICENSE placeholder handling (Phase 4.1, Step 10)

No license was chosen. `LICENSE` was replaced with `LICENSE-TODO.md` (same "no license chosen, all rights reserved, TODO" content, now explicit that it is a placeholder and deliberately **not** named `LICENSE`/`LICENSE.md` so no host's automatic license detector infers a license from it). All references to the old filename (`scripts/build_public_release_manifest.py`, `scripts/validate_public_release.py`'s structure and required-docs checks) were updated. This remains a documented **Phase 5 blocker**: choosing an actual license is the authors' decision, not something performed here.

## 11. Latent-v1 correction (Phase 4.1, Step 11)

Corrected from "paper role UNKNOWN" to:

> **STATUS: SUPERSEDED / EXCLUDED FROM REPORTED ANALYSES** — per the accepted-paper record, quality metadata remained visible, confidence intervals were inadvertently removed from some reconstructed anchors, and it was not used as evidence in the reported manuscript.
> **PUBLIC RELEASE DEFAULT: `ARCHIVAL_ONLY`** (unchanged — it was already classified this way; only the documented reason was corrected).

Updated: `experiments/static_conflict/latent_v2/README.md`, `experiments/static_conflict/latent_v2/experiment_manifest.json` (added `status` / `public_release_default` fields, corrected `paper_relationship`/`notes`), `experiments/static_conflict/README.md`, `docs/recovery_status.md`, `docs/public_artifact_plan.md`, `docs/limitations.md`, and the four `latent_main*`/`latent_gemini`/`latent_anchor_audit` rules in `scripts/build_public_release_manifest.py` (reason text only — all four rows were already `ARCHIVAL_ONLY`).

Not deleted. Not further analyzed. The standalone **dominant-evidence analysis** status is explicitly **unchanged** (still unknown manuscript-generation role), as instructed.

## 12. Posthoc provenance disclosure status

Unresolved; not claimed resolved; not altered in substance. Canonical public-facing wording (verbatim from this phase's instructions) is now used consistently in `README.md`, `docs/limitations.md`, and as a "Public-facing summary" block prepended to the top of `docs/posthoc_hash_investigation.md` (the detailed investigation below it is unchanged):

> "The archived post-hoc analysis manifest records an earlier script hash that is no longer available. The recovered script differs from that recorded hash but regenerates all archived post-hoc outputs byte-for-byte under the verified reproduction environment (SciPy 1.16.3). The historical code change cannot be reconstructed and is retained as a provenance limitation."

## 13. Remaining Phase 5 blockers

1. **License selection** (§10) — human decision, not automatable; `LICENSE-TODO.md` makes the unresolved state explicit rather than presenting a placeholder as a real license.
2. **License review for the 64 `LICENSE_REVIEW` files** — unchanged from Phase 4 (`docs/public_release_audit.md`).
3. **Camera-ready manuscripts and final citation metadata** — unchanged.
4. **`posthoc_contrasts.py` provenance gap** — disclosed (§12), not resolved; a decision on exactly how to present it in the paper text itself remains the authors'.
5. **Latent v1's correction should be reviewed by the authors** for accuracy before any public release — this phase's wording is based on the record provided in this request, not independently re-derived from new analysis (none was performed, per instruction).
6. **CI has not been dispatched on an actual GitHub Actions runner** in this phase; validated via the equivalent local commands only (§FINAL ACCEPTANCE TEST).
7. The 180 `PUBLIC_OPTIONAL` Level-2 tools/tests/docs, while no longer misleadingly `PUBLIC_CORE`, still represent a large surface area for a first public release; a future narrower "`--core-only`" release (already supported by `scripts/build_public_release.py --core-only`) is available but not exercised as the default here.

## PHASE 4.1 STATUS: **PASS**

All thirteen requested steps were completed, both hardening improvements were implemented and verified, no historical artifact was altered, no scientific result or licensing classification of scientific data was changed, and the final acceptance test (below) passed independently for both the full archival repo and the stripped public preview.
