# Final release checklist

Checkbox status reflects this repository's state as of Phase 5B (2026-10-04). Per-paper: AgenticLS camera-ready ingested; GenAI4Health camera-ready pending. `[x]` = verified/done; `[ ]` = pending, with who/what is needed.

## SCIENTIFIC

- [x] Archival reproduction passes — `python scripts/validate_accepted_papers.py` → PASS; `python -m pytest -m archive` → 36 passed.
- [x] Public validation passes — `python scripts/validate_public_release.py` → PASS, 0 problems (run from an isolated copy outside the repo); `python -m pytest -m public` → 16 passed.
- [x] Result provenance passes — `python scripts/validate_result_provenance.py` → VALID, 122/122 unique `result_id`s, all referenced paths resolve.

## CAMERA READY

- [x] Final title — AgenticLS (printed in the ingested PDF; `papers/agenticls/paper/metadata.json`).
- [ ] Final title — GenAI4Health — **waiting for the camera-ready PDF** (only the anonymized submission exists; not ingested).
- [x] Final authors — AgenticLS: Manav Vohra; Arshleen Kaur (as printed). `CITATION.cff` populated from this.
- [ ] Final authors — GenAI4Health — waiting for the PDF (`CITATION.cff` keeps `TODO` for that reference only).
- [x] Final affiliations — AgenticLS (as printed: Independent Researcher / Ernest Mario School of Pharmacy / Rutgers University).
- [ ] Final affiliations — GenAI4Health — waiting.
- [x] PDF added — AgenticLS (`agenticls-camera-ready.pdf`; local only, not for public release).
- [ ] PDF added — GenAI4Health — waiting.
- [x] PDF SHA256 recorded — AgenticLS `1b7311a7f7c563b50dbbd10c59d665b87881b8a3e9c2058c60ff28bcb72758e5`.
- [ ] PDF SHA256 recorded — GenAI4Health — waiting.
- [x] Result IDs mapped to paper — AgenticLS (`docs/camera_ready_provenance_mapping.csv`: 48 MAPPED, 2 NOT_CITED; validator passes; 37 claims without a `result_id` documented in `docs/camera_ready_unmapped_claims.csv`). GenAI4Health rows are `PENDING_CAMERA_READY`.
- [x] All manuscript numbers checked — AgenticLS: **audit status PASS** on the revised, re-ingested PDF (160 claims; the bootstrap-statement and five→four corrections are applied and verified: `docs/camera_ready_approved_revisions.md`). One claim is NOT_MACHINE_CHECKABLE with recorded manual verification (anchor-estimate direction, `agl.anchor.four`). GenAI4Health: not started.
- [x] Claim-scope audit — AgenticLS (`docs/camera_ready_claim_scope_audit.md`): no scope violations; one low-severity wording note.

## LEGAL / LICENSING

- [x] Code license selected — MIT (authors' decision, 2026-10-04); `docs/license_options.md`.
- [x] LICENSE file finalized — standard MIT text, `LICENSE` (replaced `LICENSE-TODO.md`); scope (code only) stated in README, `DATA_AND_ARTIFACT_RIGHTS.md`, `THIRD_PARTY_NOTICES.md`.
- [ ] Third-party notices reviewed — drafts updated with the PDF-permission status in Phase 5B; still need author review/finalization. No UNKNOWN status was converted into approval; withheld set documented in `docs/v1_withheld_artifacts.md`.
- [ ] 64 `LICENSE_REVIEW` files resolved — audited and grouped into 7 artifact-type families (`docs/licensing_decision_matrix.md`/`.csv`); all still `UNKNOWN` except 9 files already resolved `RELEASE_DERIVED_ONLY` (public aggregate substitute already shipped) and 1 `RELEASE_RECONSTRUCTION_SCRIPT_ONLY`. 54 files require an actual MEDAL/Cochrane/AHA/provider-terms review that has not happened.
- [ ] Provider-output redistribution decision — Google (Gemini) and Groq terms-of-service review, not performed.

## GITHUB

- [ ] Actual CI run passes — NOT done. Local pre-flight of both jobs' exact commands is in `docs/github_actions_preflight.md`; it has **not** run on a GitHub Actions runner (no git repository exists).
- [ ] Repository metadata set — final draft (`docs/github_release_metadata.md`) updated with verified AgenticLS metadata; not applied to any GitHub repo.
- [ ] Topics set — 7 topics drafted in `docs/github_release_metadata.md`, not applied.
- [ ] Default branch confirmed — `main` recommended in `docs/github_release_metadata.md`; moot until a git repository exists.
- [ ] Release tag created — NOT done. Plan + freeze manifest drafted (`docs/release_strategy.md`, `docs/tag_freeze_manifest.json`); no tag, no git repo. Local git-init plan: `docs/git_initialization_plan.md` (not executed).
- [ ] Release notes reviewed — draft written (`docs/github_v1_release_notes.md`); authors have not reviewed it.

## ARCHIVAL

- [ ] Zenodo decision — plan (`docs/archival_plan.md`) and metadata draft (`docs/zenodo_metadata_draft.json`; no DOI/date/license/URL) prepared; nothing uploaded; authors have not decided.
- [ ] DOI added if created — not applicable yet; no DOI exists, none invented anywhere in this repository.
- [ ] CITATION.cff finalized — AgenticLS reference and repo authors populated from the verified PDF; GenAI4Health reference still `TODO` (pending PDF); `version`/`date-released`/`repository-code`/`doi` omitted by design until they exist.

## SECURITY

- [x] Secret scan — `scripts/validate_public_release.py` step 12 (API-key-shaped string regex) passes on both the full repo and every preview build; re-run this phase, 0 hits.
- [x] Local usernames removed from public release — files containing a local username (`nohup.out`, operational logs incl. the Phase 5B ingestion log) are `ARCHIVAL_ONLY` and excluded by construction; the public `metadata.json` carries a redacted `~/Downloads/...` source path; verified absent from the preview builds (see `docs/phase5b_finalization_report.md`).
- [x] Absolute paths removed — same mechanism; `scripts/validate_public_release.py` step 13 (unmanifested-file check) additionally catches anything that shouldn't be there.
- [x] No unpublished/private artifacts included — `scripts/validate_public_release.py` step 6 confirms, from an isolated copy outside the repo, that no `LICENSE_REVIEW`/`ARCHIVAL_ONLY` file is present in either preview build.

## Overall (Phase 5B)

Scientific and security items remain verified (re-run in `docs/phase5b_finalization_report.md`). The code license has since been selected (MIT) and the AgenticLS number audit now PASSES; GenAI4Health is waiting on its camera-ready PDF. No commit, tag, repository, release, Zenodo deposit or DOI exists.
