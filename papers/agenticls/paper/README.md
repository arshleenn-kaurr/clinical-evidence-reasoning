# paper/ — AgenticLS

**CAMERA-READY INGESTED / VERIFIED** (revised version; the earlier PDF is superseded provenance only)

| | |
|---|---|
| Title | Stable Decisions Can Hide Evidence Sensitivity in Life-Science Evidence Synthesis |
| Authors (printed order) | Manav Vohra; Arshleen Kaur |
| Affiliation (as printed) | Independent Researcher; Ernest Mario School of Pharmacy, Rutgers University |
| Venue | AgenticLS: Life-Science Agents Workshop, NeurIPS 2026 |
| PDF | `agenticls-camera-ready.pdf` |
| PDF SHA256 | `1b7311a7f7c563b50dbbd10c59d665b87881b8a3e9c2058c60ff28bcb72758e5` |
| DOI / URLs | none supplied (none recorded) |

Metadata as printed: [`metadata.json`](metadata.json), [`../../../docs/final_paper_metadata.md`](../../../docs/final_paper_metadata.md).

**Immutable:** the ingested PDF must not be modified; its hash is the reference for the tag-freeze manifest.

**Public redistribution of the PDF is not yet authorized** (workshop/author permission not established); it is classified `PUBLIC_RELEASE_PENDING_PERMISSION` and excluded from the public preview.

## Relationship to the repository experiments

Static benchmark (260-case Gemini replication, six conditions, GPT-OSS/latent-v2/veto sensitivity), Gemini persistent-context 260, and the Gemini aligned control 40. The Groq GPT-OSS persistent extension is **not** part of this paper. See [`../reproduce.md`](../reproduce.md).

## Reproducibility

```bash
python scripts/validate_accepted_papers.py      # full archival reproduction, no API calls
python scripts/validate_public_release.py       # public-artifact validation
python scripts/audit_camera_ready_numbers.py    # manuscript numbers vs reproduced artifacts (needs pypdf)
python scripts/validate_camera_ready_mapping.py
```

## Provenance mapping and number audit status

- Mapping: [`../../../docs/camera_ready_provenance_mapping.csv`](../../../docs/camera_ready_provenance_mapping.csv); claims without a `result_id`: [`../../../docs/camera_ready_unmapped_claims.csv`](../../../docs/camera_ready_unmapped_claims.csv).
- Number audit: [`../../../docs/camera_ready_number_audit.md`](../../../docs/camera_ready_number_audit.md) — all reported result values match; audit status **PASS** (two author-approved wording corrections are applied in this PDF: [`../../../docs/camera_ready_approved_revisions.md`](../../../docs/camera_ready_approved_revisions.md)).
- Claim-scope audit: [`../../../docs/camera_ready_claim_scope_audit.md`](../../../docs/camera_ready_claim_scope_audit.md).
