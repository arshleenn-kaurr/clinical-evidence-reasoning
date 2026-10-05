# Public identity and email review

Status: **RESOLVED (2026-10-04, author decision):** repo-level authors confirmed as Manav Vohra and Arshleen Kaur (affiliation: Independent Researcher; Ernest Mario School of Pharmacy; Rutgers University; no ORCIDs or extra affiliations); the two Rutgers email addresses were **removed** from the public tree (option 2 below), names and affiliations retained; the emails remain only in the camera-ready PDF, which is excluded from the public build. Commit identity stays a placeholder until the authors supply it. The sections below record the pre-decision audit. Nothing was removed or changed by this review. Scan date 2026-10-04, run over the manifest tiers and over the built `dist/public_v1_preview/` tree (the tree that would actually become the public repository).

Repo-level authors currently recorded (`CITATION.cff`, AgenticLS paper metadata): **Manav Vohra** and **Arshleen Kaur**, affiliation as printed in the AgenticLS camera-ready: *Independent Researcher; Ernest Mario School of Pharmacy, Rutgers University*. No existing verified repository metadata says otherwise. `pyproject.toml` lists no authors. No ORCID is recorded anywhere.

## 1. INTENDED PUBLIC IDENTITY (names and affiliation)

Paper authorship is already public through the accepted workshop paper, and a citation file needs it. These files in the v1 public tree name the authors and/or affiliation:

| File | Manav Vohra | Arshleen Kaur | Rutgers / Ernest Mario affiliation | Purpose |
|---|:-:|:-:|:-:|---|
| `CITATION.cff` | yes | yes | yes | repo authors + AgenticLS reference |
| `papers/agenticls/README.md` | yes | yes | no | paper summary |
| `papers/agenticls/paper/README.md` | yes | yes | yes | PDF status / provenance |
| `papers/agenticls/paper/metadata.json` | yes | yes | yes | verified camera-ready metadata |
| `docs/final_paper_metadata.md` | yes | yes | yes | verified camera-ready metadata |
| `docs/zenodo_metadata_draft.json` | yes (as "Vohra, ...") | yes | yes | draft deposit metadata (not uploaded) |
| `docs/github_release_metadata.md` | yes | yes | no | README citation line |
| `docs/github_v1_release_notes.md` | yes | yes | no | release notes draft |
| `docs/final_release_checklist.md` | yes | yes | yes | checklist items |
| `docs/phase5b_finalization_report.md` | yes | yes | yes | finalization report |

Decision needed from the authors: confirm that the two names and this affiliation string are what should appear as repo-level authors and in these files. Nothing needs to change if so.

## 2. OPTIONAL EMAIL DISCLOSURE — RESOLVED: option 2 (removed)

The two Rutgers email addresses printed on the AgenticLS title page appear in exactly **two** files of the public tree:

- `papers/agenticls/paper/metadata.json` (field `email_as_printed`, one per author)
- `docs/final_paper_metadata.md` (one row listing both)

They are not in `CITATION.cff`, `README.md`, the Zenodo draft, or any other public file. Options:

1. Keep them (they are already printed in the public paper; useful for contact).
2. Remove them from both files and keep only names/affiliation. Reproduction questions then go through GitHub Issues. (Lowest exposure; recommended if there is any doubt, since a repository is crawled and scraped far more than a PDF.)
3. Replace them with one contact address the authors choose.

If option 2 or 3 is chosen, the two files, `MANIFEST.csv`, `docs/tag_freeze_manifest.json` and the manifest/scope files need regeneration (the standard rebuild order in `docs/git_initialization_plan.md`).

## 3. ARCHIVAL-ONLY OCCURRENCES (not in any public build)

- `validation/logs/camera_ready_ingestion_agenticls.json` records the full local source path of the ingested PDF (contains a local username). Classified `ARCHIVAL_ONLY`.
- Operational logs under `validation/logs/` and `validation/public_preview_validation/logs/` and the Groq `nohup.out` contain the local home-directory path (`ARCHIVAL_ONLY`).
- The camera-ready PDF itself (title page names, affiliations and emails) is `PUBLIC_RELEASE_PENDING_PERMISSION` and excluded.
- One incidental hit: `Kaur` occurs inside a random base64-like string in a `LICENSE_REVIEW` provider-output file (not a name; not public).

`scripts/validate_public_release.py` checks for local-home-directory paths in the public tree; it reports none.

## 4. Not exposed

No phone numbers, postal addresses, personal accounts, ORCIDs, or the user's personal (non-Rutgers) email appear in the public tree. Git commit identity (`user.name` / `user.email`) is a separate exposure: whatever the authors configure for the first commit becomes public in history. Use an address you are willing to publish (a GitHub no-reply address is the conservative choice). It is a placeholder in `docs/git_initialization_plan.md`.
