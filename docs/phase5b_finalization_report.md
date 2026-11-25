# Phase 5B finalization report

Date: 2026-10-04. Scope: finalize the accepted-paper release locally. **Nothing was committed, pushed, published, tagged, uploaded or made public; no repository, release, tag, Zenodo deposit or DOI exists; no license was selected.** `historical_package/`, raw/canonical outputs, endpoint definitions and archived analysis values were not changed; no model API was called.

## PHASE 5B STATUS: **READY EXCEPT FOR NAMED HUMAN DECISIONS (AgenticLS)**; GenAI4Health WAITING; overall release: **code license since decided (MIT, post-Phase-5B); remaining items are human release decisions**

Per-paper: **AgenticLS — number audit PASS** on the revised camera-ready (re-ingested after the authors corrected the bootstrap-resample statement and the Appendix B count); remaining AgenticLS items are human decisions only (code license, PDF redistribution permission, rights review, publication authorization). **GenAI4Health — WAITING FOR CAMERA-READY PDF.** No MISMATCH remains; one claim is NOT_MACHINE_CHECKABLE with recorded manual verification (anchor-estimate direction). Nothing was committed, pushed, published, tagged or uploaded; no license selected; `historical_package/` and all result values untouched.

## 1–2. Camera-ready PDFs ingested; hashes; final titles/authors/affiliations

| | AgenticLS | GenAI4Health |
|---|---|---|
| Ingested | **Yes, revised version** — `papers/agenticls/paper/agenticls-camera-ready.pdf` (dry-run first, then `--force`; identity verified from first-page text; the earlier PDF `30e8f4e65cd3a095c787f34caa3bc24963ba9413c6d0524a59b69a60d181285e` is superseded provenance only, not current, not retained) | **No** — the only PDF supplied is the anonymized submission ("Anonymous Author(s)", "Do not distribute"); intentionally not ingested |
| SHA256 | `1b7311a7f7c563b50dbbd10c59d665b87881b8a3e9c2058c60ff28bcb72758e5` (273,564 B; matches source) | — |
| Title | Stable Decisions Can Hide Evidence Sensitivity in Life-Science Evidence Synthesis | — (submission title unverified) |
| Authors / affiliations (as printed) | Manav Vohra; Arshleen Kaur — Independent Researcher; Ernest Mario School of Pharmacy; Rutgers University | — |
| Workshop / year | AgenticLS: Life-Science Agents Workshop, NeurIPS 2026 | — |

Source path, destination, SHA256 and UTC timestamp are in `papers/agenticls/paper/metadata.json` (source path redacted to `~/Downloads/…`) and, with the full local path, in the non-public `validation/logs/camera_ready_ingestion_agenticls.json`. Details: `docs/final_paper_metadata.md`. The earlier `AgenticLS.pdf` draft (different emails/affiliations) was not used. The PDF was treated as immutable (SHA256 re-verified by the audit tool on every run).

## 3–4. READMEs and CITATION.cff

AgenticLS READMEs → CAMERA-READY INGESTED / VERIFIED (title, authors, venue, SHA256, relationship to experiments, commands, mapping status). GenAI4Health stays CAMERA-READY PENDING. `CITATION.cff`: AgenticLS reference + repo authors from verified metadata; GenAI4Health reference still `TODO`; `version`, `date-released`, `repository-code`, `url`, `doi` deliberately omitted. YAML parses; required keys present (also checked by `validate_public_release.py` step 10).

## 5. Provenance mapping

`docs/camera_ready_provenance_mapping.csv`: 158 rows — AgenticLS 48 MAPPED + 2 NOT_CITED; GenAI4Health 108 PENDING_CAMERA_READY. Results shared across the two papers (e.g. `g4h.replication.*` cited in AgenticLS) carry `SHARED_RESULT`. **37 AgenticLS claims have no `result_id`** (design counts, execution counts, hashes, seeds, and the anchor-order confidence contrast): documented as UNMAPPED CLAIM in `docs/camera_ready_unmapped_claims.csv`, each verified read-only against canonical data/manifests (no new provenance rows were created; creating some is recommended, esp. for the order contrast, which has **no archived output** but reproduces exactly: +1.20, [0.76, 1.64], via the archived bootstrap routine/seed). `scripts/validate_camera_ready_mapping.py` now validates the populated mapping by default (`--template` for the template): **VALID**.

## 6. Manuscript number audit (AgenticLS) — `docs/camera_ready_number_audit.md`

`python scripts/audit_camera_ready_numbers.py` (needs `pypdf`, see `requirements-camera-ready-audit.txt`): **160 claims on the revised PDF: EXACT_MATCH 67, ROUNDING_MATCH 57, TEXTUAL_CLAIM_VERIFIED 35, NOT_MACHINE_CHECKABLE 1 (manually verified), MISMATCH 0 — status PASS.** (On the first ingested PDF: MISMATCH 1 + one unverified item, both since resolved, below.)

1. *(resolved)* **`agl.method.boot_p260` — was MISMATCH (methods statement, not a result value).** Methods and App. D.4 say "Paired confidence intervals used 10,000 case-level bootstrap resamples." The persistent-260 terminal CI (headline −12.32, [−13.02, −11.62]) was produced with **100,000** resamples (`analyze_sequential_gemini.py`, `B=100000`; also stated in `result_provenance.csv`). The printed interval values themselves reproduce exactly. All other intervals used 10,000. Originally flagged for an author decision. **Resolved in revised camera-ready PDF.**
2. *(resolved)* **`agl.anchor.five` — was NOT_MACHINE_CHECKABLE, manual verification incomplete.** "In five primary cases, the displayed point estimate favored the intervention…": exactly five do_not_support primary anchors have an estimate and no interval (count verified); direction verified for 4/5 from the question wording; for **C0006** ("improved survival to hospital discharge", RR 0.58) the outcome direction is not recorded in any artifact, so favorability cannot be confirmed. **Resolved by author verification and revised camera-ready PDF** (four anchors, C0006 excluded).

Non-blocking notes (in the audit and `docs/camera_ready_claim_scope_audit.md`): the printed H→H+L4 CIs match the *post-hoc* bootstrap of that contrast, while the archived *prespecified* `confidence_shift.csv` differs at the 2nd decimal of one bound (same for the primary and GPT-OSS rows); several appendix values sit exactly on a rounding half-unit (flagged in the audit detail). 59 numeric tokens not covered by a claim (+107 exact repeats of verified strings) are listed in the audit; reviewed by the verifier in this phase: they are model names, section/page numbers, axis ticks, CI-level "95%", and the temperature/scale definitions, not unverified results.

### Resolution — both items fixed by the authors and re-ingested

The authors corrected (1) Methods and Appendix D.4 (10,000 resamples, except the persistent-vs-fresh terminal comparison, 100,000) and (2) Appendix B (four, not five, anchors with an estimate but no interval favoring the intervention; C0006, survival to discharge, RR 0.58 [0.12–2.74], does not). The revised PDF was re-ingested; the audit confirms the bootstrap sentence appears in both places (`agl.method.boot_resamples`) and the count reads four (`agl.anchor.four`, manual verification recorded: five candidates, C0006 excluded by the author-supplied external verification, other four favor the intervention by outcome wording). A word-level diff of the old and new PDFs shows only these two edits (plus reflow). Record: `docs/camera_ready_approved_revisions.md`.

## 7–8. Claim-scope audit; post-hoc disclosure

`docs/camera_ready_claim_scope_audit.md`: no wording violating a documented scope limit (calibration, causal evidence use, arrival-only isolation, autonomous appraisal, veto-set safety, Groq persistent extension, latent-v1, restricted-data availability are all disclaimed or absent); one low-severity observation ("depending on how that evidence accumulated"). The paper contains no reproducibility/code-availability statement, so nothing conflicts with the approved post-hoc script-hash disclosure, which is present verbatim in `README.md` and `docs/posthoc_hash_investigation.md` (and in expanded form in `docs/limitations.md`). Not inserted into the paper. `posthoc_hash_investigation.md` unchanged.

## 9. Public v1 scope and preview

Manifest: 481 files — PUBLIC_CORE 181, PUBLIC_OPTIONAL 177, **LICENSE_REVIEW 64 (unchanged)**, ARCHIVAL_ONLY 55 (+1: the ingestion log), SCRATCH_IGNORE 3, **PUBLIC_RELEASE_PENDING_PERMISSION 1** (new tier; the PDF). Scope: V1_CORE 215 / V1_SUPPORTING 43 / DEFER 100. `dist/public_v1_preview/`: 258 files + `MANIFEST.csv` and `PREVIEW_ONLY.txt`, 0 hash mismatches, no PDF. Validated from an isolated copy outside the repository: `validate_public_release.py` → **OVERALL: PASS (0 problems)**; `pytest -m public` → **17 passed**.

## 10–11. Code license; third-party/rights

*(At the time of Phase 5B: blocked on the code license; superseded — the authors selected MIT afterwards, see `docs/pre_github_readiness_report.md` and `docs/license_options.md`.)* `THIRD_PARTY_NOTICES.md` / `DATA_AND_ARTIFACT_RIGHTS.md` updated only with the factual PDF status. No UNKNOWN status was converted to approval; `docs/v1_withheld_artifacts.md` lists exactly what is withheld and why (64 LICENSE_REVIEW by family, 55 ARCHIVAL_ONLY, 1 PDF, 100 deferred).

## 12–16. GitHub metadata, release notes, tag freeze, git plan, CI preflight, Zenodo

- `docs/github_release_metadata.md` updated; `docs/github_v1_release_notes.md` drafted (no URL/DOI/date/license).
- `docs/tag_freeze_manifest.json` (built by `scripts/build_tag_freeze_manifest.py`, `--check` verifies): `agenticls-2026-camera-ready` inputs frozen locally but HELD; `genai4health-2026-camera-ready` WAITING; `v1.0.0` BLOCKED. Commit hashes `null`. No tag created.
- `docs/git_initialization_plan.md`: the archive is not a git repo; plan initializes from the validated public tree only, manifest-driven staging, never `git add .`. Not run.
- `docs/github_actions_preflight.md`: **two real CI defects found and fixed** — (a) `.venv` inside the checkout broke `public-integrity` (6,332 spurious failures); (b) the archive job's `pytest tests/` would fail on a full-archive checkout, now `pytest -m archive`. After the fixes: public job PASS on an isolated copy with an in-tree `.venv`; archive job skips cleanly when the marker file is absent. Not run on GitHub.
- `docs/zenodo_metadata_draft.json`: verified metadata only; no DOI, date, URL, license or access_right. Not uploaded.

## 17. Final checklist

`docs/final_release_checklist.md` updated; only items actually completed are checked (CI run, release, tags, Zenodo, DOI remain unchecked).

## 18. Final local audit (commands and results)

| Check | Result |
|---|---|
| `python scripts/verify_hashes.py` | ALL HASHES OK |
| `python scripts/validate_accepted_papers.py` | OVERALL: PASS |
| `python -m pytest -m archive` | 36 passed |
| v1 preview rebuilt, copied outside the repo: `validate_public_release.py` | OVERALL: PASS (0 problems) — includes manifest verification, secret scan, local-path scan, 64-link scan, unmanifested-file check |
| `python -m pytest -m public` (isolated copy) | 17 passed |
| `python scripts/validate_camera_ready_mapping.py` | VALID (158 rows) |
| `python scripts/audit_camera_ready_numbers.py` | **PASS** — AgenticLS: 0 MISMATCH, 1 NOT_MACHINE_CHECKABLE with recorded manual verification; GenAI4Health PENDING (exit 0) |
| `python scripts/build_tag_freeze_manifest.py --check` | all frozen hashes verified |
| No restricted artifact in preview | PASS (validator step 6: no LICENSE_REVIEW / ARCHIVAL_ONLY / PENDING_PERMISSION file present) |
| `historical_package/` untouched | `verify_hashes.py` OK; no file there modified during Phase 5B (`DRY_RUN_RESUME_20261004.txt`, mtime 02:52, is byte-identical to its original and pre-dates this phase) |
| Phase-5B-created stray files | root and `papers/agenticls/` `.DS_Store` (Finder metadata) deleted |

## Remaining blockers (all human actions)

1. ~~Code-license selection~~ — done after Phase 5B: MIT (`LICENSE`).
2. GenAI4Health final camera-ready PDF → ingest, claim table, audit, mapping.
3. Permission to redistribute the PDF(s) (currently excluded from public builds).
4. Rights review of the 54 UNKNOWN files (MEDAL/Cochrane/AHA/provider terms).
5. Author confirmation that author emails (`metadata.json`) and short quoted fragments (audit) may appear publicly; confirm repo-level author list in `CITATION.cff`.
6. Separate authorization for git init, repository creation, tagging, push, release, Zenodo.

## Exact commands for the future publication step (NOT run; each needs explicit authorization)

```bash
# (a) after items 1–7: regenerate + validate the public tree
python scripts/build_public_release_manifest.py && python scripts/build_public_v1_scope.py && python scripts/build_public_release.py --v1-core
# (b) local git init from the clean public tree: follow docs/git_initialization_plan.md steps 2–5 verbatim (never `git add .`)
# (c) tags, only after the commit exists and docs/tag_freeze_manifest.json --check passes:
git tag -a agenticls-2026-camera-ready -m "AgenticLS camera-ready" ; git tag -a v1.0.0 -m "v1.0.0"   # genai4health tag only after its PDF is ingested
# (d) remote + push (repository URL supplied by the authors; create the repo PRIVATE first):
git remote add origin <URL-SUPPLIED-BY-AUTHORS> && git push -u origin main && git push origin --tags
# (e) run the real CI (push triggers it) and confirm both jobs; then, if authorized:
#     create the GitHub release from docs/github_v1_release_notes.md, enable the Zenodo integration,
#     deposit using docs/zenodo_metadata_draft.json, then add the DOI/URL/date-released to CITATION.cff in a follow-up commit.
```
