# v1.0.0 release notes (DRAFT — not published; no GitHub release exists)

> Draft text for a future GitHub release. Nothing here has been published. Placeholders in `TODO` are deliberate: no repository URL, DOI, release date or license has been selected or invented.

## What this release contains

A reproducible research archive and tooling for one research program — *clinical evidence reasoning under conflicting and persistent context* — supporting two NeurIPS 2026 workshop papers. It contains frozen runners and analysis code, reported analysis outputs, experiment/provenance manifests, a 122-row result-provenance table, reproduction and validation tooling, tests, and CI. It deliberately **excludes** raw source-derived data, frozen cohorts/prompts, provider model outputs and the paper PDFs (see "Restricted artifacts").

## Accepted papers

- **AgenticLS** — Manav Vohra, Arshleen Kaur. *Stable Decisions Can Hide Evidence Sensitivity in Life-Science Evidence Synthesis.* AgenticLS: Life-Science Agents Workshop, NeurIPS 2026. Camera-ready ingested and number-audited (`papers/agenticls/`).
- **GenAI4Health** — *Evidence Is Not a Vote: …* NeurIPS 2026 workshop paper. **Camera-ready pending**; this section is completed once its PDF is ingested.

## Reproducibility

Three levels (`docs/reproducibility_levels.md`):
1. **Public artifact validation** — `python scripts/validate_public_release.py` and `python -m pytest -m public` (no restricted inputs, no network, no API keys).
2. **Full archival analysis reproduction** — `python scripts/validate_accepted_papers.py`; every accepted-paper analysis is regenerated from archived model outputs and compared to the archived results (byte-identical under the pinned environment: Python 3.12, SciPy 1.16.3). Requires the withheld inputs, so it runs only on the full archive.
3. **Model re-execution** — not required, not performed; no model API is called anywhere in this repository's tooling.

Manuscript-number audit (`docs/camera_ready_number_audit.md`): every reported AgenticLS result value matches the archived artifacts; two wording corrections (bootstrap-resample count; a count of anchors whose estimate favors the intervention) were identified, corrected by the authors, and the revised PDF re-ingested; see `docs/camera_ready_approved_revisions.md`. The AgenticLS audit status is PASS.

## Public vs. archival scope

The public release is the `V1_CORE` + `V1_SUPPORTING` set (`docs/public_v1_scope.md`). Everything else is retained in the archive, not deleted.

## Known provenance limitation

The archived post-hoc analysis manifest records an earlier script hash that is no longer available. The recovered script differs from that recorded hash but regenerates all archived post-hoc outputs byte-for-byte under the verified reproduction environment (SciPy 1.16.3). The historical code change cannot be reconstructed and is retained as a provenance limitation.

Other documented limitations: latent-v1 is superseded and excluded from every reported analysis; the Groq GPT-OSS **persistent-context** extension is a separate, in-progress, non-canonicalized cross-model extension and is not part of either accepted paper (the *static* GPT-OSS-120B sensitivity runs reported in the papers are included).

## Restricted artifacts not included

64 files (frozen cohorts, generated prompts, raw/canonical provider outputs, candidate-audit CSVs, raw source datasets) are withheld pending redistribution-rights review (MEDAL / Cochrane / AHA / provider terms); camera-ready PDFs are withheld pending author/workshop permission. Details: `docs/v1_withheld_artifacts.md`, `DATA_AND_ARTIFACT_RIGHTS.md`, `THIRD_PARTY_NOTICES.md`.

## License

**TODO — no code license has been selected.** A code license, once chosen, will not cover the withheld data or provider outputs.

## Validation status (local, pre-publication)

See `docs/phase5b_finalization_report.md` for the exact commands, results and remaining blockers. CI has **not** been run on a GitHub runner (no repository exists); local pre-flight is in `docs/github_actions_preflight.md`.

## Citation

See `CITATION.cff` (no DOI, repository URL or release date yet).
