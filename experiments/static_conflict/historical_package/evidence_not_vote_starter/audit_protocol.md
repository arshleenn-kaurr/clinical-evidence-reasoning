# Manual audit protocol

Audit BEFORE any held-out model outputs are viewed.

## Main Cochrane cohort

Keep a case only if all are true:

1. The question asks one clinically interpretable therapeutic/effectiveness decision.
2. The reference label `Yes` or `No` is supported by the MEDAL source note.
3. `evidence-quality` is High or Moderate.
4. The anchor note can be rewritten without adding facts not in the source.
5. After anonymization, the case remains understandable.
6. The answer is not dependent on knowing the hidden intervention's identity.
7. The source text is not internally contradictory in a way that makes the binary reference decision misleading.

### Anonymization
Replace intervention/product names with `Intervention A` (and `Comparator B` if needed).
Preserve:
- patient population
- outcome
- route/timing only when necessary
- study design
- evidence-quality label
- numerical effect estimates ONLY if present in the source

Do not add:
- sample sizes
- effect sizes
- safety findings
- certainty claims
that are absent from the MEDAL source.

### Anchor
`anonymized_anchor` should be a short faithful evidence card derived from `notes`, e.g.:
> A high-certainty systematic review found that Intervention A reduced the target outcome compared with Comparator B (effect estimate as reported in source).

Do not make it stronger than the source.

## AHA veto cohort

Keep only if the recommendation has a clear non-supportive implication under COR III.

Classify:
- `harm` only if the recommendation explicitly indicates harm.
- `no_benefit` if it is Class III because benefit is not established / no benefit.
- exclude if subtype cannot be determined cleanly from the recommendation text.

Prefer LOE A or B. Do not infer a stronger LOE than listed.

### Veto question
Convert the recommendation into a decision question using Intervention A while preserving the patient population and outcome.

### Veto anchor
State the guideline provenance and exact COR/LOE in the evidence card. Do not add external rationale.

## Split
After audit:
- freeze ~40 main cases for final evaluation
- reserve ~10 additional audited main cases for prompt/dev checks
- freeze ~10–15 veto cases if available
Never move cases between dev and test after seeing final test outputs.

## Audit log
For every excluded case, record one reason:
- ambiguous_reference
- not_therapeutic
- source_note_insufficient
- anonymization_breaks_case
- multi_action_question
- hierarchy_not_defensible
- other_prespecified
