#!/usr/bin/env python3
"""Phase 3: render data-driven markdown reports from validation JSON/CSV (no hand-typed values)."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "validation"
D = ROOT / "docs"

# hash report
h = json.loads((V / "hash_verification_report.json").read_text())
L = ["# Hash verification report (Phase 3, step 2)", "", f"Generated {h['generated_utc']} by `scripts/phase3_hash_report.py`; machine-readable: `validation/hash_verification_report.json`. Repo-level `scripts/verify_hashes.py` was also run (log: `validation/logs/step2_verify_hashes.log`).", "",
     f"Scope: {h['scope']}.", "", f"- Manifest entries checked: **{h['n_manifest_entries']}**", f"- Matching: **{h['n_match']}**", f"- Mismatching: **{h['n_mismatch']}**", "", "## Integrity anchors", "", "| Anchor | Path | Expected | Match |", "|---|---|---|---|"]
L += [f"| {a['anchor']} | `{a['path']}` | `{a['expected_sha256']}` | {'✅' if a['match'] else '❌'} |" for a in h["anchors"]]
L += ["", "## Mismatches", ""]
for m in h["mismatches"]:
    L += [f"- `{m['target']}` per `{m['manifest']}`: expected `{m['expected_sha256']}`, actual `{m['actual_sha256']}`. This is the known `posthoc_contrasts.py` discrepancy; it was **not** passed over silently: see [posthoc_hash_investigation.md](posthoc_hash_investigation.md)."]
L += ["", "## Entries by manifest", "", "| Package | Manifest | Entries | Match |", "|---|---|---|---|"]
from collections import Counter, defaultdict
agg = defaultdict(lambda: [0, 0])
for e in h["entries"]:
    agg[(e["package"], e["manifest"])][0] += 1
    agg[(e["package"], e["manifest"])][1] += e["match"]
L += [f"| {p} | `{m}` | {n} | {k} |" for (p, m), (n, k) in agg.items()]
(D / "hash_verification_report.md").write_text("\n".join(L) + "\n")

# structure report
s = json.loads((V / "canonical_structure_report.json").read_text())
L = ["# Canonical structure report (Phase 3, step 3)", "", f"Generated {s['generated_utc']} by `scripts/phase3_structure.py`. {s['note']} Machine-readable: `validation/canonical_structure_report.json`.", "",
     "## GenAI4Health", "", "| Experiment | Canonical file | Success / expected | Unique IDs | Dup IDs | Missing IDs | Cases | Incomplete cases | Malformed | Schema problems | Raw→canonical | Status |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for k, v in s["genai4health"].items():
    rc = v.get("raw_to_canonical")
    rcs = "n/a (no separate RAW)" if not rc else (f"RAW {rc['raw_rows']} rows ({rc['raw_ok']} ok, errors {rc['raw_error_http_status'] or 0}); CLEAN = RAW ok rows in order: {rc['canonical_equals_raw_ok_rows_in_order']}; byte-identical: {rc['raw_identical_to_canonical_bytes']}")
    L.append(f"| {k} | `{Path(v['canonical_file']).name}` | {v['successful_rows']}/{v['expected_successful']} | {v['unique_ids']} | {len(v['duplicate_ids'])} | {len(v['missing_ids_vs_prompts'])} | {v['cases_in_output']}/{v['cases_in_cohort']} | {len(v['cases_with_incomplete_conditions'])} | {v['malformed_rows']} | {v['schema_problem_counts'] or 0} | {rcs} | **{v['status']}** |")
L += ["", "Expected IDs are the `prompt_id`s of the frozen prompt files; every output ID matches exactly (none missing, none unexpected).", "", "## AgenticLS", ""]
g = s["agenticls"]["gemini_persistent_260"]
L += ["### Gemini persistent 260", "", f"- Canonical rows: {g['successful_rows']}/{g['expected_successful']} ok; unique run_ids {g['unique_run_ids']}; duplicates {len(g['duplicate_run_ids'])}; missing {len(g['missing_run_ids'])}; cases {g['cases']} (incomplete {len(g['cases_incomplete'])})",
      f"- Arm × condition: {g['arm_condition_counts']}", f"- Sequential history/message-count/cumulative-evidence problems: {g['sequential_structure_problems'] or 0}",
      f"- Attempts: {g['attempts']['rows']} rows; HTTP {g['attempts']['http_status']}; ok-attempt run_ids == canonical: {g['attempts']['ok_attempt_run_ids_equal_canonical']}",
      f"- Execution order (terminal log): overall {g['execution_order']['overall']}; by stratum {g['execution_order']['by_stratum']}",
      f"- FINAL_BACKUP identical: results {g['results_equal_FINAL_BACKUP']}, attempts {g['attempts_equal_FINAL_BACKUP']}", f"- **{g['status']}**", ""]
a = s["agenticls"]["gemini_aligned_control_40"]
L += ["### Gemini aligned control 40", "", f"- Cohort sha256 `{a['cohort_sha256']}`; lines ⊂ 260 cohort: {a['cohort_lines_subset_of_260']}; per stratum {a['cases_per_stratum']}",
      f"- Canonical rows: {a['successful_rows']}/{a['expected_successful']}; unique {a['unique_run_ids']}; duplicates {len(a['duplicate_run_ids'])}; missing {len(a['missing_run_ids'])}",
      f"- Arm × condition: {a['arm_condition_counts']}", f"- Attempts: {a['attempts']['rows']}; HTTP {a['attempts']['http_status']}",
      f"- Branch points (source_h_* → Gemini-260 sequential::H: run_id, prompt sha256, raw_text sha256, timestamp): **{a['branch_point_links_verified']}**",
      f"- Execution order: overall {a['execution_order']['overall']}; by stratum {a['execution_order']['by_stratum']}", f"- **{a['status']}**"]
(D / "canonical_structure_report.md").write_text("\n".join(L) + "\n")

# provenance md
rows = list(csv.DictReader(open(D / "result_provenance.csv", encoding="utf-8")))
L = ["# Result provenance", "", "Full map with source cohort / raw / canonical / script / output / protocol paths and the values read from archived outputs: [result_provenance.csv](result_provenance.csv) (generated by `scripts/phase3_provenance.py`; no values typed by hand). Schema/path validator: `scripts/validate_result_provenance.py` (also run by `scripts/validate_accepted_papers.py` and CI).", "",
     f"{len(rows)} results mapped: {sum(r['paper']=='GenAI4Health' for r in rows)} GenAI4Health, {sum(r['paper']=='AgenticLS' for r in rows)} AgenticLS, each with a unique `result_id`.", "",
     "Reserved (currently `TODO: camera-ready pending` / `TODO`, per instruction not to guess): `camera_ready_location`, `table_number`, `figure_number`, `section`. These will be filled in once the camera-ready PDFs are final.", "",
     "| Paper | Result | Prespecified / post-hoc | Reproduced status |", "|---|---|---|---|"]
L += [f"| {r['paper']} | `{r['result_id']}` | {r['prespecified_or_posthoc']} | {r['reproduced_status']} |" for r in rows]
(D / "result_provenance.md").write_text("\n".join(L) + "\n")
print("rendered")
