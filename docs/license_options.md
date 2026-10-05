# Software/repository license options

**DECISION RECORDED (2026-10-04): the authors selected MIT** (Copyright (c) 2026 Manav Vohra and Arshleen Kaur); see `LICENSE`. `LICENSE-TODO.md` was replaced. The rest of this document is the pre-decision comparison, kept for provenance. The MIT license covers project-authored code only and grants no rights to the withheld data, provider outputs, `LICENSE_REVIEW` artifacts or paper PDFs. The comparison below is neutral; the advisory section at the end gives a non-binding recommendation and selects nothing.

## Comparison: MIT, Apache-2.0, BSD-3-Clause

| | MIT | Apache-2.0 | BSD-3-Clause |
|---|---|---|---|
| **Permissiveness** | Very high — minimal conditions beyond preserving the notice/license text | High — same core permissions as MIT, plus more formal structure | Very high — equivalent to MIT with an added non-endorsement clause |
| **Patent terms** | None — silent on patents | Explicit express patent grant from contributors, with a patent-litigation retaliation clause (terminates the grant if you sue over patents) | None — silent on patents |
| **Attribution requirements** | Preserve copyright notice + license text in copies | Preserve copyright notice, license text, and a `NOTICE` file if the project has one; must state changes made to modified files | Preserve copyright notice + license text in copies; the "3-clause" also bars using contributors' names to endorse derived products without permission |
| **Suitability for research code** | Common, simple, widely understood by other researchers/institutions | Common in larger or corporate-adjacent projects; the explicit patent grant is attractive if any method here might be patentable or used by industry | Common in academic/scientific software (e.g. much of the scientific Python stack uses BSD); the non-endorsement clause suits an academic lab's name | 
| **Interaction with restricted/third-party data** | None of these licenses say anything about data — they are code licenses. A code license, whichever is chosen, **does not grant any rights to the `LICENSE_REVIEW` data files** (Cochrane/AHA-derived cohorts, prompts, raw model outputs). That must be handled separately (see below). | | |
| **Risk of being misread as covering data/artifacts** | Moderate: a bare top-level `LICENSE` file with no further explanation invites readers to assume "the whole repo is MIT," including the JSONL data files sitting next to the code. This repository already mitigates part of that risk structurally (data under `LICENSE_REVIEW` is excluded from any public release build by `scripts/build_public_release.py` regardless of which code license is chosen), but the **documentation structure below is still recommended** so a human skimming the repo doesn't have to infer the distinction from the manifest. | | |

None of the three is unsuitable; the choice is a matter of institutional preference (e.g. does the authors' university or funder have a house style, does patent language matter here, is BSD's academic convention preferred). This is explicitly left to the authors.

## Recommended structural approach (not a license choice)

Regardless of which code license is eventually chosen, this document recommends the repository **distinguish three separate things** that a single `LICENSE` file conflates by convention:

| File | Covers | Status |
|---|---|---|
| `LICENSE` (once chosen) | **Code only**: everything in `scripts/`, `src/`, `tests/`, the frozen runners/analysis code inside `historical_package/` | TODO — currently `LICENSE-TODO.md` placeholder |
| `DATA_LICENSE_NOTICE.md` | **Data/artifacts**: frozen cohorts, prompts, raw/canonical model outputs, and anything else classified `LICENSE_REVIEW` in `docs/public_release_manifest_draft.csv` — explicitly states these are NOT covered by the code license and are under separate, unresolved review | Draft created this phase: see `DATA_AND_ARTIFACT_RIGHTS.md` (this repo's version of that file — see Step 12) |
| `THIRD_PARTY_NOTICES.md` | **Third-party/upstream material**: MEDAL, Cochrane, AHA attributions; provider (Gemini/Groq) output notices | Draft created this phase |

A reader (or a legal reviewer) should be able to open any one of these three and immediately know its scope, rather than having to reverse-engineer "does the MIT/Apache/BSD text at the repo root also apply to this JSONL file?" The manuscripts themselves (paper PDFs, once added under `papers/*/paper/`) are **paper copyright**, a fourth, separate thing — governed by the workshop/publisher's own copyright policy, not by any file in this repository.

## What this document does NOT do

- It does not select MIT, Apache-2.0, or BSD-3-Clause (the advisory section names a preference; the decision is the authors').
- It does not claim any of the three is better in general; the advisory section above is a non-binding view for this repository only.
- It does not resolve the `LICENSE_REVIEW` data question (see `docs/licensing_decision_matrix.md`) — that is independent of which code license is eventually chosen.

## Advisory recommendation (non-binding; nothing is selected)

*(Written before the decision; the authors chose the preferred option.)* Fit to this repository: academic reproducibility tooling and analysis code, authored by two people, reused by researchers and possibly companies, sitting next to third-party-governed data that no code license can cover.

| Candidate | Main advantage | Main downside | Recommended here? |
|---|---|---|---|
| **MIT** | Shortest, best-known permissive license; no friction for researchers or companies; matches most ML research code | No explicit patent grant; no NOTICE mechanism | **Yes — preferred** |
| **Apache-2.0** | Explicit patent grant and NOTICE file; strongest clarity for company reuse | Longer; NOTICE/state-changes obligations; patent clause is of little practical value for evaluation scripts | Acceptable alternative if the authors or their institution want the patent language |
| **BSD-3-Clause** | Academic convention; non-endorsement clause protects author/institution names | Slightly less familiar outside science; the endorsement clause adds little for a small repo | Not preferred (no benefit over MIT here) |

**Preferred: MIT**, because the repository is small research/tooling code with no patent-sensitive method, and simplicity maximizes reuse. Check first whether the Rutgers affiliation imposes any institutional policy on code licensing; that, not the technical comparison, may decide it.

Whichever license is chosen, keep the structural split above: the `LICENSE` text must be accompanied by a short scope statement (README/`DATA_AND_ARTIFACT_RIGHTS.md`) that it covers **code only** and grants no rights to MEDAL/Cochrane/AHA-derived data, provider outputs, or paper PDFs. These notices already exist. Do not create `LICENSE` until the authors decide; the validator and docs currently expect `LICENSE-TODO.md` (see `docs/git_initialization_plan.md`, precondition 1).
