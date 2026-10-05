# artifacts/raw

Raw execution artifacts live **inside the intact historical packages**, not here, to avoid duplicating them. [`raw_artifact_index.csv`](raw_artifact_index.csv) lists each one (raw results, attempt logs, checkpoints, backups) with its path, sha256 and notes.

Rules: never edit, reorder, deduplicate or reformat. Derived cleanups go to new files under `artifacts/canonical/`.

| Experiment | Raw / attempt files |
|---|---|
| static (all runs) | `experiments/static_conflict/historical_package/evidence_not_vote_starter/results/` |
| Gemini persistent 260 (AgenticLS) | `…/gemini_persistent_260/historical_package/agenticls_gemini_sequential/results/` |
| Gemini aligned control 40 (AgenticLS) | `…/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control/results/` |
| Groq GPT-OSS extension (NOT accepted AgenticLS) | `…/groq_gpt_oss_120b/historical_package/agenticls_groq_full_ready/{results,groq_interim_snapshot}/` + `nohup.out`, dry runs |

**Deferred:** Groq `results/groq_260_results.jsonl`, `groq_260_attempts.jsonl` and `groq_260_resume_20261004.log` are still being written by the running job. Copy them after it exits.
