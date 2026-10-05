# Camera-ready claim-scope audit

Scope: wording in the ingested camera-ready PDFs checked against the documented scope limitations of this repository. **The papers were not edited.** Short fragments are quoted only to locate wording for author review.

## AgenticLS (`papers/agenticls/paper/agenticls-camera-ready.pdf`, SHA256 `1b7311a7…2758e5`)

Method: full-text keyword sweep (calibrat*, causal, isolat*, autonomous, safety, Groq, latent, public, release, availab*, code, anchoring, belief, establish/prove/show) plus a read of Abstract, Discussion/Limitations and Appendices C–E. Result: **no wording was found that violates a documented scope limit**; each risk area is explicitly disclaimed in the paper. Items 1–3 below are low-severity observations for author attention, none requires a change for repository consistency.

| # | Risk area | Finding | Evidence (short fragments) | Status |
|---|---|---|---|---|
| 1 | Confidence treated as calibrated uncertainty | Explicitly disclaimed in Abstract, Methods, Limitations | "do not interpret self-reported confidence as calibrated uncertainty" | OK |
| 2 | Dominant-evidence IDs as causal evidence use | Explicitly disclaimed (Abstract, App. E.4); always phrased "reported dominant evidence" | "source attribution as a causal measurement" | OK |
| 3 | Persistent experiment isolating evidence arrival only | Disclaimed repeatedly. One discussion sentence is slightly more attributive than the disclaimers around it | Discussion: "depending on how that evidence accumulated" vs. Methods/App. C.2: "does not isolate a causal effect of evidence arrival" | **Author review (low):** consider whether "accumulated" should carry the joint-factor qualifier (history + prior outputs) at that sentence |
| 4 | Benchmark tests autonomous evidence-quality inference | Disclaimed | "instructed hierarchy rather than autonomous evidence-quality appraisal" | OK |
| 5 | Small veto set proves clinical safety | Disclaimed | "does not establish clinical safety" | OK |
| 6 | Groq persistent extension part of accepted AgenticLS work | **Not claimed.** The paper mentions Groq only for the *static* GPT-OSS-120B sensitivity (App. E.6, "evaluated post hoc through the Groq API on the frozen 40-case primary cohort"). Persistent-context results are Gemini only ("the principal persistent-context comparison used only Gemini-3.6-flash") | | OK. Repository docs must keep distinguishing the **static** GPT-OSS/Groq runs (in the accepted paper) from the **persistent** Groq extension (not in it) |
| 7 | latent-v1 included in reported evidence | **Not claimed.** Only latent-v2 appears (App. E.7), consistent with latent-v1 being SUPERSEDED / EXCLUDED | "Latent-v2 was a post-hoc analysis" | OK |
| 8 | Restricted data fully public | The paper makes **no** data/code availability or release statement; cites SHA256 of frozen files (cohort, aligned subset) | | OK. Nothing in the paper conflicts with the withheld `LICENSE_REVIEW` files |
| 9 | Over-strong verbs ("prove", "demonstrate") | None. "establish" appears only as "establish a bounded behavioral finding" and in negations ("does not establish …") | | OK |

### Process/design statements that artifacts cannot verify (not numeric; flagged, not changed)

- "Replication membership was fixed before aggregate primary results were inspected" and "The subset was frozen before any aligned-control outcomes were generated or inspected" — consistent with freeze dates in the manifests (aligned freeze 2026-09-23, aligned outputs timestamped later the same day), but the ordering of *inspection* is attestation by the authors.
- "Eligibility review was performed by a single reviewer" — author attestation.
- Pre-specification labelling ("The within-case confidence change from H to H+L4 was also prespecified"): the CI printed in the text ([−5.13, −4.16]) equals the **post-hoc** bootstrap of that contrast, while the separately archived prespecified `confidence_shift.csv` records [−5.1269, −4.1462] (differs at the 2nd decimal of the upper bound; same pattern for primary −6.50 vs −6.375 and GPT-OSS −4.68 vs −4.725). Point estimates agree. Author may wish to state which bootstrap run the printed interval comes from. Not a numeric mismatch of the headline value.

### Reproducibility statements vs. the post-hoc script-hash disclosure

The paper contains **no** reproducibility/code-availability statement and does not claim byte-for-byte or script-hash-level reproducibility, so nothing in it conflicts with the approved disclosure ("…earlier script hash that is no longer available…"). The disclosure is present verbatim in `README.md` and `docs/posthoc_hash_investigation.md` and in expanded (hash-annotated) form in `docs/limitations.md`. It was **not** inserted into the paper.

### One methods statement that does conflict with the archive (see number audit)

App. D.4 / Methods: "Paired confidence intervals used 10,000 case-level bootstrap resamples." The persistent-260 terminal CI (headline [−13.02, −11.62]) was produced with **100,000** resamples (`analyze_sequential_gemini.py`, `B=100000`; `docs/result_provenance.csv`; `papers/agenticls/reproduce.md`). All other intervals used 10,000. The printed interval values reproduce exactly; only the global resample-count sentence is inaccurate for that one analysis. **Resolved**: the authors revised the manuscript (`docs/camera_ready_approved_revisions.md`, Revision 1); the current PDF states that the persistent-vs-fresh terminal comparison used 100,000 resamples and the other paired CIs 10,000, in both Methods and Appendix D.4. Verified by the audit (`agl.method.boot_resamples`).

## GenAI4Health

**Not audited — CAMERA-READY PENDING.** Only the anonymized submission was available; it is not an authority and was not ingested. Nothing is asserted about the final wording.
