#!/usr/bin/env python3
"""Phase 3, steps 4-7: compare regenerated analysis outputs (validation/) with
archived outputs (historical packages). Read-only on archives.

Status vocabulary:
  EXACT_MATCH     byte-identical
  SEMANTIC_MATCH  parsed values identical, serialization differs
  NUMERIC_MATCH   all differences are numeric and <= 1e-12 absolute
  MISMATCH        any other difference
  NOT_REPRODUCIBLE / NOT_APPLICABLE  set by caller
Nothing is normalized silently: every differing cell/field is listed.
"""
import collections
import csv
import hashlib
import json
import math
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "validation"
S = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter"
G = ROOT / "experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential"
A = ROOT / "experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control"
TOL = 1e-12


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def num(x):
    try:
        f = float(x)
        return f if not math.isnan(f) else "nan"
    except (TypeError, ValueError):
        return None


def compare_csv(new, old):
    a = list(csv.reader(open(old, newline="", encoding="utf-8")))
    b = list(csv.reader(open(new, newline="", encoding="utf-8")))
    diffs = []
    if len(a) != len(b) or (a and b and a[0] != b[0]):
        return "MISMATCH", [{"reason": "shape/header differs", "archived_rows": len(a), "reproduced_rows": len(b)}]
    header = a[0]
    for i, (ra, rb) in enumerate(zip(a[1:], b[1:]), start=1):
        for j, (x, y) in enumerate(zip(ra, rb)):
            if x != y:
                diffs.append({"row": i, "column": header[j], "archived": x, "reproduced": y,
                              "abs_diff": abs(num(x) - num(y)) if isinstance(num(x), float) and isinstance(num(y), float) else None})
    if not diffs:
        return "SEMANTIC_MATCH", []
    if all(d["abs_diff"] is not None and d["abs_diff"] <= TOL for d in diffs):
        return "NUMERIC_MATCH", diffs
    return "MISMATCH", diffs


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def compare_json(new, old):
    a = dict(leaves(json.loads(Path(old).read_text())))
    b = dict(leaves(json.loads(Path(new).read_text())))
    fields = []
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k, "<absent>"), b.get(k, "<absent>")
        same = x == y and type(x) is type(y)
        d = abs(x - y) if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool) else None
        fields.append({"field": k, "archived": x, "reproduced": y, "equal": same, "abs_diff": d})
    bad = [f for f in fields if not f["equal"]]
    if not bad:
        status = "SEMANTIC_MATCH"
    elif all(f["abs_diff"] is not None and f["abs_diff"] <= TOL for f in bad):
        status = "NUMERIC_MATCH"
    else:
        status = "MISMATCH"
    return status, fields


def _display(p):
    p = Path(p)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def compare_file(new, old):
    rec = {"reproduced": _display(new), "archived": _display(old),
           "reproduced_sha256": sha(new), "archived_sha256": sha(old)}
    if rec["reproduced_sha256"] == rec["archived_sha256"]:
        rec["status"], rec["differences"] = "EXACT_MATCH", []
    elif str(new).endswith(".csv"):
        rec["status"], rec["differences"] = compare_csv(new, old)
    elif str(new).endswith(".json"):
        rec["status"], fields = compare_json(new, old)
        rec["differences"] = [f for f in fields if not f["equal"]]
    else:
        rec["status"], rec["differences"] = "MISMATCH", [{"reason": "non-CSV/JSON bytes differ"}]
    return rec


def env(python):
    return {"python": python}


# ---------------------------------------------------------------- step 4
def prespecified():
    out = {}
    for d in sorted((V / "genai4health/prespecified").iterdir()):
        files = {f.name: compare_file(f, S / "analysis" / d.name / f.name) for f in sorted(d.iterdir())}
        out[d.name] = {"files": files, "status": worst(r["status"] for r in files.values())}
    return out


ORDER = ["EXACT_MATCH", "SEMANTIC_MATCH", "NUMERIC_MATCH", "MISMATCH", "NOT_REPRODUCIBLE"]


def worst(statuses):
    return max(statuses, key=ORDER.index)


# ---------------------------------------------------------------- step 5
def r2(x, places="0.01"):
    return str(Decimal(repr(float(x))).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def canonical_reference_check(posthoc_dir, prespec_dir):
    text = (S / "analysis/canonical_results_reference.md").read_text(encoding="utf-8")
    rd = lambda n: list(csv.DictReader(open(posthoc_dir / n, encoding="utf-8")))
    props = {(r["cohort"], r["metric"]): r for r in rd("binomial_proportions_exact.csv")}
    contr = {(r["cohort"], r["contrast"]): r for r in rd("confidence_contrasts_bootstrap.csv")}
    dirs = {(r["cohort"], r["contrast"]): r for r in rd("confidence_direction_counts.csv")}
    strat = {r["stratum"]: r for r in rd("replication_conflict_aligned_by_stratum.csv")}
    degr = {(r["cohort"], r["contrast"]): r for r in rd("categorical_degradation_summary.csv")}
    mcn = {(r["cohort"], r["comparison"]): r for r in rd("paired_accuracy_mcnemar.csv")}
    anon = {r["subset"]: r for r in rd("anonymization_sensitivity.csv")}
    checks = []

    def add(section, key, ref, rep):
        checks.append({"section": section, "key": key, "reference_text": ref, "reproduced": rep, "match": ref == rep})

    section, cohort = None, None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if line.startswith("### "):
            cohort = line[4:].split()[0]
            continue
        s = line.strip()
        if not s:
            continue
        if section and section.startswith("1."):
            m = re.match(r"(\S+)\s+(\d+)/(\d+) = ([\d.]+)% \[([\d.]+), ([\d.]+)\]", s)
            if m:
                r = props[(cohort, m.group(1))]
                add("1", f"{cohort}/{m.group(1)}", list(m.groups()[1:]),
                    [r["numerator"], r["denominator"], r2(r["percent"]), r2(r["cp_lo"]), r2(r["cp_hi"])])
        elif section and section.startswith("2."):
            m = re.match(r"(\S+)\s+([+-][\d.]+) \[([+-][\d.]+), ([+-][\d.]+)\]\s+n=(\d+)\s+means ([\d.]+) vs ([\d.]+)\s+down/eq/up (\d+)/(\d+)/(\d+)\s+median ([+-]?[\d.]+)", s)
            if m:
                c, d = contr[(cohort, m.group(1))], dirs[(cohort, m.group(1))]
                sg = lambda x: ("+" if float(x) >= 0 else "") + r2(x)
                add("2", f"{cohort}/{m.group(1)}", list(m.groups()[1:]),
                    [sg(c["mean_difference"]), sg(c["boot_lo"]), sg(c["boot_hi"]), c["n_cases"], r2(c["mean_a"]), r2(c["mean_b"]),
                     d["n_decrease"], d["n_unchanged"], d["n_increase"],
                     # Reference file prefixes "+" on non-negative medians in this section (e.g. "+0.0").
                     ("+" if float(d["median_difference"]) >= 0 else "") + r2(d["median_difference"], "0.1")])
        elif section and section.startswith("3."):
            m = re.match(r"(.+?)\s+n=\s*(\d+)\s+([+-]?[\d.]+) \[([+-]?[\d.]+), ([+-]?[\d.]+)\]\s+(\d+)/(\d+)/(\d+)\s+median ([+-]?[\d.]+)", s)
            if m:
                r = strat[m.group(1).strip()]
                add("3", m.group(1).strip(), list(m.groups()[1:]),
                    [r["n"], r2(r["mean_conflict_minus_aligned"]), r2(r["ci_lo"]), r2(r["ci_hi"]), r["conflict_lower"], r["equal"], r["conflict_higher"], r2(r["median_difference"], "0.1")])
        elif section and section.startswith("4."):
            m = re.match(r"(\S+)\s+(H->\S+)\s+denom=\s*(\d+) total=(\d+) to_insufficient=(\d+) wrong_direction=(\d+) other=(\d+)", s)
            if m:
                r = degr[(m.group(1), m.group(2))]
                add("4", f"{m.group(1)}/{m.group(2)}", list(m.groups()[2:]),
                    [r["H_correct_denominator"], r["categorical_degradation_total"], r["to_insufficient"], r["wrong_direction_reversal"], r["other_change"]])
        elif section and section.startswith("5."):
            m = re.match(r"(\S+)\s+(\S+_vs_\S+)\s+p=([\d.]+)", s)
            if m:
                add("5", f"{m.group(1)}/{m.group(2)}", m.group(3), r2(mcn[(m.group(1), m.group(2))]["mcnemar_exact_p"], "0.001"))
        elif section and section.startswith("6."):
            m = re.match(r"(.+?)\s+n=\s*(\d+)\s+([+-]?[\d.]+) \[([+-]?[\d.]+), ([+-]?[\d.]+)\]", s)
            if m:
                r = anon[m.group(1).strip()]
                add("6", m.group(1).strip(), list(m.groups()[1:]), [r["n"], r2(r["mean_conflict_minus_aligned"]), r2(r["ci_lo"]), r2(r["ci_hi"])])
            m = re.match(r"excluded \((\d+)\): (.+)", s)
            if m:
                r = anon["excluded case ids"]
                add("6", "excluded case ids", [m.group(1), m.group(2)], [r["n"], r["case_ids"]])
        elif section and section.startswith("7."):
            m = re.match(r"(\S+)\s+n=\s*(\d+)\s+(\{.*\})", s)
            if m:
                folder = {"primary": "primary_gemini", "replication": "replication_gemini", "latent_v2": "latent_v2_gemini",
                          "veto": "veto_gemini", "gpt_oss_primary": "gpt_oss_primary", "gpt_oss_veto": "gpt_oss_veto"}[m.group(1)]
                rows = list(csv.DictReader(open(prespec_dir / folder / "flip_threshold.csv", encoding="utf-8")))
                counts = dict(collections.Counter(r["flip_threshold"] for r in rows))
                ref = eval(m.group(3), {"__builtins__": {}})  # literal dict printed in the reference file
                add("7", m.group(1), [m.group(2), ref], [str(len(rows)), counts])
    return checks


def posthoc():
    arch = S / "analysis/posthoc_contrasts"
    runs = {}
    for label, d in [("current_env_scipy_1.18.1", V / "genai4health/posthoc"),
                     ("sensitivity_env_scipy_1.16.3", V / "genai4health/posthoc_scipy1.16.3")]:
        files = {f.name: compare_file(f, arch / f.name) for f in sorted(d.iterdir())}
        csv_status = worst(r["status"] for n, r in files.items() if n != "manifest.json")
        runs[label] = {"files": files, "output_csvs_status": csv_status,
                       "manifest_differences": files["manifest.json"]["differences"]}
    checks = canonical_reference_check(V / "genai4health/posthoc", V / "genai4health/prespecified")
    return {
        "script": str((S / "posthoc_contrasts.py").relative_to(ROOT)),
        "recovered_script_sha256": sha(S / "posthoc_contrasts.py"),
        "manifest_script_sha256": json.loads((arch / "manifest.json").read_text())["script_sha256"],
        "runs": runs,
        "canonical_results_reference_md": {
            "file": str((S / "analysis/canonical_results_reference.md").relative_to(ROOT)),
            "sha256": sha(S / "analysis/canonical_results_reference.md"),
            "generator": "NOT RECOVERED (no recovered script writes this file)",
            "n_values_checked": len(checks), "n_match": sum(c["match"] for c in checks),
            "mismatches": [c for c in checks if not c["match"]], "checks": checks,
        },
    }


# ---------------------------------------------------------------- steps 6-7
def agenticls(name, new, old):
    rec = compare_file(new, old)
    status, fields = compare_json(new, old)
    rec["n_fields_compared"] = len(fields)
    rec["n_fields_equal"] = sum(f["equal"] for f in fields)
    rec["fields"] = fields
    return rec


def main():
    pre = prespecified()
    (V / "genai4health/prespecified_comparison.json").write_text(json.dumps(
        {"comparison": "score_results.py regenerated (scratch) vs archived analysis/<cohort>/", "cohorts": pre}, indent=2) + "\n")
    ph = posthoc()
    (V / "genai4health/posthoc_comparison.json").write_text(json.dumps(ph, indent=2) + "\n")
    g = agenticls("gemini_260", V / "agenticls/gemini_260_analysis.json", G / "results/gemini_260_analysis.json")
    (V / "agenticls/gemini_260_comparison.json").write_text(json.dumps(g, indent=2) + "\n")
    a = agenticls("aligned", V / "agenticls/aligned_control_analysis.json", A / "results/aligned_control_analysis.json")
    (V / "agenticls/aligned_control_comparison.json").write_text(json.dumps(a, indent=2) + "\n")
    for k, v in pre.items():
        print(f"prespecified {k}: {v['status']} ({len(v['files'])} files)")
    for k, v in ph["runs"].items():
        print(f"posthoc {k}: CSVs {v['output_csvs_status']}; manifest diffs: {[d['field'] for d in v['manifest_differences']]}")
    c = ph["canonical_results_reference_md"]
    print(f"canonical_results_reference.md: {c['n_match']}/{c['n_values_checked']} lines match")
    for m in c["mismatches"]:
        print("  REF MISMATCH", m)
    print(f"gemini_260: {g['status']} {g['n_fields_equal']}/{g['n_fields_compared']} fields equal")
    print(f"aligned_40: {a['status']} {a['n_fields_equal']}/{a['n_fields_compared']} fields equal")


if __name__ == "__main__":
    main()
