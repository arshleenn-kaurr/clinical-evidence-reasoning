# Evidence Is Not a Vote — benchmark starter

Working question:
> When clinical evidence conflicts, do LLMs weight evidence by epistemic strength, or can increasing quantities of weaker evidence overturn a decision supported by stronger evidence?

This scaffold uses:
- MEDAL Cochrane systematic-review items for the main evidence-dilution cohort.
- MEDAL AHA guideline recommendations for a smaller "veto" cohort.
- Controlled synthetic lower-tier evidence cards as perturbations. These cards are not claimed to be real studies; they are matched benchmark perturbations used to isolate evidence quantity and direction.

## Frozen v0 protocol

### Main cohort
Select Cochrane cases with:
- answer in {Yes, No}
- evidence-quality in {High, Moderate}
- nonempty supporting notes
- a question that can be expressed as one clear therapeutic decision

Map:
- Yes -> `support`
- No -> `do_not_support`

### Veto cohort
Select AHA recommendations with:
- COR III (harm or no benefit)
- LOE A or B where possible
- one clear actionable recommendation

Map:
- COR III -> `do_not_support`

### Conditions per case
1. `H` — strong anchor only
2. `H_L1` — anchor + 1 weak conflicting card
3. `H_L2` — anchor + 2 weak conflicting cards
4. `H_L4` — anchor + 4 weak conflicting cards
5. `H_L4_ALIGNED` — anchor + 4 weak aligned cards
6. `L4_H` — same evidence as H_L4, but weak cards first and anchor last

Do not add H_L8 unless the protocol is amended before the held-out test run.

### Primary endpoint
Evidence Dilution Rate at n weak conflicting cards:

EDR_n = P(prediction(H+nL) != reference | prediction(H) == reference)

Primary headline comparison: `EDR_4`.

### Secondary endpoints
- overall accuracy by condition
- flip threshold: smallest n in {1,2,4} that changes a correct H decision
- order sensitivity: prediction(H_L4) != prediction(L4_H)
- aligned-control delta: accuracy(H_L4_ALIGNED) - accuracy(H_L4)
- confidence change from H to H_L4
- veto failure rate in COR III subset

### Statistics
- case is the unit of resampling
- paired bootstrap, 10,000 resamples, fixed seed 68020260909
- report 95% percentile CIs
- report each model separately before pooling
- no case deletion after test outputs are inspected, except prespecified parse failures

## Workflow

1. Install dependencies:
   `pip install -r requirements.txt`

2. Download/filter candidate cases:
   `python prepare_cases.py --out-dir data`

3. Manually audit candidate CSVs.
   Fill:
   - `eligible` = 1/0
   - `anonymized_question`
   - `anonymized_anchor`
   - `audit_note`
   For veto cases also fill `veto_subtype` as `harm` or `no_benefit` when unambiguous.

4. Freeze an audited benchmark file:
   `python freeze_cases.py --main data/cochrane_candidates.csv --veto data/aha_veto_candidates.csv --out data/frozen_cases.jsonl`

5. Generate all prompt conditions:
   `python make_conditions.py --cases data/frozen_cases.jsonl --out data/prompts.jsonl`

6. Run models using your preferred API harness. Each output should conform to:
   `response_schema.json`

7. Save one JSONL record per prompt with:
   - prompt_id
   - case_id
   - condition
   - model
   - decision
   - confidence
   - rationale

8. Score:
   `python score_results.py --results results.jsonl --cases data/frozen_cases.jsonl --out-dir analysis`

## Important scientific constraints

- Synthetic perturbation cards must be generated deterministically from templates, not written case-by-case after seeing model behavior.
- The aligned and conflicting cards must have identical study-design metadata; only the reported direction changes.
- Do not claim the perturbation cards are real published studies.
- Do not expose intervention identity if the model can answer from memorized guideline knowledge. Use anonymized question/anchor fields.
- Keep development and final test cases separate before prompt tuning.
- If a case is ambiguous, exclude it during manual audit, before any held-out model run.
