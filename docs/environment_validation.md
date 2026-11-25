# Environment validation (Phase 3)

## CURRENT REPRODUCTION ENVIRONMENT (2026-10-04)

| Item | Value |
|---|---|
| OS | macOS 27.0.1 (build 26A434), arm64 |
| Python | CPython 3.14.8 (`/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`) |
| Main env (`validation/.venv`) | numpy 2.5.3, pandas 3.0.6, scipy 1.18.1 (`validation/logs/pip_freeze_main_env.txt`) |
| Sensitivity env (`validation/.venv_scipyprobe`) | numpy 2.5.3, pandas 3.0.6, scipy 1.16.3 (`validation/logs/pip_freeze_scipy1163_env.txt`) |
| AgenticLS analyses | system Python 3.14.8, standard library only |
| API calls | **none**; no API keys set (checked by `scripts/validate_environment.py`) |

The archived `requirements.txt` (`datasets>=3.0`, `pandas>=2.0`, `numpy>=1.26`) sets lower bounds only. `datasets` is needed only for case preparation, which was not re-run. scipy is imported by `posthoc_contrasts.py` but not listed there.

Commands and timestamps are in `validation/logs/` (`step2_*`, `step3_*`, `step4_prespecified.log`, `step5_posthoc.log`, `step6_7_agenticls.log`, `step4_7_compare.log`). Source artifact hashes: `validation/hash_verification_report.json`.

## HISTORICAL EXECUTION ENVIRONMENT (what the files show; mostly unknown)

| Evidence | Implication |
|---|---|
| Static package `__pycache__/*.cpython-314.pyc` (score_results, run_gemini, run_groq, make_*), `prepare_cases.cpython-310.pyc` | Static pipeline was run with CPython 3.14 (case preparation once with 3.10) |
| Gemini persistent / aligned `__pycache__/*.cpython-313.pyc` | AgenticLS scripts were run with CPython 3.13 |
| Post-hoc outputs reproduce byte-exactly only with scipy < 1.17 (1.16.x tested) | scipy at post-hoc time was probably 1.16.x (inference) |
| numpy / pandas versions | **unknown**; not recorded |
| OS / hardware | **unknown** |

The current environment is **not** claimed to be the historical one. Exact reproduction across pandas 3.0.6 and Python 3.14.8 shows the outputs don't depend on those differences for these inputs.
