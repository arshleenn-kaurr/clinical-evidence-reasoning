# Final paper metadata (camera-ready, as printed)

Recorded exactly as printed in the ingested camera-ready PDFs. Absent fields are `null`/unknown, never inferred. Machine-readable copies: `papers/<paper>/paper/metadata.json`.

## AgenticLS — CAMERA-READY INGESTED / VERIFIED

| Field | Value (as printed) |
|---|---|
| Title | Stable Decisions Can Hide Evidence Sensitivity in Life-Science Evidence Synthesis |
| Author order | 1. Manav Vohra; 2. Arshleen Kaur |
| Affiliation lines (both authors, as printed) | Independent Researcher / Ernest Mario School of Pharmacy / Rutgers University |
| Emails | printed on the title page of the PDF; deliberately not recorded in this public repository (author decision) |
| Workshop | AgenticLS: Life-Science Agents Workshop |
| Conference / year | NeurIPS 2026 (footer on p.1: "AgenticLS: Life-Science Agents Workshop, NeurIPS 2026.") |
| "Accepted" / camera-ready footer wording | none printed (`null`) |
| Full conference name ("Conference on Neural Information Processing Systems") | not printed (`null`) |
| DOI / OpenReview / arXiv / proceedings / pages | none printed (`null`) |
| Pages | 12 (main text pp.1–5, references pp.5–6, appendices pp.7–12) |
| Author note (p.5) | states authors are Doctor of Pharmacy Candidates at Ernest Mario School of Pharmacy, Rutgers University; work conducted independently |
| Ingested file | `papers/agenticls/paper/agenticls-camera-ready.pdf` |
| SHA256 | `1b7311a7f7c563b50dbbd10c59d665b87881b8a3e9c2058c60ff28bcb72758e5` (273,393 bytes) |
| Source path / ingestion | `~/Downloads/AgenticLS_CameraReady.pdf` (full local path: non-public log `validation/logs/camera_ready_ingestion_agenticls.json`); ingested 2026-10-04 (UTC timestamp in metadata.json) |
| Identity verification | first-page text (title, authors, workshop footer), not filename |
| Numbered tables | none; one numbered figure (Figure 1) |
| Redistribution permission for the PDF | **NOT ESTABLISHED** (see `docs/public_v1_scope.md`) |
| Revision history | This is the corrected version (Methods/App. D.4 bootstrap sentence; App. B five→four; `docs/camera_ready_approved_revisions.md`). The earlier PDF (`30e8f4e65cd3a095c787f34caa3bc24963ba9413c6d0524a59b69a60d181285e`) is superseded provenance only (listed in `metadata.json`). |

Note: an earlier `AgenticLS.pdf` draft in the same download folder carries different author contact and affiliation lines. It was **not** used as an authority and was not ingested.

## GenAI4Health — CAMERA-READY PENDING

The only PDF available at ingestion time (`GenAI4Health.pdf`) is the **anonymized submission** ("Anonymous Author(s)"; footer "Submitted to 40th Conference on Neural Information Processing Systems (NeurIPS 2026). Do not distribute."). It was not ingested, and no title, author, affiliation, workshop or number is recorded as final. The title in `CITATION.cff` is the submission title, flagged as unverified against the final camera-ready.

Next action: authors supply the final camera-ready path, then run `scripts/ingest_camera_ready.py --paper genai4health … --apply`, `scripts/audit_camera_ready_numbers.py` (a GenAI4Health claim table must be added), `scripts/build_camera_ready_mapping.py`.
