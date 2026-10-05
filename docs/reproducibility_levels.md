# Reproducibility levels

This repository supports three distinct levels of "reproducibility." They require different inputs, answer different questions, and only one of them is part of ordinary CI. Conflating them is exactly what caused the public-release architecture problem this document (and `docs/public_dependency_audit.md`) exists to prevent.

## LEVEL 1 — PUBLIC ARTIFACT VALIDATION

**Available to anyone with the public repo.** No `LICENSE_REVIEW` input is ever required.

Confirms that the *public release itself* is internally consistent: its manifest is well-formed, every file it claims to ship matches its recorded hash, no restricted or unclassified file has leaked in, the two reconstructed-code artifacts (Figure 1 plotting, the canonical-reference generator) are present, labeled, and — for the reference generator, whose own inputs are themselves public — actually re-run and byte-identical to the archive, documentation links resolve, and citation/required-docs metadata is present.

```bash
python scripts/validate_public_release.py
python -m pytest -m public
```

This does **not** reproduce the accepted-paper scientific analyses. It cannot: `score_results.py`, `posthoc_contrasts.py`, `analyze_sequential_gemini.py`, and `analyze_aligned_control.py` all require the frozen cohorts, prompts, and raw/canonical model outputs, which are `LICENSE_REVIEW` and intentionally excluded from the public release (see `docs/public_dependency_audit.md`). Level 1 checks that the public artifact is trustworthy and well-formed; it is a release-engineering guarantee, not a scientific one.

Verified, from a copy of the preview placed **outside** this repository (no parent-repo fallback possible): `validation/public_preview_validation/` — PASS.

## LEVEL 2 — FULL ARCHIVAL ANALYSIS REPRODUCTION

**Requires the complete archival artifact**, including the `LICENSE_REVIEW` frozen cohorts/prompts/raw-canonical results.

This is the level that actually re-derives the accepted-paper results: it copies the historical packages to a scratch directory, re-runs the four archived analysis scripts against the archived model outputs, and compares every regenerated output to the archive byte-for-byte (or, for the one scipy-version-sensitive cell, to within 4×10⁻¹⁷).

```bash
python scripts/verify_hashes.py
python scripts/validate_accepted_papers.py
python -m pytest -m archive
```

**No model/API call is made at this level either.** The archived provider outputs (every successful and failed attempt, every canonical result row) are what gets re-analyzed — see "no new model/API calls" below. This is the strongest reproducibility claim this repository makes, and it is what Phase 3 (`docs/phase3_reproduction_report.md`) and the `full-archive-reproduction` CI job exercise.

## LEVEL 3 — MODEL RE-EXECUTION

**Not required to reproduce the reported analyses, and not part of ordinary CI.** This would mean re-running the frozen runners (`run_gemini.py`, `run_groq.py`, `run_sequential_gemini.py`, `run_aligned_control_gemini.py`) against live Gemini/Groq APIs to generate *new* model outputs, rather than re-analyzing the archived ones.

This repository's tooling never does this. `scripts/validate_accepted_papers.py`, every pytest marker, and both CI jobs are explicitly scoped to Levels 1 and 2 only. A Level 3 re-execution would:
- need live API keys and cost money per call,
- not be expected to byte-reproduce the archived raw outputs (model/provider state drifts over time; the Gemini persistent-context protocol itself documents one such API-era difference — see `docs/limitations.md`),
- and is explicitly out of scope for the Groq GPT-OSS extension, which remains unanalyzed and uncanonicalized in this repository regardless.

If someone wants to attempt Level 3, the frozen runners and their protocols document exactly what was run (model, temperature, reasoning settings, endpoints); that is a deliberate act outside this repository's reproducibility guarantees, not something any script here performs automatically.

## Why Levels 1 and 2 can both say "no new model/API calls"

The frozen runners already made every model call that matters, once, historically, and logged every attempt — successful and failed — into archived JSONL files (`docs/data_provenance.md`). "Reproducing the analysis" at both Level 1 (trivially, since it touches no model output) and Level 2 (by design) means re-running the deterministic, non-API analysis code over those already-archived provider outputs, not calling a model again. This is what makes Level 2 reproducible at all without incurring new API cost or encountering model drift: the inputs to the analysis step are frozen files, not a live endpoint.
