# AgenticLS Gemini persistent-context extension — frozen execution plan

## Status
Post-hoc extension of the frozen *Evidence Is Not a Vote* benchmark. This execution and analysis plan is frozen before aggregate results from the Gemini persistent-context experiment are inspected.

## Core question
For identical terminal clinical evidence, do persistent multi-turn updates produce different observable terminal assessments than a fresh one-shot presentation?

## Interpretation boundary
The persistent condition jointly changes incremental evidence delivery, retained prior assistant outputs, prior provisional decisions, self-reported confidence, rationale, reported attribution, and conversation history. Any difference is interpreted as **persistent-context update sensitivity**. It is not interpreted as cognitive anchoring, calibrated uncertainty, latent belief, a pure causal effect of evidence arrival, autonomous retrieval, clinical utility, or validated routing behavior.

## Cohort
The exact independently frozen 260-case replication cohort is used without outcome-dependent inclusion, removal, rebalancing, or substitution. `replication_cases_verified.jsonl` must have SHA256:

`b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a`

The 10-case `dev_cases.jsonl` cohort is operational-only and excluded from the 260 evaluation cohort.

## Model and API
- model identifier: `gemini-3.6-flash`
- Google Gemini `generateContent` REST API
- one completion per prompt-condition
- strict structured JSON output using `responseMimeType=application/json` plus `responseJsonSchema`
- no explicit thinking/reasoning parameter, matching the historical benchmark's provider-default thinking configuration as closely as the current API permits
- the historical static benchmark supplied `temperature=0`
- current Gemini 3.6 Flash documentation deprecates/ignores `temperature`, `top_p`, and `top_k`; the new runner therefore omits those sampling fields rather than falsely treating them as controlled

This API-era difference must be disclosed in the manuscript if the extension is reported.

## Evidence construction
The evidence cards, evidence identifiers, order, question, hierarchy instruction, and synthetic lower-tier construction are inherited from the frozen benchmark. The evidence-weighting instruction remains:

> Evidence items may differ in study design, certainty, directness, and relevance. Do not count sources as votes. Weigh each item according to the strength and clinical relevance of the evidence it represents.

## Per-case design
Six successful model calls per case.

### Persistent arm
One retained conversation:
1. `H`
2. `H_L1`
3. `H_L2`
4. `H_L3`
5. `H_L4`

Only a successful canonical assistant response enters later history. A failed attempt is retried from the identical pre-turn history and is never appended to conversation history.

### Fresh terminal arm
A new empty conversation receives `H+L1+L2+L3+L4` in the same evidence order and returns one assessment (`H_L4`).

Thus the terminal evidence is identical while the evidence-delivery/history process differs.

### Arm order
Fresh-first versus sequential-first execution order is deterministically balanced within the frozen evidence-quality × reference-decision strata using SHA256(case_id), independent of model outputs. This is an operational wall-clock control, not an endpoint.

## Call count
`260 × 6 = 1,560` required successful assessments.

## Primary endpoints
1. Terminal categorical agreement between sequential `H_L4` and fresh `H_L4`. Report n/N, disagreement rate, and exact two-sided Clopper-Pearson CI.
2. Terminal self-reported confidence difference, sequential minus fresh. Report paired mean, median, 95% paired bootstrap CI (100,000 resamples, fixed seed 20260922), and lower/equal/higher counts.
3. Terminal E0-inclusion transition based on whether `E0` appears in `dominant_evidence_ids` in fresh versus sequential terminal outputs.
4. Sequential trajectory across H, H_L1, H_L2, H_L3, H_L4: turn means, change from initial, fully non-increasing fraction, terminal <= initial fraction, first confidence decline, first categorical deviation, and E0-inclusion trajectory.

## Secondary endpoints
- terminal correctness against the frozen reference label
- exact McNemar test on paired binary terminal correctness
- number of reported dominant-evidence IDs
- presence of lower-tier IDs in reported attribution
- stratification by frozen reference direction and, if reconstructed from cohort metadata, anchor quality
- rationale analyses only if explicitly labeled exploratory

## Exploratory threshold sensitivity
For every integer threshold `tau=70,...,95`, report how often sequential and fresh terminal confidence lie on opposite sides of the threshold. This is descriptive counterfactual threshold sensitivity only. It is not routing performance, policy validation, or evidence that confidence should control escalation.

## Retry and checkpoint rules
- every attempted provider request is retained in the attempts JSONL
- transient errors are retried with the identical serialized request
- 400/401/403/404 are fatal configuration/authentication errors
- persistent 429 exits cleanly so the identical command can resume later
- completed successful run IDs are skipped on resume
- failed attempts never enter later sequential context
- no aggregate main-cohort results are inspected until all 1,560 successful assessments are complete

## Smoke-test gate
Run exactly the 10 excluded dev cases before main execution. The structural validator must pass 60/60 successful states, correct cumulative evidence IDs, correct message/history counts, no duplicate successful run IDs, valid model/schema metadata, and no canonical error rows. The validator intentionally computes no scientific outcome summaries.
