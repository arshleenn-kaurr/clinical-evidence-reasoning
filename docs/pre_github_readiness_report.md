# Pre-GitHub readiness report

Date: 2026-10-04. Scope: repository finalization and private-GitHub preparation only. **Nothing was committed, pushed, tagged, released, uploaded or made public; no git repository, GitHub repository, remote, tag, release, Zenodo deposit or DOI exists; no license was selected and no `LICENSE` file was created.** `historical_package/`, raw/canonical outputs, the AgenticLS PDF and all GenAI4Health camera-ready work are untouched; no model API was called.

## PRE-GITHUB STATUS: **READY FOR FIRST LOCAL COMMIT FROM THE CLEAN PUBLIC TREE** (post-decision update below); commit name/email still to be supplied

### Update after author decisions (2026-10-04)
- **License:** MIT selected; standard `LICENSE` (Copyright (c) 2026 Manav Vohra and Arshleen Kaur) replaces `LICENSE-TODO.md`; scope (code only; no rights to MEDAL/Cochrane/AHA-derived material, provider outputs, LICENSE_REVIEW artifacts, or camera-ready PDFs unless separately permitted) stated in `README.md`, `DATA_AND_ARTIFACT_RIGHTS.md`, `THIRD_PARTY_NOTICES.md`. No LICENSE_REVIEW status changed. `CITATION.cff` records `license: MIT`.
- **Authors:** Manav Vohra, Arshleen Kaur; affiliation Independent Researcher; Ernest Mario School of Pharmacy; Rutgers University. No ORCIDs.
- **Emails:** removed from `papers/agenticls/paper/metadata.json` and `docs/final_paper_metadata.md`; `docs/public_identity_review.md` marked resolved.
- **Commit identity:** placeholders `<AUTHOR NAME>` and `<PUBLISHABLE GIT EMAIL>` remain (GitHub no-reply recommended, none invented).
- **Versioning:** private repo first; no `v1.0.0`, paper tags, GitHub Release or Zenodo until GenAI4Health camera-ready is complete (unless the authors decide otherwise).
- **Git plan:** step 1 reduced to the minimum deterministic order (manifest → scope → manifest → build → `--check`).


## 1. Phase 5B report consistency
Fixed in `docs/phase5b_finalization_report.md`: the stale "exit 1 — AgenticLS BLOCKED" audit row now reads PASS (0 MISMATCH, 1 NOT_MACHINE_CHECKABLE with recorded manual verification; GenAI4Health PENDING); the two historical issues keep their original explanation and now end "Resolved in revised camera-ready PDF." / "Resolved by author verification and revised camera-ready PDF." A full re-read found no other sentence describing AgenticLS as scientifically blocked.

## 2. AgenticLS number audit
**PASS**: 160 claims — EXACT_MATCH 67, ROUNDING_MATCH 57, TEXTUAL_CLAIM_VERIFIED 35, NOT_MACHINE_CHECKABLE 1 (manually verified, note recorded: `agl.anchor.four`), **MISMATCH 0**. Mapping validator: VALID (158 rows; 48 mapped, 2 not cited, 108 GenAI4Health pending). Caveat to keep visible: the one manually verified claim relies on the authors' external confirmation that C0006's direction does not favor the intervention.

## 3. Current AgenticLS PDF hash
`1b7311a7f7c563b50dbbd10c59d665b87881b8a3e9c2058c60ff28bcb72758e5` (re-checked this phase; file untouched). The tag-freeze manifest references this hash; `30e8f4e6…` appears only as superseded.

## 4. Public v1 build
Manifest 484 files: PUBLIC_CORE 184, PUBLIC_OPTIONAL 177, LICENSE_REVIEW 64 (unchanged), ARCHIVAL_ONLY 55, SCRATCH_IGNORE 3 (after removing two stray Finder `.DS_Store` files), PUBLIC_RELEASE_PENDING_PERMISSION 1. v1 scope: V1_CORE 218 / V1_SUPPORTING 43 / DEFER 100. `dist/public_v1_preview/`: 261 files + `MANIFEST.csv` + `PREVIEW_ONLY.txt`, 0 hash mismatches, PDF excluded. ()

## 5. Isolated public validation
Clean copy of `dist/public_v1_preview/` outside the archive (without `PREVIEW_ONLY.txt`, fresh Python 3.12 venv with the pinned lock file): `validate_public_release.py` → **OVERALL: PASS (0 problems)**; `pytest -m public` → **17 passed**; every `MANIFEST.csv` entry (261) present and hash-matched, no unmanifested file on disk; 0 restricted-artifact leakage (no LICENSE_REVIEW / ARCHIVAL_ONLY / PDF-pending-permission file; no `.jsonl` cohort/raw files); 0 secret hits; 0 local-path leaks (the only `/Users/` strings are the redacted `/Users/<local-username>/` documentation examples); AgenticLS camera-ready PDF absent. Only PDFs present: the two Figure 1 PDFs.

## 6. License decision
*(Superseded: MIT was selected; see the update above.)* The advisory in `docs/license_options.md` preferred MIT.

## 7. Git initialization readiness
`docs/git_initialization_plan.md` rewritten: initialization only from a clean copy of `dist/public_v1_preview/` outside the archive; seven explicit steps (rebuild, clean copy, isolated validation, `git init -b main`, manifest-driven staging, `git status` review, first commit "Initial reproducibility release"); never `git add .`. Not executed. The copy, validation and staging logic was exercised without git (see section 5); that dry run found and fixed one real bug in the plan (the staging snippet read a non-existent `repo_path` column; `MANIFEST.csv` uses `public_path`).

## 8. Private GitHub setup readiness
`docs/private_github_setup.md` written: create private `clinical-evidence-reasoning` (default `main`), add remote `<GITHUB_REPO_URL>`, push `main` only, watch real Actions (public-integrity passes; archive job skips cleanly without restricted inputs), review the private repo, then stop. Not executed; no URL invented.

## 9. GitHub metadata readiness
`docs/github_release_metadata.md` finalized: description "Reproducible benchmarks for how language models reason under conflicting and sequential clinical evidence."; 7 topics (clinical-ai, llm-evaluation, biomedical-nlp, evidence-synthesis, reproducibility, agentic-ai, healthcare-ai). Not applied anywhere. Root `README.md` revised: first-screen summary, two-paper structure, static vs persistent distinction, AgenticLS status updated (it previously still said camera-ready pending), reproducibility status, where to start; caveats on confidence calibration, dominant-evidence IDs and non-public data retained; Groq persistent extension still labelled as outside both papers.

## 10. Public identity / email
`docs/public_identity_review.md`: authors Manav Vohra and Arshleen Kaur, affiliation as printed, appear in 10 public-tree files (intended identity). The two Rutgers emails appear in exactly two public files (`papers/agenticls/paper/metadata.json`, `docs/final_paper_metadata.md`) — **AUTHOR DECISION REQUIRED**. Local-username occurrences are archival-only. Commit identity for the first commit is also an author decision.

## 11. Restricted artifacts
All 64 LICENSE_REVIEW files (54 still UNKNOWN), 55 ARCHIVAL_ONLY files and the PDF remain excluded from every public build; verified by the validator's leak check. Not resolved in this phase by design; README, `DATA_AND_ARTIFACT_RIGHTS.md` and `THIRD_PARTY_NOTICES.md` state that the repository is publishable without them, that the code license covers code only, and that PDFs are not redistributed.

## 12. GenAI4Health
**WAITING FOR CAMERA-READY PDF.** Only the anonymized submission exists and was not ingested. Its audit, mapping rows, citation and tag remain pending.

## 13. Remaining actions before a private push
1. Choose the code license (then apply it as above and re-validate).
2. Decide on author emails (keep / remove / replace) and confirm the repo-level author list.
3. Supply a publishable commit identity.
4. Review `docs/github_v1_release_notes.md` and the README as an outsider would.
5. Authorize git init, repository creation (private), remote and push, in that order.

## 14. Remaining actions before public launch
1. Real GitHub Actions run passes on the private repo.
2. GenAI4Health camera-ready ingested, audited and mapped (or an explicit decision to launch AgenticLS-only).
3. Decision on PDF redistribution (otherwise PDFs stay out).
4. Decide whether any of the 54 UNKNOWN-rights files or a synthetic substitute will ever be released (not required for v1).
5. Separate authorization to make the repository public, tag (`agenticls-2026-camera-ready`, `v1.0.0`), create the release, and deposit to Zenodo; then add URL/DOI/date to `CITATION.cff` in a follow-up commit.

## Archive-side checks (this phase)
`validate_camera_ready_mapping.py` VALID; `audit_camera_ready_numbers.py` AgenticLS PASS / GenAI4Health PENDING; `validate_accepted_papers.py` OVERALL: PASS; `build_tag_freeze_manifest.py --check` verified; manifests/scope/preview rebuilt in the converging order. No `historical_package/` file was edited.
