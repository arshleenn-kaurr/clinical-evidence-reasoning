# AgenticLS post-hoc aligned persistent-context control — frozen protocol

Freeze date: 2026-09-23

## Motivation
The completed 260-case persistent conflict experiment showed a large persistent-minus-fresh confidence difference under the same terminal clinical evidence. A remaining alternative explanation is generic multi-turn/persistent-context drift rather than an effect specific to accumulating conflicting evidence.

## Frozen cohort
Rather than use the older 40-case primary cohort, this control uses a deterministic balanced 40-case subset of the **same 260-case replication cohort** used in the completed persistent conflict experiment. This permits exact same-case comparison to the already-frozen conflict results.

Selection was performed from case metadata only, without consulting case-level model outcomes.

Selection tag: `agenticls-aligned-control-v1-20260923`

Source 260-case file SHA256:
`b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a`

Frozen 40-case control file SHA256:
`6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540`

The control contains 10 cases in each stratum:
- High / support
- High / do_not_support
- Moderate / support
- Moderate / do_not_support

Within each stratum, cases were ordered by SHA256 of `agenticls-aligned-control-v1-20260923|<case_id>` and the first 10 were selected.

## Exact branch-point design
For each selected case, the experiment reuses the already-recorded successful `sequential::H` response from the completed conflict persistent experiment as the branch point. The H prompt and H assistant output are therefore **identical** for the aligned and existing conflict sequential branches.

New aligned persistent continuation:
- existing H response (no new API call)
- +L1 aligned
- +L2 aligned
- +L3 aligned
- +L4 aligned

Fresh aligned comparison:
- H + L1 aligned + L2 aligned + L3 aligned + L4 aligned in a new conversation

The four lower-tier cards retain the same IDs, study-design descriptions, certainty labels, limitations, and ordering used in the conflict experiment. Only their directional result statements are aligned with the frozen reference direction rather than opposed to it.

## New call count
Per case:
- 4 aligned persistent continuation calls
- 1 fresh aligned terminal call

Total: 40 × 5 = **200 successful new calls**.

## Execution controls
- Model: `gemini-3.6-flash`
- Same strict structured-output schema as the completed persistent experiment
- No explicit reasoning parameter
- No explicit sampling parameters, matching the completed persistent runner
- Successful prior outputs remain in persistent conversation history
- Failed attempts are logged and retried with identical request payloads
- Resume-safe JSONL checkpointing
- Fresh-first vs aligned-sequential-first execution is exactly balanced 5/5 within each 10-case stratum

## Primary post-hoc analysis
For each of the same 40 cases, compute:

`gap_conflict = confidence(conflict persistent H+L4) - confidence(conflict fresh H+L4)`

`gap_aligned = confidence(aligned persistent H+L4_A) - confidence(aligned fresh H+L4_A)`

Primary control contrast:

`interaction = gap_conflict - gap_aligned`

Report paired mean, median, direction counts, and 10,000 case-level bootstrap 95% CI. Bootstrap seed: `2026092301`.

Interpretation:
- aligned gap near 0 while conflict gap is negative: evidence that the main persistent penalty is not explained by generic multi-turn drift alone
- aligned gap similar to conflict gap: evidence that generic persistent-context effects plausibly explain much of the main result
- intermediate aligned gap: both persistent interaction and evidence polarity may contribute

This control is post-hoc and does not establish a unique causal mechanism.
