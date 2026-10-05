# Reproducibility

Two explicitly separate levels (full detail: `docs/public_dependency_audit.md`; environment: `docs/reproduction_environment.md`).

## Public artifact validation — no restricted inputs needed

```bash
python scripts/validate_public_release.py
python -m pytest -m public
```

Always runnable from `dist/public_release_preview/` (build it with `python scripts/build_public_release.py`) or any checkout built the same way. Verified by running both commands from a copy of the preview placed **outside** this repository: `validation/public_preview_validation/` (PASS, 0 problems).

## Full archival reproduction — requires the complete local archive

```bash
python scripts/verify_hashes.py            # 222 copies, 95 historical manifest entries, 4 cohort anchors; one documented discrepancy
python scripts/validate_accepted_papers.py  # the single accepted-paper validation command
python -m pytest -m archive                 # or: python -m pytest tests/ for both levels
python scripts/validate_environment.py
```

All raw outputs are archived, so the accepted-paper analyses re-run **without API calls**. Historical scripts write into their own package directories: `validate_accepted_papers.py` and the `archive`-marked tests always use a scratch copy and never write into `historical_package/`.

Paper maps: [`papers/genai4health/reproduce.md`](../papers/genai4health/reproduce.md), [`papers/agenticls/reproduce.md`](../papers/agenticls/reproduce.md). Full Phase 3 reproduction report: [`phase3_reproduction_report.md`](phase3_reproduction_report.md).

Re-running the *original frozen runners* (not the analysis scripts) would be a new execution against live APIs (and, for Gemini, a model whose sampling controls changed since the historical runs); that is not expected to byte-reproduce the archived raw outputs, and is out of scope for both reproducibility levels above.

## CI

`.github/workflows/reproducibility.yml`: `public-integrity` always runs; `full-archive-reproduction` self-detects whether the restricted `LICENSE_REVIEW` inputs are present in the checkout and skips cleanly (not a failure) when they are not — e.g. on a future stripped public repo.
