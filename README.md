# Clinical Evidence Reasoning

Research archive and reproduction pipeline for two accepted NeurIPS 2026 workshop papers studying how large language models weigh scientific evidence: whether categorical decisions and self-reported confidence hold up under conflicting lower-tier evidence, and whether they shift when that evidence arrives incrementally in a persistent conversation rather than all at once.

## At a glance

- **What it studies:** whether an LLM's categorical clinical decision and its self-reported confidence stay stable when lower-tier evidence conflicts with a high-tier anchor, and whether that changes when evidence arrives one piece at a time in a persistent conversation.
- **Two papers, one program:** *GenAI4Health* (static conflict: all evidence in one prompt) and *AgenticLS* (persistent context: evidence delivered turn by turn, compared with a fresh one-shot presentation of the same cumulative evidence).
- **Paper status:** both accepted at NeurIPS 2026 workshops. AgenticLS camera-ready is ingested and its numbers audited against the archived outputs (no mismatches); GenAI4Health camera-ready is **pending**.
- **Reproducibility:** accepted-paper analyses re-run from archived model outputs with **no API calls**. Some inputs (frozen cohorts, prompts, raw/canonical model outputs; 64 files) are **not** in the public release because their redistribution rights are unresolved, so a public checkout validates release integrity, not the full scientific re-run.
- **Where to start:** [`papers/agenticls/README.md`](papers/agenticls/README.md) or [`papers/genai4health/README.md`](papers/genai4health/README.md); then [Reproducibility](#reproducibility) below and [`docs/limitations.md`](docs/limitations.md).

## Research program

One program, two angles on the same question:

- **Static evidence conflict.** Fix a case and a high-tier anchor (a Cochrane systematic review or AHA guideline recommendation), then add synthetic lower-tier conflicting or aligned evidence cards. Does the model's categorical decision and confidence hold, or does more (weaker) evidence dilute a correct decision? This is `experiments/static_conflict/`.
- **Persistent-context sensitivity.** Deliver that same evidence incrementally, one card per conversational turn, with prior model outputs retained in context, instead of as a single batch prompt. Does the terminal assessment differ from a fresh one-shot presentation of the identical cumulative evidence? This is `experiments/persistent_context/`.

AgenticLS builds directly on the static-conflict benchmark (same cohort, same evidence-card construction, same prompt template) and adds the persistent-context design on top of it.

## Accepted papers

| | Title | Status |
|---|---|---|
| **GenAI4Health** | *Evidence Is Not a Vote: Categorical Stability and Confidence Sensitivity Under Conflicting Clinical Evidence* | Accepted. Final PDF: **CAMERA-READY PENDING** ([papers/genai4health/](papers/genai4health/)) |
| **AgenticLS** | *Stable Decisions Can Hide Evidence Sensitivity in Life-Science Evidence Synthesis* | Accepted (AgenticLS: Life-Science Agents Workshop, NeurIPS 2026). Camera-ready ingested locally and number-audited; the PDF is not redistributed here ([papers/agenticls/](papers/agenticls/)) |

No DOI, arXiv ID, or OpenReview link is recorded anywhere in the recovered material, so none is given here. The paper PDFs are not included in the public release: permission to redistribute them has not been established.

## Main experiments

| Experiment | Model | Cases | Design | Paper |
|---|---|---|---|---|
| Gemini primary | `gemini-3.6-flash` | 40 | H, H_L1, H_L2, H_L4, H_L4_ALIGNED, L4_H | GenAI4Health |
| Gemini replication | `gemini-3.6-flash` | 260 (shared cohort, see below) | same 6 conditions | GenAI4Health |
| Gemini guideline/veto boundary | `gemini-3.6-flash` | 15 (AHA COR III) | same 6 conditions | GenAI4Health |
| GPT-OSS sensitivity (primary + veto) | `openai/gpt-oss-120b` (Groq) | 40 + 15 | same design, second model | GenAI4Health |
| Gemini latent-anchor sensitivity | `gemini-3.6-flash` | 40 | same design, alternate anchor construction | GenAI4Health |
| Gemini persistent 260 | `gemini-3.6-flash` | 260 (same shared cohort) | persistent H→H_L1→H_L2→H_L3→H_L4 + one fresh H_L4 | **AgenticLS** |
| Gemini aligned persistent control | `gemini-3.6-flash` | 40 (10/stratum subset of the 260) | aligned-evidence persistent control, branched from the 260 run's H response | **AgenticLS** |
| Groq GPT-OSS persistent extension | `openai/gpt-oss-120b` (Groq) | 260 (same shared cohort) | batch arm vs. persistent sequential arm | **post-acceptance cross-model extension — not part of either accepted paper, IN PROGRESS / NOT CANONICALIZED** |

The 260-case cohort is byte-identical (sha256 `b3bc2dd1…a818a`) across the static replication, Gemini persistent, and Groq extension copies — one cohort, reused, not three different ones. See `data/frozen/`.

## Reproducibility

This repository has **two explicitly separate reproducibility levels**, because the public release intentionally excludes 64 `LICENSE_REVIEW` files (frozen cohorts, prompts, and raw/canonical model outputs — see `docs/public_dependency_audit.md`). Neither level requires an API call.

### Public artifact validation

Works using **only** the files actually shipped in a public release (`dist/public_release_preview/`, or any checkout built the same way). Does **not** require the restricted cohorts/results and is always runnable from the stripped public artifact.

```bash
uv venv --python 3.12 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements-reproduction.lock.txt
source .venv/bin/activate
python scripts/validate_public_release.py
python -m pytest -m public
```

This checks manifest/hash integrity, repo structure, experiment manifests, the public-safe parts of the result-provenance map, that no restricted file has leaked into the checkout, that the two reconstructed-code artifacts (Figure 1 plotting, the canonical-reference generator) are present and internally consistent — the reconstructed reference generator is actually re-run and compared byte-for-byte against the archive — plus doc-link, `CITATION.cff`, and basic secret checks. As of this writing, run from a copy of the preview placed **outside** this repository (no parent-repo fallback possible): **PASS, 0 problems** (`validation/public_preview_validation/`).

### Full archival reproduction (strongest validation path)

Requires the **complete local archive**, including the `LICENSE_REVIEW` inputs. This is the path that actually reproduces the accepted-paper scientific analyses.

```bash
python scripts/validate_accepted_papers.py
python -m pytest -m archive   # or: python -m pytest tests/ for both levels together
```

Verifies source hashes, canonical data structure, re-runs the archived `score_results.py` / `posthoc_contrasts.py` (GenAI4Health) and `analyze_sequential_gemini.py` / `analyze_aligned_control.py` (AgenticLS) in a scratch copy, compares every output against the archive, and validates the result-provenance map — then prints PASS/FAIL. As of this writing: **PASS** (GenAI4Health and AgenticLS analyses reproduce exactly; see `docs/phase3_reproduction_report.md` and the one documented exception in Known provenance limitations below).

See `docs/reproducibility_levels.md` for the full three-level breakdown (public validation / full archival reproduction / model re-execution — the last of which is not required and not performed by anything in this repository), `docs/reproduction_environment.md` for why Python 3.12 / scipy 1.16.3 are pinned, `docs/public_dependency_audit.md` for exactly which files each level needs, and `.github/workflows/reproducibility.yml` for CI (its `public-integrity` job always runs; its `full-archive-reproduction` job self-detects whether the restricted inputs are present and skips cleanly, rather than failing, when they are not).

A smaller first-release scope (`V1_CORE`/`V1_SUPPORTING`, deferring redundant intermediates and operational clutter) is proposed in `docs/public_v1_scope.md`: `python scripts/build_public_release.py --v1-core`.

The Groq extension is excluded from both commands by design (see Known provenance limitations).

## Repository map

```
papers/<paper>/            README, reproduce.md, paper/ (metadata; PDFs not redistributed)
experiments/
  static_conflict/         GenAI4Health + AgenticLS's shared foundation
  persistent_context/       gemini_persistent_260/, gemini_aligned_control_40/ (AgenticLS)
                             groq_gpt_oss_120b/ (extension, out of scope)
  each experiment folder:   README.md + experiment_manifest.json + historical_package/
                             (intact, byte-identical copy of the recovered execution package)
data/                       frozen-cohort and hash-manifest registries (not duplicate copies)
artifacts/                  raw / canonical / summary indexes into historical_package/
scripts/                    reproduction + release tooling (see file headers for labels)
scripts/reconstructed/      NEW Phase-4 code, clearly labeled, never historical
tests/                      pytest, marked @public (stripped-release-safe) or @archive (needs LICENSE_REVIEW)
validation/                 Phase 3/4 scratch output, logs, comparisons (regenerated, not archival)
docs/                       inventory, provenance, methodology, status, limitations, audits
```

## Provenance

```
frozen input → runner → raw provider output → canonical/clean dataset → analysis → paper result
```

Every `historical_package/` is an unedited, byte-identical copy of a recovered execution package (verify with `python scripts/verify_hashes.py`). `docs/data_provenance.md` traces the full chain from the raw MEDAL source files to each frozen cohort; `docs/result_provenance.csv` maps 122 individual results (108 GenAI4Health, 14 AgenticLS) to their source cohort, raw file, canonical file, analysis script, analysis output, and reproduction status — one row per result, nothing typed by hand.

## Scope and interpretation caveats

- **Self-reported confidence is not calibrated uncertainty.** The 0–100 confidence values the models return are model-reported numbers, not validated probabilities — this repository does not claim otherwise anywhere, and neither should anything built on top of it.
- **`dominant_evidence_ids` is reported attribution, not proof of causal evidence use.** A model naming an evidence card as "dominant" does not establish that the card causally drove the decision.
- **Neither accepted paper's findings should be read as "fully open."** 64 files (frozen cohorts, generated prompts, raw/canonical model outputs) remain under redistribution-rights review and are excluded from every public build regardless of this repository's own reproducibility guarantees — see Data / licensing below.

## Known provenance limitations

- **`posthoc_contrasts.py` script-hash discrepancy.** The archived post-hoc analysis manifest records an earlier script hash that is no longer available. The recovered script differs from that recorded hash but regenerates all archived post-hoc outputs byte-for-byte under the verified reproduction environment (SciPy 1.16.3). The historical code change cannot be reconstructed and is retained as a provenance limitation. The mismatch is not claimed to be resolved; see `docs/posthoc_hash_investigation.md`.
- **Figure 1's original plotting code is missing.** Its underlying data was reproduced exactly; a NEW, clearly labeled reconstruction (`scripts/reconstructed/plot_genai4health_figure1.py`) redraws the panels. See `docs/figure1_reconstruction.md`.
- **`canonical_results_reference.md`'s original generator is missing.** A NEW, clearly labeled reconstruction (`scripts/reconstructed/build_canonical_results_reference.py`) regenerates it — byte-identical to the archive. See `docs/canonical_reference_reconstruction.md`.
- Full list, including scientific limitations drawn from the recovered protocols: `docs/limitations.md`.

## Data / licensing

Some recovered artifacts — raw MEDAL Cochrane and AHA guideline text, cohorts and prompts built from it, and provider outputs that may restate it — remain under redistribution-rights review (64 files; none cleared yet) and are excluded from every public build. See `docs/public_release_audit.md`, `docs/public_artifact_plan.md`, and the file-by-file `docs/licensing_decision_matrix.md` for the classification and reasoning, `docs/restricted_artifact_substitutes.md` for what's public instead, and `docs/public_release_manifest_draft.csv` / `scripts/build_public_release.py` for a dry-run preview build (writes to `dist/public_release_preview/`, never published automatically).

Rights are split: the code license covers code only; it does **not** grant rights to the withheld data/provider outputs or to the paper PDFs. See `DATA_AND_ARTIFACT_RIGHTS.md` and `THIRD_PARTY_NOTICES.md`. The 64 withheld files stay excluded; the repository is designed to be publishable without them.

Code license: **MIT** (see [`LICENSE`](LICENSE), Copyright (c) 2026 Manav Vohra and Arshleen Kaur). See also `docs/license_options.md` for how the choice was framed.

**Scope of the MIT License.** The MIT License in [`LICENSE`](LICENSE) applies to **project-authored code only** (and the project-authored documentation and synthetic evidence cards described in `THIRD_PARTY_NOTICES.md`). It does **not** grant any right to redistribute: MEDAL-derived material; Cochrane-derived material; AHA-derived material; provider-generated (Gemini/Groq) model outputs; any artifact classified `LICENSE_REVIEW`; or the camera-ready paper PDFs (unless separately permitted by their copyright holders). Those remain under separate, unresolved review and are excluded from the public release.

## Citation

See [`CITATION.cff`](CITATION.cff). The AgenticLS reference uses only fields printed in its camera-ready PDF; the GenAI4Health reference is still pending its camera-ready. No DOI, page numbers, proceedings volume, repository URL, or release date is recorded, because none exists yet.
