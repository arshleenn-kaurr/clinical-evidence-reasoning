# GPT-OSS-120B static sensitivity (GenAI4Health, SENSITIVITY)

All paths are under `../historical_package/evidence_not_vote_starter/`. Runner: `run_groq.py` (`openai/gpt-oss-120b` via Groq; temperature 0, reasoning_effort medium; hash locked in `data/evaluation_lock.sha256`).

| Run | Inputs | Raw | Clean | Rows | Scoring |
|---|---|---|---|---|---|
| Primary 40 | `data/final_main_prompts.jsonl` | `results/final_main_gpt_oss_120b_RAW.jsonl` | `…_CLEAN.jsonl` | 240 ok | `analysis/gpt_oss_primary/` |
| Veto 15 | `data/final_veto_prompts.jsonl` | `results/final_veto_gpt_oss_120b_RAW.jsonl` | `…_CLEAN.jsonl` | 90 ok | `analysis/gpt_oss_veto/` |

In both runs the RAW, CLEAN and unsuffixed result files are byte-identical, so no failed attempts are retained. Interim checkpoint: `results/final_main_gpt_oss_120b_checkpoint_204.jsonl`. The post-hoc manifest describes GPT-OSS primary as a "post-hoc SECOND-MODEL SENSITIVITY ANALYSIS" run after the Gemini results were known.

Not to be confused with the Groq **persistent-context** extension in `persistent_context/groq_gpt_oss_120b/`.
