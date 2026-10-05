# AgenticLS (NeurIPS 2026 workshop paper)

*Stable Decisions Can Hide Evidence Sensitivity in Life-Science Evidence Synthesis* — Manav Vohra, Arshleen Kaur. AgenticLS: Life-Science Agents Workshop, NeurIPS 2026.

**Manuscript: CAMERA-READY INGESTED / VERIFIED** (`paper/`, SHA256 `1b7311a7…2758e5`; details in [`paper/README.md`](paper/README.md)).

Uses:
1. The static benchmark foundation: [`experiments/static_conflict/`](../../experiments/static_conflict/) (shared 260 cohort, evidence-card construction, prompt template)
2. The Gemini persistent-context 260 experiment with its fresh comparator: [`persistent_context/gemini_persistent_260/`](../../experiments/persistent_context/gemini_persistent_260/)
3. The Gemini aligned persistent control 40 with its fresh aligned comparator: [`persistent_context/gemini_aligned_control_40/`](../../experiments/persistent_context/gemini_aligned_control_40/)

**Not included:** the Groq GPT-OSS-120B persistent-context run (`persistent_context/groq_gpt_oss_120b/`). It is a separate post-acceptance cross-model extension and is not a substitute for the accepted experiments.

Reproduction map: [reproduce.md](reproduce.md). Provenance mapping: [`docs/camera_ready_provenance_mapping.csv`](../../docs/camera_ready_provenance_mapping.csv) (mapped; see audit for two open author-review items).
