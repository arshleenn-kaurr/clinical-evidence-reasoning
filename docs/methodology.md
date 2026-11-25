# Methodology

Summaries only. The historical protocol files (paths in parentheses) are authoritative.

## Static evidence-conflict benchmark (GenAI4Health; AgenticLS foundation)
(`static_conflict/historical_package/evidence_not_vote_starter/README.md`, `analysis_contract.md`, `audit_protocol.md`)

- Cases: MEDAL Cochrane items (High/Moderate quality, Yes/No → support/do_not_support), manually audited and anonymized. Veto cohort: AHA COR III recommendations.
- Evidence: one higher-tier anchor (E0) plus deterministic synthetic lower-tier cards, which are not claimed to be real studies.
- Conditions: `H, H_L1, H_L2, H_L4, H_L4_ALIGNED, L4_H`.
- Primary endpoint: EDR_4 (conditional on H correct). Secondary endpoints: accuracy, EDR_1/2, flip threshold, order sensitivity, aligned-control delta (accuracy), confidence shift, veto failure rate. Paired bootstrap 10,000 resamples, seed 68020260909.
- Cohorts: primary 40 and veto 15 (frozen 2026-09-09T06:12:54Z); replication 260 (frozen 2026-09-09T09:54:17Z, "supplementary replication extension", selection independent of model outputs).
- Models: `gemini-3.6-flash` (temperature 0); `openai/gpt-oss-120b` via Groq (temperature 0, reasoning_effort medium), the latter as a post-hoc second-model sensitivity analysis.
- Post-hoc: exact CIs, conflict-vs-aligned confidence contrasts, stratified and anonymization sensitivity (`posthoc_contrasts.py`, labelled POST_HOC in its manifest); dominant-evidence analysis.

## Persistent context: accepted AgenticLS experiments
(`gemini_persistent_260/…/PROTOCOL_FREEZE_GEMINI.md`, `gemini_aligned_control_40/…/PROTOCOL_FREEZE_ALIGNED_CONTROL.md`)

- **Gemini persistent 260:** for the shared 260 cohort, one retained conversation H→H_L1→H_L2→H_L3→H_L4 plus a fresh one-shot H_L4 with identical terminal evidence (6 calls/case). Arm order balanced by SHA256(case_id) within strata. Primary endpoints: terminal categorical agreement (Clopper-Pearson), terminal confidence difference (paired bootstrap 100,000, seed 20260922), E0-inclusion transition, sequential trajectory. Exploratory: threshold sensitivity τ=70–95. `gemini-3.6-flash` with **no sampling parameters sent** and provider-default thinking (the protocol notes this differs from the static benchmark's temperature=0).
- **Aligned persistent control 40 (post-hoc):** a 10-per-stratum subset of the same cohort. It reuses the existing persistent H response as the branch point, then 4 aligned persistent updates + 1 fresh aligned terminal call (5 calls/case). Primary contrast: (conflict persistent−fresh gap) − (aligned persistent−fresh gap), bootstrap 10,000, seed 2026092301.

## Persistent context: Groq GPT-OSS-120B extension (not part of the accepted papers)
(`groq_gpt_oss_120b/…/PROTOCOL_FREEZE_DRAFT_GROQ.md`)

Same 260 cohort. A **5-state batch arm** vs a 5-turn persistent arm (10 calls/case), with temperature 0 and reasoning_effort medium. The design differs from the accepted Gemini experiment. In progress.
