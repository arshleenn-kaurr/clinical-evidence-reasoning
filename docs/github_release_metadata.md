# GitHub repository metadata draft

Draft only (updated Phase 5B with verified AgenticLS camera-ready metadata). No GitHub setting is changed by this document; nothing here has been applied, no repository exists, and no URL is invented.

## Repository name

`clinical-evidence-reasoning`

## One-sentence description (About field)

> Reproducible benchmarks for how language models reason under conflicting and sequential clinical evidence.

## Suggested topics/tags

A short, non-overstuffed list (GitHub recommends keeping this focused):

- `clinical-ai`
- `llm-evaluation`
- `biomedical-nlp`
- `evidence-synthesis`
- `reproducibility`
- `agentic-ai`
- `healthcare-ai`

Seven topics, final. `language-models` was dropped as redundant with `llm-evaluation`; generic tags (`python`, `research`, `nlp`) would dilute discovery.

## About text (longer form, for the repo's "About" panel if GitHub allows more than one line)

> Archive, reproduction tooling, and provenance documentation for two accepted NeurIPS 2026 workshop papers (GenAI4Health, AgenticLS) studying categorical and confidence stability in LLM clinical-evidence reasoning, under static conflicting evidence and under persistent multi-turn context. Every accepted-paper analysis reproduces from archived model outputs with no new API calls (`python scripts/validate_accepted_papers.py`); a separate public-only validation path (`python scripts/validate_public_release.py`) checks the release itself without requiring restricted inputs. AgenticLS camera-ready is ingested and its numbers audited; GenAI4Health camera-ready is pending. See `docs/limitations.md` for known provenance limitations.

## Social-preview description (short, for link-unfurl cards — keep well under 300 characters)

> Reproducible LLM clinical-evidence-reasoning research: two NeurIPS 2026 workshop papers, archived model outputs, no-API-call analysis reproduction, and a public/archival validation split.

## Recommended default branch

`main`. No rationale beyond current convention; nothing in the recovered material specifies otherwise, and this repo is not yet a git repository, so no branch exists to rename.

## Discussions

**Recommend: disabled at launch.** This is a reproducibility archive with a defined validation surface (`scripts/validate_*`), not an ongoing community project at this stage; Issues (below) already covers bug reports and questions about reproduction. Can be enabled later if public interest warrants a discussion space, e.g. around the camera-ready release.

## Issues

**Recommend: enabled.** Useful for reproduction-blocking bug reports (e.g. "`validate_public_release.py` fails on Windows") and licensing-decision follow-up once authors act on `docs/licensing_decision_matrix.md`. Low-maintenance to leave on even if traffic is low.

## Releases

**Recommend: used, but not yet created in this phase** (see `docs/release_strategy.md` for the proposed tag structure; this phase explicitly does not create any tag or release).

## Suggested repository visibility at launch

**Recommend: private until the remaining blockers in `docs/final_release_checklist.md` are resolved**, specifically: license selection, the 64 `LICENSE_REVIEW` files' disposition, and camera-ready PDFs. Making the repository public is itself the publication act this phase's rules explicitly prohibit performing; this is noted here as the eventual target state, not something to do now.

## Phase 5B final fields (verified metadata only)

| Field | Value |
|---|---|
| Repository name | `clinical-evidence-reasoning` |
| Description | as above ("About field") |
| Topics | the 7 listed above |
| Release title (proposed) | `v1.0.0 — Reproducibility release: clinical evidence reasoning under conflicting and persistent context` |
| Release notes | draft in [`github_v1_release_notes.md`](github_v1_release_notes.md) |
| Repository URL / DOI / release date | **none** — omitted until they exist |
| License | **MIT** (code only; `LICENSE`). Data, provider outputs, LICENSE_REVIEW artifacts and PDFs are not covered. |
| Visibility at creation | private (recommended; making it public is a separate, explicit authorization) |

### README paper citations (verified fields only)

- **AgenticLS** — Manav Vohra and Arshleen Kaur. *Stable Decisions Can Hide Evidence Sensitivity in Life-Science Evidence Synthesis.* AgenticLS: Life-Science Agents Workshop, NeurIPS 2026. (No DOI/pages/proceedings printed in the PDF.)
- **GenAI4Health** — final citation pending the camera-ready PDF (submission title: *Evidence Is Not a Vote: Categorical Stability and Confidence Sensitivity Under Conflicting Clinical Evidence*; authors/workshop wording unverified).

Canonical camera-ready filename (written by `scripts/ingest_camera_ready.py`): `papers/<paper>/paper/<paper>-camera-ready.pdf`.
