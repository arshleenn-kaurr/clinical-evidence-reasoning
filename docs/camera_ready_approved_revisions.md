# Approved manuscript revisions — AgenticLS (APPLIED in the current camera-ready)

Authorized by the authors on 2026-10-04. Result values, CIs and all archived artifacts are **unchanged**. The ingested PDF (`agenticls-camera-ready.pdf`, SHA256 `30e8f4e6…181285e`) is immutable and still contains the old wording; these edits must be made in the manuscript source by the authors and a **revised PDF supplied for re-ingestion** (`scripts/ingest_camera_ready.py --paper agenticls … --apply --force`, which changes the recorded SHA256 and requires re-running the audit, the mapping builder and `scripts/build_tag_freeze_manifest.py`).

## Revision 1 — bootstrap resample count (Methods, p.3; Appendix D.4, p.10)

- Old: "Paired confidence intervals used 10,000 case-level bootstrap resamples."
- **New:** "Paired confidence intervals used 10,000 case-level bootstrap resamples, except for the 260-case persistent-versus-fresh terminal confidence comparison, which used 100,000 resamples."
- Verified: `analyze_sequential_gemini.py` uses `B=100000` (persistent-260); static post-hoc and aligned-control analyses use 10,000. Persistent result (−12.32, [−13.02, −11.62]) unchanged.

## Revision 2 — anchors with an estimate but no interval (Appendix B, p.7)

- Old: "In five primary cases, the displayed point estimate favored the intervention despite a predefined do_not_support conclusion and no displayed interval; the stated systematic-review conclusion supplied the benchmark reference direction in these cases."
- **New:** "Among primary anchors with a quantitative estimate but no displayed interval, four had point estimates favoring the intervention despite a predefined do_not_support conclusion; in those cases, the stated systematic-review conclusion supplied the benchmark reference direction."
- Verified: five do_not_support primary anchors carry an estimate and no interval (C0006, C0032, C0034, C0044, C0046). C0006 (survival to hospital discharge, RR 0.58, 95% CI 0.12–2.74 — numbers confirmed in the archived audit notes; direction per the authors' external source verification) does not favor the intervention; the other four do. (The new sentence's population — anchors with an estimate but no interval — has five members in total, one of which does not favor the intervention, giving four.)

## Status: APPLIED

The authors corrected the manuscript and the revised PDF was ingested (dry-run first, `--force`) on 2026-10-04. Current camera-ready SHA256 `1b7311a7f7c563b50dbbd10c59d665b87881b8a3e9c2058c60ff28bcb72758e5`. The previous PDF (`30e8f4e65cd3a095c787f34caa3bc24963ba9413c6d0524a59b69a60d181285e`) is recorded **only as superseded provenance** in `papers/agenticls/paper/metadata.json` (`superseded_versions`); it is not retained in the repository and is not current. A word-level diff of the two PDFs' text shows only these two edits (plus layout reflow); no numeric result changed.

Audit result on the current PDF: both revisions `verified: true`, `applied_in_pdf: true`; the bootstrap sentence is present in both Methods (p.3) and Appendix D.4 (p.10); Appendix B (p.7) states four. AgenticLS audit status **PASS**.
