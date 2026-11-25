# Frozen analysis contract v0

## Central question
Does the probability of a correct therapeutic decision degrade as the number of lower-tier conflicting evidence items increases, despite a fixed higher-tier anchor?

## Unit
One therapeutic decision case.

## Main cohort
Cochrane-derived MEDAL items with:
- binary reference answer (Yes/No)
- High or Moderate evidence quality
- usable supporting note
- one-action therapeutic question after audit

## Veto cohort
AHA COR III recommendations, preferably LOE A/B, with a clearly actionable "do not" implication after audit.

## Conditions
H, H_L1, H_L2, H_L4, H_L4_ALIGNED, L4_H.

## Primary endpoint
EDR_4, conditional on H being correct.

## Secondary endpoints
Accuracy, EDR_1, EDR_2, flip threshold, order sensitivity, aligned-control delta, confidence shift, veto failure rate.

## Fixed seeds
Candidate sampling seed: 20260909
Condition ordering seed: deterministic SHA256(case_id + condition)
Bootstrap seed: 68020260909

## Exclusions after freeze
Only:
1. API/transport failure with no model answer after retry policy;
2. response cannot be parsed after one deterministic repair attempt;
3. duplicated prompt_id due to implementation error.

Clinical ambiguity is NOT a post-hoc exclusion criterion after test outputs are visible.

## Claim discipline
- This benchmark tests controlled evidence-composition robustness, not real-world prospective clinical decision quality.
- Synthetic lower-tier cards are perturbations, not claimed real studies.
- A negative result is valid: if models remain stable, report robustness within the tested contract.
