#!/usr/bin/env python3
"""RELEASE TOOLING / REPRODUCTION TOOLING (not historical execution code).

Single-command validation of the two accepted papers' archived artifacts and
analyses. No network access, no external model API calls. Runs:

  1. source hash verification (repo-level + accepted-paper manifests)
  2. canonical structure validation
  3. GenAI4Health prespecified + post-hoc analysis reproduction (scratch)
  4. AgenticLS persistent-260 analysis reproduction (scratch)
  5. AgenticLS aligned-control-40 analysis reproduction (scratch)
  6. comparison of regenerated vs archived outputs
  7. result-provenance (docs/result_provenance.csv) schema validation

All re-execution happens in a disposable scratch directory
(validation/_orchestrator_scratch/, recreated each run, gitignored) and
regenerated outputs are written under validation/ — never into any
historical_package/. Nothing under historical_package/ is read-write
checked here beyond hashing (read-only).

The Groq GPT-OSS persistent-context extension is explicitly OUT OF SCOPE:
this script never touches it.

Known documented provenance exception (does not fail validation, but is
always printed): the archived post-hoc analysis manifest records a
script_sha256 that no longer matches the recovered posthoc_contrasts.py.
See docs/posthoc_hash_investigation.md. The recovered script reproduces
every archived post-hoc output exactly under the pinned environment.

Exit code: 0 if all required accepted-paper reproducibility checks pass,
1 otherwise.

Usage: python scripts/validate_accepted_papers.py [--keep-scratch]
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S_HIST = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter"
G_HIST = ROOT / "experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential"
A_HIST = ROOT / "experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control"
SCRATCH = ROOT / "validation/_orchestrator_scratch"
V = ROOT / "validation"

COHORTS = {
    "primary_gemini": ("results/final_main_gemini_3_6_flash.jsonl", "data/final_main_cases.jsonl"),
    "replication_gemini": ("results/replication_gemini_3_6_flash_CLEAN.jsonl", "data/replication_cases.jsonl"),
    "veto_gemini": ("results/final_veto_gemini_3_6_flash.jsonl", "data/final_veto_cases.jsonl"),
    "gpt_oss_primary": ("results/final_main_gpt_oss_120b_CLEAN.jsonl", "data/final_main_cases.jsonl"),
    "gpt_oss_veto": ("results/final_veto_gpt_oss_120b_CLEAN.jsonl", "data/final_veto_cases.jsonl"),
    "latent_v2_gemini": ("results/latent_v2_main_gemini_3_6_flash_CLEAN.jsonl", "data/final_main_cases.jsonl"),
}


class Section:
    def __init__(self, title):
        self.title = title
        self.ok = True
        self.lines = []

    def log(self, msg):
        self.lines.append(msg)
        print(f"  {msg}")

    def fail(self, msg):
        self.ok = False
        self.log(f"FAIL: {msg}")

    def header(self):
        print(f"\n== {self.title} ==")


def run(cmd, cwd=None, log_path=None):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if log_path:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"$ {' '.join(str(c) for c in cmd)}  (cwd={cwd})\n")
            fh.write(proc.stdout)
            fh.write(proc.stderr)
            fh.write(f"\nexit={proc.returncode}\n\n")
    return proc


def step1_hashes(sections):
    sec = Section("Step 1: source hash verification")
    sec.header()
    p1 = run([sys.executable, "-B", "scripts/verify_hashes.py"], cwd=ROOT)
    sec.log(p1.stdout.strip().splitlines()[-1] if p1.stdout.strip() else "(no output)")
    if p1.returncode != 0:
        sec.fail("scripts/verify_hashes.py reported a failure")
    p2 = run([sys.executable, "-B", "scripts/phase3_hash_report.py"], cwd=ROOT)
    report = json.loads((V / "hash_verification_report.json").read_text())
    known = [m for m in report["mismatches"] if "posthoc_contrasts.py" in m["target"]]
    unknown = [m for m in report["mismatches"] if m not in known]
    sec.log(f"accepted-paper manifest entries: {report['n_manifest_entries']}, match: {report['n_match']}, mismatch: {report['n_mismatch']}")
    if known:
        sec.log(f"DOCUMENTED EXCEPTION (not a failure): posthoc_contrasts.py script hash differs from its own manifest — see docs/posthoc_hash_investigation.md")
    if unknown:
        sec.fail(f"{len(unknown)} undocumented hash mismatch(es): {[m['target'] for m in unknown]}")
    if not all(a["match"] for a in report["anchors"]):
        sec.fail("cohort anchor hash mismatch (260-case or aligned-control-40)")
    else:
        sec.log("cohort anchors match: 260-case b3bc2dd1…, aligned-control-40 6d0fbdf6…")
    sections.append(sec)
    return sec.ok


def step2_structure(sections):
    sec = Section("Step 2: canonical structure validation")
    sec.header()
    run([sys.executable, "-B", "scripts/phase3_structure.py"], cwd=ROOT)
    report = json.loads((V / "canonical_structure_report.json").read_text())
    for paper in ("genai4health", "agenticls"):
        for k, v in report[paper].items():
            sec.log(f"{paper}/{k}: {v['status']}")
            if v["status"] != "STRUCTURE_VERIFIED":
                sec.fail(f"{paper}/{k}: {v['problems']}")
    sections.append(sec)
    return sec.ok


def prepare_scratch():
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    SCRATCH.mkdir(parents=True)
    shutil.copytree(S_HIST, SCRATCH / "evidence_not_vote_starter")
    shutil.copytree(G_HIST, SCRATCH / "agenticls_gemini_sequential")
    shutil.copytree(A_HIST, SCRATCH / "agenticls_aligned_persistent_control")


def step3_genai4health(sections, log):
    sec = Section("Step 3: GenAI4Health analysis reproduction (scratch)")
    sec.header()
    pkg = SCRATCH / "evidence_not_vote_starter"
    for cohort, (results, cases) in COHORTS.items():
        out_dir = V / "genai4health/prespecified" / cohort
        if out_dir.exists():
            shutil.rmtree(out_dir)
        p = run([sys.executable, "-B", "score_results.py", "--results", results, "--cases", cases,
                 "--out-dir", str(out_dir)], cwd=pkg, log_path=log)
        if p.returncode != 0:
            sec.fail(f"score_results.py ({cohort}) exit {p.returncode}")
        else:
            sec.log(f"prespecified/{cohort}: score_results.py exit 0")
    ph_out = V / "genai4health/posthoc"
    if ph_out.exists():
        shutil.rmtree(ph_out)
    p = run([sys.executable, "-B", "posthoc_contrasts.py"], cwd=pkg, log_path=log)
    if p.returncode != 0:
        sec.fail(f"posthoc_contrasts.py exit {p.returncode}")
    else:
        shutil.copytree(pkg / "analysis/posthoc_contrasts", ph_out)
        sec.log("posthoc_contrasts.py exit 0")
    sections.append(sec)
    return sec.ok


def step45_agenticls(sections, log):
    sec = Section("Steps 4-5: AgenticLS persistent-260 and aligned-control-40 reproduction (scratch)")
    sec.header()
    gpkg = SCRATCH / "agenticls_gemini_sequential"
    apkg = SCRATCH / "agenticls_aligned_persistent_control"
    g_out = V / "agenticls/gemini_260_analysis.json"
    p = run([sys.executable, "-B", "analyze_sequential_gemini.py", "results/gemini_260_results.jsonl",
             "--out", str(g_out)], cwd=gpkg, log_path=log)
    sec.log(f"analyze_sequential_gemini.py exit {p.returncode}")
    if p.returncode != 0:
        sec.fail("analyze_sequential_gemini.py failed")
    a_out = V / "agenticls/aligned_control_analysis.json"
    p = run([sys.executable, "-B", "analyze_aligned_control.py", "--cases", "aligned_control_cases_40.jsonl",
             "--aligned-results", "results/aligned_control_results.jsonl",
             "--conflict-results", str(gpkg / "results/gemini_260_results.jsonl"),
             "--output-json", str(a_out)], cwd=apkg, log_path=log)
    sec.log(f"analyze_aligned_control.py exit {p.returncode}")
    if p.returncode != 0:
        sec.fail("analyze_aligned_control.py failed")
    sections.append(sec)
    return sec.ok


def step6_compare(sections):
    sec = Section("Step 6: comparison against archived outputs")
    sec.header()
    run([sys.executable, "-B", "scripts/phase3_compare.py"], cwd=ROOT)
    pre = json.loads((V / "genai4health/prespecified_comparison.json").read_text())["cohorts"]
    for k, v in pre.items():
        sec.log(f"prespecified/{k}: {v['status']}")
        if v["status"] != "EXACT_MATCH":
            sec.fail(f"prespecified/{k} did not reproduce exactly: {v['status']}")
    ph = json.loads((V / "genai4health/posthoc_comparison.json").read_text())
    cur = ph["runs"]["current_env_scipy_1.18.1"]["output_csvs_status"]
    sec.log(f"posthoc (this interpreter's scipy): {cur}")
    if cur not in ("EXACT_MATCH", "NUMERIC_MATCH"):
        sec.fail(f"posthoc outputs do not reproduce within tolerance: {cur}")
    elif cur == "NUMERIC_MATCH":
        sec.log("NOTE: NUMERIC_MATCH, not EXACT_MATCH — likely a scipy version != 1.16.3; "
                "pinned requirements-reproduction.txt gives EXACT_MATCH (see docs/reproduction_environment.md)")
    g = json.loads((V / "agenticls/gemini_260_comparison.json").read_text())
    sec.log(f"agenticls/gemini_260: {g['status']} ({g['n_fields_equal']}/{g['n_fields_compared']} fields)")
    if g["status"] != "EXACT_MATCH":
        sec.fail("gemini_260 analysis did not reproduce exactly")
    a = json.loads((V / "agenticls/aligned_control_comparison.json").read_text())
    sec.log(f"agenticls/aligned_control: {a['status']} ({a['n_fields_equal']}/{a['n_fields_compared']} fields)")
    if a["status"] != "EXACT_MATCH":
        sec.fail("aligned_control analysis did not reproduce exactly")
    c = ph["canonical_results_reference_md"]
    sec.log(f"canonical_results_reference.md: {c['n_match']}/{c['n_values_checked']} lines match")
    if c["n_match"] != c["n_values_checked"]:
        sec.fail("canonical_results_reference.md values do not all match")
    sections.append(sec)
    return sec.ok


def step7_provenance(sections):
    sec = Section("Step 7: result-provenance validation")
    sec.header()
    run([sys.executable, "-B", "scripts/phase3_provenance.py"], cwd=ROOT)
    p = run([sys.executable, "-B", "scripts/validate_result_provenance.py"], cwd=ROOT)
    for line in p.stdout.strip().splitlines():
        sec.log(line)
    if p.returncode != 0:
        sec.fail("result_provenance.csv failed schema/path validation")
    sections.append(sec)
    return sec.ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-scratch", action="store_true", help="Do not delete validation/_orchestrator_scratch/ afterwards")
    args = ap.parse_args()

    log = V / "logs/validate_accepted_papers.log"
    log.write_text(f"validate_accepted_papers.py run, interpreter {sys.executable}\n")
    (V / "logs").mkdir(parents=True, exist_ok=True)

    sections = []
    ok = True
    ok &= step1_hashes(sections)
    ok &= step2_structure(sections)
    prepare_scratch()
    ok &= step3_genai4health(sections, log)
    ok &= step45_agenticls(sections, log)
    ok &= step6_compare(sections)
    ok &= step7_provenance(sections)

    if not args.keep_scratch and SCRATCH.exists():
        shutil.rmtree(SCRATCH)

    print("\n" + "=" * 60)
    print("VALIDATE ACCEPTED PAPERS — SUMMARY")
    print("=" * 60)
    for sec in sections:
        print(f"[{'PASS' if sec.ok else 'FAIL'}] {sec.title}")
    print("-" * 60)
    print(f"Groq GPT-OSS persistent-context extension: OUT OF SCOPE (not checked)")
    print("Camera-ready manuscripts: not checked here (see scripts/audit_camera_ready_numbers.py; AgenticLS ingested, GenAI4Health CAMERA-READY PENDING)")
    print("=" * 60)
    print("OVERALL: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
