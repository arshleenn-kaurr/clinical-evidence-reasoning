# persistent_context

Does persistent multi-turn evidence delivery produce the same assessment as a fresh presentation of the same terminal evidence? All three runs use the **same frozen 260-case cohort** (sha256 `b3bc2dd1…a818a`, byte-identical to the static replication cohort).

| Run | Paper | Design | Status |
|---|---|---|---|
| [gemini_persistent_260/](gemini_persistent_260/) | **AgenticLS (accepted)** | `gemini-3.6-flash`; persistent H→H_L1→H_L2→H_L3→H_L4 + one fresh H_L4 per case (6 calls/case) | RECOVERED; counts + hashes verified |
| [gemini_aligned_control_40/](gemini_aligned_control_40/) | **AgenticLS (accepted)** | post-hoc control: 40-case subset; reuses the Gemini-260 sequential H, 4 aligned persistent updates + 1 fresh aligned terminal (5 calls/case) | RECOVERED; counts + hashes verified |
| [groq_gpt_oss_120b/](groq_gpt_oss_120b/) | **None: POST-ACCEPTANCE CROSS-MODEL EXTENSION** | `openai/gpt-oss-120b` on Groq; 5-state batch arm vs 5-turn sequential arm (10 calls/case) | **STATUS: IN PROGRESS / NOT CANONICALIZED** |

The Groq run's original files use "AgenticLS" in titles and paths. Those files are frozen and were not edited. That naming does **not** make it the AgenticLS paper's experiment. Its own README calls it "not a direct sequential extension of the historical Gemini 260-case outputs", and its design differs (batch arm instead of a single fresh comparator).

Each run keeps an intact byte-identical `historical_package/` with its manifests verifying in place.
