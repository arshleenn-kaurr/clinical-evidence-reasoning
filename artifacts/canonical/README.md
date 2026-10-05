# artifacts/canonical

[`canonical_artifact_index.csv`](canonical_artifact_index.csv) lists the historical clean/canonical result files inside the packages (static `*_CLEAN.jsonl`; the Gemini persistent and aligned runners' results files). They were produced historically and are preserved as-is.

Where no CLEAN file exists (static Gemini primary and veto), the archived result file was used directly as analysis input, per the post-hoc manifest.

TODO: the Groq extension has no canonical file. Its raw results contain duplicate successful run_ids; `scripts/canonicalize_results.py` intentionally refuses to run until a rule is decided.
