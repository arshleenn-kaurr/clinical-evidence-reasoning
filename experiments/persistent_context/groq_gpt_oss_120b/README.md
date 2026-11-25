# Groq GPT-OSS-120B persistent-context extension (NOT the accepted AgenticLS experiment)

> **POST-ACCEPTANCE CROSS-MODEL EXTENSION**
> **STATUS: IN PROGRESS / NOT CANONICALIZED**
> Does not support, and must never be cited as, an accepted-paper result. Excluded from `scripts/validate_accepted_papers.py`, `tests/`, CI (`.github/workflows/reproducibility.yml`), and the public-release manifest by design.

A new cross-model extension after acceptance. It must not be used as, or described as, the AgenticLS reproduction.

All paths are under `historical_package/agenticls_groq_full_ready/`, a byte-identical copy of the recovered folder with its original layout (`SHA256SUMS.txt` 7/7 verify). See [PROVENANCE.md](PROVENANCE.md) and [CONFIG_NOTE.md](CONFIG_NOTE.md).

- `openai/gpt-oss-120b` on Groq; temperature 0; reasoning_effort medium; strict JSON schema
- Arms: batch (5 independent prompts H…H_L4) vs persistent sequential (5 turns). Target 2,600 successful calls.
- Status: **in progress**. The runner was restarted 2026-10-04 04:09 (PID 1444). `results/groq_260_results.jsonl`, `groq_260_attempts.jsonl` and `groq_260_resume_20261004.log` are **not yet copied**.
- Known issue (documented, not fixed): the live results file contains duplicate successful run_ids (see `docs/migration_plan.md`).
