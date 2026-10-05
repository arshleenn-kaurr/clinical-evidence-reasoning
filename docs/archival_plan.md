# Archival plan (GitHub → Zenodo → DOI)

Plan only. **Nothing has been uploaded anywhere.** No DOI is invented anywhere in this document — every DOI field below is explicitly `TODO`.

## Proposed flow

```
GitHub release (tag, e.g. v1.0.0) → Zenodo archive (GitHub-Zenodo integration, or manual deposit) → DOI minted by Zenodo
```

Zenodo's standard GitHub integration mints a new DOI automatically whenever a new GitHub Release is published for a connected repository, and (notably) can mint a single **concept DOI** that always resolves to the latest version, plus a **version-specific DOI** per release. This maps naturally onto the tag structure in `docs/release_strategy.md`.

## Is a repo-level DOI useful?

**Yes, recommended** — a repo-level (concept) DOI gives the code+archive a single, stable, citable identifier independent of which version someone used, which is standard practice for research-software citation (and what `CITATION.cff` is designed to hold). TODO once minted: fill in `CITATION.cff`'s `repository-code` / `doi` fields — currently omitted, not guessed.

## Should paper-specific releases each get versioned DOIs?

**Recommended: yes**, following the three-tag structure in `docs/release_strategy.md`:
- `v1.0.0` → one version-specific DOI (the general reproducibility-archive citation).
- `genai4health-2026-camera-ready` → a second version-specific DOI, so a reader of the GenAI4Health paper can cite the exact artifact state the paper describes, independent of later repo changes.
- `agenticls-2026-camera-ready` → a third version-specific DOI, same reasoning for AgenticLS.

All three can share the same Zenodo **concept DOI** (so they're grouped as versions of one archived work) while each also getting its own **version DOI** for precise citation. This is Zenodo's default behavior for a GitHub-connected repository with multiple releases.

## What files should be included in archival release assets

Per `docs/release_strategy.md`:
- `v1.0.0`: the `V1_CORE` + `V1_SUPPORTING` scope (`dist/public_v1_preview/` contents, i.e. what `scripts/build_public_release.py --v1-core` produces), zipped or as the GitHub-generated source archive of that tag.
- Each `<paper>-2026-camera-ready` tag: that paper's camera-ready PDF (Step 9's ingestion target) as an explicit release asset, plus optionally a scoped subset archive of just that paper's `experiments/`/`papers/` subtree.
- **Never** a `LICENSE_REVIEW` or `ARCHIVAL_ONLY` file, regardless of tag — the same exclusion that applies to the GitHub release applies to any Zenodo deposit built from it, since Zenodo archives whatever the GitHub release asset contains.

## How restricted artifacts should be handled

Not included in any archival release asset until `docs/licensing_decision_matrix.md`'s `UNKNOWN` dispositions are resolved. If/when some are cleared (`PUBLIC_IF_CLEARED`), they would be added to a later release, not retroactively inserted into an already-archived DOI'd version (Zenodo versions are immutable once minted — a correction or addition becomes a new version with its own DOI, which is itself consistent with how this repository already treats every artifact: never edit in place, always a new file/version).

## How to cite the code/artifact vs. the papers

Two separate things, already distinguished in `CITATION.cff`'s structure (top-level entry = this repository/software; `references` list = the two papers):
- **Citing the software/archive**: cite the Zenodo DOI (once minted) or the GitHub repo + commit/tag, via `CITATION.cff`'s top-level fields.
- **Citing a paper**: cite the paper's own eventual DOI/proceedings citation (NeurIPS workshop proceedings, once camera-ready — see `docs/release_strategy.md` Step on camera-ready ingestion), via `CITATION.cff`'s `references` entries, **not** the repository DOI. The repository DOI is for "I reproduced/built on this code," the paper citation is for "I'm citing this finding."

## How CITATION.cff should relate to Zenodo metadata

Zenodo reads `CITATION.cff` automatically when present in a GitHub-connected repository and uses it to pre-populate the deposit's metadata (title, authors, version, date). This means:
- `CITATION.cff`'s `authors` field (currently `TODO`/`TODO` placeholder) should be finalized **before** the first Zenodo deposit, since Zenodo will otherwise either show the placeholder or require manual correction on Zenodo's side (which then diverges from the repo's own file — better to fix it once, upstream).
- Once a DOI exists, `CITATION.cff` should be updated to **include** it (`identifiers` field, `doi` type) — a one-time addition after the first Zenodo deposit, not before.

## Explicitly not done in this phase

No GitHub release was created. No Zenodo deposit was made. No DOI was invented, guessed, or reserved. `CITATION.cff` was not changed by this document (its placeholders remain exactly as Phase 4 left them).
