# Phase 5A release preparation report

Date: 2026-10-04. Scope: release preparation only — no publish, no GitHub release, no Zenodo deposit, no license selection, no `historical_package/` change, no scientific result change.

## 1. License-review matrix status

`docs/licensing_decision_matrix.csv`/`.md` (Step 1): all 64 `LICENSE_REVIEW` files audited and grouped into 7 artifact-type families. Dispositions: 54 `UNKNOWN` (require actual MEDAL/Cochrane/AHA/provider-terms review, not performed here), 9 `RELEASE_DERIVED_ONLY` (already resolved — public aggregate substitutes already ship), 1 `RELEASE_RECONSTRUCTION_SCRIPT_ONLY` (author a new synthetic example rather than clear the real one). No legal conclusion stated anywhere; "requires redistribution-rights review" language used throughout, never "illegal to publish."

## 2. Restricted-artifact substitute plan

`docs/restricted_artifact_substitutes.md` (Step 2): per-group table of what's already public today (hashes, schemas, aggregate statistics, construction code) vs. what a future substitute could add (case-ID-only cohort manifest, decision/confidence-only per-row tables, a genuinely new synthetic example). No transformation or redaction of restricted content proposed anywhere.

## 3. License options prepared

`docs/license_options.md` (Step 3): MIT / Apache-2.0 / BSD-3-Clause compared on permissiveness, patent terms, attribution, research-code suitability, and (critically) non-coverage of the `LICENSE_REVIEW` data. **No license selected.** Recommends the `LICENSE` / `DATA_AND_ARTIFACT_RIGHTS.md` / `THIRD_PARTY_NOTICES.md` structural split (Step 12).

## 4. Proposed v1 public scope

`docs/public_v1_scope.md`/`.csv` (Step 4): of 338 public-eligible files (`PUBLIC_CORE`+`PUBLIC_OPTIONAL`), 195 `V1_CORE`, 43 `V1_SUPPORTING`, 100 `DEFER_FROM_V1` (redundant reproduction-run duplicates, stale operational logs, dev/smoke-only output, superseded latent-v1 code, internal migration bookkeeping, not-yet-implemented placeholders). Nothing deleted from the archive either way.

## 5. V1 preview validation

`scripts/build_public_release.py --v1-core` → `dist/public_v1_preview/`: **238 files, 0 hash mismatches.** Validated from a copy placed **outside** this repository (`scripts/validate_public_release.py` → PASS, 0 problems; `pytest -m public` → 16 passed). See §14 for exact commands/exit codes.

## 6. GitHub metadata draft

`docs/github_release_metadata.md` (Step 6): repo name, one-line description, 8 topics, About/social-preview text, `main` default branch, Issues enabled / Discussions disabled at launch, visibility recommended private until the checklist (§12) clears. Nothing applied to any actual GitHub repo (none exists — this is still not a git repository).

## 7. Release/tag strategy

`docs/release_strategy.md` (Step 7): `v1.0.0`, `genai4health-2026-camera-ready`, `agenticls-2026-camera-ready`, all sharing one repo history (not separate per-paper repos), plus a documented-but-not-proposed-now `gpt-oss-persistent-extension-v1`. No tag created.

## 8. Archival/Zenodo plan

`docs/archival_plan.md` (Step 8): GitHub release → Zenodo → DOI flow; concept DOI + per-tag version DOIs recommended; restricted artifacts never included in any archival asset regardless of legal resolution; `CITATION.cff` ↔ Zenodo metadata relationship explained. No upload made, no DOI invented.

## 9. Camera-ready ingestion tooling status

`scripts/ingest_camera_ready.py` (Step 9): dry-run by default, requires explicit `--apply` to write anything, refuses to overwrite an existing ingested PDF without `--force`, never parses/extracts bibliographic metadata from the PDF itself. **Tested this phase** with a synthetic placeholder PDF: dry-run printed the correct plan and wrote nothing; missing-file case correctly failed with exit 1. No real camera-ready PDF exists yet, so nothing was ingested.

## 10. Camera-ready provenance-mapping tooling status

`docs/camera_ready_provenance_mapping_template.csv` (Step 10): 122 rows (one per `docs/result_provenance.csv` result_id), `paper`/`result_id` pre-filled, all other fields `TODO`. `scripts/validate_camera_ready_mapping.py`: **tested this phase** — passes on the all-`TODO` template (122 rows, 0 mapped, 0 problems); correctly fails (exit 1) when given a `result_id` not present in `result_provenance.csv`. No manuscript page/section values filled in (none exist yet).

## 11. Third-party/data-rights notice status

`THIRD_PARTY_NOTICES.md` and `DATA_AND_ARTIFACT_RIGHTS.md` (Step 12): drafted, distinguishing project-authored content, MEDAL-derived, Cochrane-derived, AHA-derived, provider model outputs, and (not-yet-existing) paper PDFs. No ownership/licensing claim stated anywhere; "redistribution status under review" used throughout.

## 12. Final release checklist status

`docs/final_release_checklist.md` (Step 13): **SCIENTIFIC and SECURITY sections fully checked**, independently re-verified in this phase (see §14). **CAMERA READY, LEGAL/LICENSING, GITHUB, and ARCHIVAL sections are explicit pending human/editorial/legal decisions**, each with the specific blocker named.

A real gap was found and fixed while preparing this checklist's SECURITY row: a username/path leak scan (not previously part of `validate_public_release.py`) found that 15 `validation/logs/` and `validation/public_preview_validation/logs/` files — this repository's own Phase 3/4/5 operational session logs, not `historical_package/` content — embedded the local developer's absolute home-directory path, and were classified `PUBLIC_OPTIONAL`. Fixed by: (a) reclassifying those 15 files `ARCHIVAL_ONLY` in `scripts/build_public_release_manifest.py` (they were already `DEFER_FROM_V1` for the v1 scope, so the v1 preview was unaffected by the underlying issue, but the *base* `dist/public_release_preview/` was not), (b) redacting the real username out of three other repo-authored files that quoted it as a documentation example (`docs/public_release_audit.md`, `artifacts/raw/raw_artifact_index.csv`, `docs/source_inventory.csv` — all now say `/Users/<local-username>/`), and (c) adding a permanent local-home-directory-path check to `scripts/validate_public_release.py` step 12, alongside the existing API-key-shaped-secret check. Re-verified clean (0 hits) on both preview builds from isolated copies after the fix — see §14.

## 13. Remaining human decisions

1. Code license selection (MIT/Apache-2.0/BSD-3-Clause/other) — authors.
2. Resolution of the 54 `UNKNOWN`-disposition `LICENSE_REVIEW` files (MEDAL/Cochrane/AHA terms review; Google/Groq provider-output terms review) — authors, likely with legal input.
3. Final camera-ready title/authors/affiliations for both papers — authors.
4. Whether/when to make the repository public, create a GitHub release, and deposit to Zenodo — authors.
5. Whether to author a new synthetic `example_audited_case.jsonl` substitute (low-effort, flagged not done) — authors' preference.

## 14. Remaining blockers before Phase 5B

Per the Final Acceptance Criteria:

- **A (archival still reproduces):** PASS. `python scripts/verify_hashes.py` → `ALL HASHES OK`, exit 0. `python scripts/validate_accepted_papers.py` → `OVERALL: PASS`, exit 0. `python -m pytest -m archive` → 36 passed, exit 0.
- **B (v1 preview independently validates):** PASS. Built fresh (`python scripts/build_public_release.py --v1-core` → 238 files, 0 mismatches), copied to an isolated location outside this repository, then: `python scripts/validate_public_release.py` → `OVERALL: PASS (0 problem(s))`, exit 0; `python -m pytest -m public` → 16 passed, exit 0.
- **C (no restricted artifact exposed):** PASS, re-verified after the §12 fix. `validate_public_release.py` step 6 (no `LICENSE_REVIEW`/`ARCHIVAL_ONLY` present) and the new username/path check in step 12 both report clean on both `dist/public_release_preview/` and `dist/public_v1_preview/` from isolated copies.
- **D (no license selected without author approval):** PASS. `LICENSE-TODO.md` unchanged from Phase 4.1 in substance; `docs/license_options.md` compares without choosing.
- **E (camera-ready infrastructure ready):** PASS. `scripts/ingest_camera_ready.py` and `scripts/validate_camera_ready_mapping.py` both exist, both tested this phase, both correctly dry-run/no-op in the absence of real camera-ready material.
- **F (remaining blockers are explicit human decisions, not hidden engineering problems):** PASS, per §13 and the checklist (§12) — every unchecked box names what's needed and who needs to act.

No `historical_package/` file was modified (`find experiments -path "*historical_package*" -newermt <Phase-3-start> | wc -l` → `0`, re-checked this phase). No scientific result was changed. No LICENSE_REVIEW classification was changed to simplify release (64 before, 64 after this phase — the only manifest-tier changes were operational-log files moving `PUBLIC_OPTIONAL → ARCHIVAL_ONLY`, which affects zero scientific data).

## PHASE 5A STATUS: **PASS WITH HUMAN DECISIONS PENDING**

Every engineering/tooling deliverable in Steps 1–13 was built and verified working. Nothing was published. Every remaining gap before an actual public release is a named human decision (§13) or an action this repository's tooling cannot itself perform (creating a real GitHub repo, a Zenodo deposit, or a final manuscript) — not a hidden defect.
