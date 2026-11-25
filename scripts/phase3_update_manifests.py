#!/usr/bin/env python3
"""Phase 3, step 11: add `historical_hashes` and `phase3_reproduction` blocks to
accepted-paper experiment_manifest.json files. Existing fields are kept as-is;
historical and reproduction hashes are separate. Groq manifest is not touched."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = "experiments/static_conflict/historical_package/evidence_not_vote_starter/"
G = "experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential/"
A = "experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control/"
V = ROOT / "validation"
pre = json.loads((V / "genai4health/prespecified_comparison.json").read_text())["cohorts"]
ph = json.loads((V / "genai4health/posthoc_comparison.json").read_text())
gc = json.loads((V / "agenticls/gemini_260_comparison.json").read_text())
ac = json.loads((V / "agenticls/aligned_control_comparison.json").read_text())
ENV = {"python": "3.14.8 (CPython, macOS 27.0.1 arm64)", "main_env": "numpy 2.5.3, pandas 3.0.6, scipy 1.18.1",
       "posthoc_sensitivity_env": "numpy 2.5.3, pandas 3.0.6, scipy 1.16.3", "agenticls_env": "standard library only",
       "date_utc": "2026-10-04", "note": "Current reproduction environment; NOT the historical execution environment (see docs/environment_validation.md)."}


def h(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def hd(paths):
    return {p: h(p) for p in paths}


def static_block(adir, cases, canon, extra_inputs):
    out_dir = f"{S}analysis/{adir}/"
    rep_dir = f"validation/genai4health/prespecified/{adir}/"
    files = sorted(p.name for p in (ROOT / out_dir).iterdir())
    hist = {"frozen_inputs": hd([S + cases] + [S + x for x in extra_inputs]), "runner": hd([S + ("run_groq.py" if "gpt_oss" in adir else "run_gemini.py")]),
            "canonical_results": hd([S + canon]), "analysis_scripts": hd([S + "score_results.py", S + "posthoc_contrasts.py"]),
            "archived_analysis_outputs": hd([out_dir + f for f in files])}
    rep = {"environment": ENV, "commands_log": "validation/logs/step4_prespecified.log; validation/logs/step5_posthoc.log",
           "reproduced_outputs": hd([rep_dir + f for f in files]),
           "prespecified_status": pre[adir]["status"],
           "posthoc_status": f"CSVs {ph['runs']['current_env_scipy_1.18.1']['output_csvs_status']} (scipy 1.18.1); {ph['runs']['sensitivity_env_scipy_1.16.3']['output_csvs_status']} (scipy 1.16.3)",
           "status": "ANALYSIS_REPRODUCED"}
    return hist, rep


def update(path, blocks):
    p = ROOT / path / "experiment_manifest.json"
    m = json.loads(p.read_text())
    if "experiments" in m:
        for e in m["experiments"]:
            if e["experiment_id"] in blocks:
                e["historical_hashes"], e["phase3_reproduction"] = blocks[e["experiment_id"]]
            elif e["experiment_id"] not in blocks:
                e.setdefault("phase3_reproduction", {"status": "NOT_TESTED_IN_PHASE3"})
    else:
        m["historical_hashes"], m["phase3_reproduction"] = blocks[m["experiment_id"]]
    p.write_text(json.dumps(m, indent=2) + "\n")
    print("updated", path)


update("experiments/static_conflict/gemini_primary_40", {"static_gemini_primary_40": static_block("primary_gemini", "data/final_main_cases.jsonl", "results/final_main_gemini_3_6_flash.jsonl", ["data/final_main_prompts.jsonl"])})
update("experiments/static_conflict/gemini_replication_260", {"static_gemini_replication_260": static_block("replication_gemini", "data/replication_cases.jsonl", "results/replication_gemini_3_6_flash_CLEAN.jsonl", ["data/replication_prompts.jsonl"])})
update("experiments/static_conflict/guideline_veto", {"static_gemini_veto_15": static_block("veto_gemini", "data/final_veto_cases.jsonl", "results/final_veto_gemini_3_6_flash.jsonl", ["data/final_veto_prompts.jsonl"])})
update("experiments/static_conflict/gpt_oss_sensitivity", {
    "static_gpt_oss_primary_40": static_block("gpt_oss_primary", "data/final_main_cases.jsonl", "results/final_main_gpt_oss_120b_CLEAN.jsonl", ["data/final_main_prompts.jsonl"]),
    "static_gpt_oss_veto_15": static_block("gpt_oss_veto", "data/final_veto_cases.jsonl", "results/final_veto_gpt_oss_120b_CLEAN.jsonl", ["data/final_veto_prompts.jsonl"])})
update("experiments/static_conflict/latent_v2", {"static_gemini_latent_v2_40": static_block("latent_v2_gemini", "data/final_main_cases.jsonl", "results/latent_v2_main_gemini_3_6_flash_CLEAN.jsonl", ["data/latent_v2_main_prompts.jsonl"])})

pa = f"{S}analysis/posthoc_contrasts/"
names = sorted(p.name for p in (ROOT / pa).iterdir())
m = json.loads((ROOT / "experiments/static_conflict/analysis/experiment_manifest.json").read_text())
m["historical_hashes"] = {"posthoc_script_recovered": h(S + "posthoc_contrasts.py"), "posthoc_script_per_archived_manifest": ph["manifest_script_sha256"],
                          "archived_posthoc_outputs": hd([pa + n for n in names]), "canonical_results_reference_md": h(S + "analysis/canonical_results_reference.md")}
m["phase3_reproduction"] = {"environment": ENV,
    "reproduced_outputs_scipy_1.18.1": hd([f"validation/genai4health/posthoc/{n}" for n in names]),
    "reproduced_outputs_scipy_1.16.3": hd([f"validation/genai4health/posthoc_scipy1.16.3/{n}" for n in names]),
    "posthoc_status": {k: v["output_csvs_status"] for k, v in ph["runs"].items()},
    "canonical_results_reference_values": f"{ph['canonical_results_reference_md']['n_match']}/{ph['canonical_results_reference_md']['n_values_checked']} lines match",
    "figure1": "DATA_REPRODUCED / PLOTTING_CODE_MISSING",
    "status": "ANALYSIS_REPRODUCED with documented script-hash DISCREPANCY (see docs/posthoc_hash_investigation.md)"}
(ROOT / "experiments/static_conflict/analysis/experiment_manifest.json").write_text(json.dumps(m, indent=2) + "\n")
print("updated static analysis")

update("experiments/persistent_context/gemini_persistent_260", {"agenticls_gemini_persistent_260": (
    {"frozen_inputs": hd([G + "replication_cases_verified.jsonl"]), "runner": hd([G + "run_sequential_gemini.py"]), "protocol": hd([G + "PROTOCOL_FREEZE_GEMINI.md"]),
     "canonical_results": hd([G + "results/gemini_260_results.jsonl"]), "raw_attempts": hd([G + "results/gemini_260_attempts.jsonl"]),
     "analysis_scripts": hd([G + "analyze_sequential_gemini.py"]), "archived_analysis_outputs": hd([G + "results/gemini_260_analysis.json"])},
    {"environment": ENV, "commands_log": "validation/logs/step6_7_agenticls.log", "reproduced_outputs": hd(["validation/agenticls/gemini_260_analysis.json"]),
     "comparison": f"{gc['status']} ({gc['n_fields_equal']}/{gc['n_fields_compared']} fields)", "status": "ANALYSIS_REPRODUCED"})})
update("experiments/persistent_context/gemini_aligned_control_40", {"agenticls_gemini_aligned_control_40": (
    {"frozen_inputs": hd([A + "aligned_control_cases_40.jsonl"]), "runner": hd([A + "run_aligned_control_gemini.py"]), "protocol": hd([A + "PROTOCOL_FREEZE_ALIGNED_CONTROL.md"]),
     "canonical_results": hd([A + "results/aligned_control_results.jsonl", G + "results/gemini_260_results.jsonl"]), "raw_attempts": hd([A + "results/aligned_control_attempts.jsonl"]),
     "analysis_scripts": hd([A + "analyze_aligned_control.py"]), "archived_analysis_outputs": hd([A + "results/aligned_control_analysis.json"])},
    {"environment": ENV, "commands_log": "validation/logs/step6_7_agenticls.log", "reproduced_outputs": hd(["validation/agenticls/aligned_control_analysis.json"]),
     "comparison": f"{ac['status']} ({ac['n_fields_equal']}/{ac['n_fields_compared']} fields)", "status": "ANALYSIS_REPRODUCED"})})
