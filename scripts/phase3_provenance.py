#!/usr/bin/env python3
"""Phase 3, step 8: result provenance map for accepted-paper results.

Values are READ from archived machine-generated outputs (never typed); the
reproduced_status comes from validation/*_comparison.json.
Writes docs/result_provenance.csv and docs/result_provenance.md."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SR = "experiments/static_conflict/historical_package/evidence_not_vote_starter/"
GR = "experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential/"
AR = "experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control/"
V = ROOT / "validation"

pre = json.loads((V / "genai4health/prespecified_comparison.json").read_text())["cohorts"]
ph = json.loads((V / "genai4health/posthoc_comparison.json").read_text())
gcmp = json.loads((V / "agenticls/gemini_260_comparison.json").read_text())
acmp = json.loads((V / "agenticls/aligned_control_comparison.json").read_text())

PH_STATUS = {n: r["status"] for n, r in ph["runs"]["current_env_scipy_1.18.1"]["files"].items()}
PH_STATUS_116 = {n: r["status"] for n, r in ph["runs"]["sensitivity_env_scipy_1.16.3"]["files"].items()}

COH = {  # cohort -> (experiment, cohort file, raw file, canonical file, prespecified analysis dir)
    "primary": ("static_conflict/gemini_primary_40", "data/final_main_cases.jsonl", "results/final_main_gemini_3_6_flash.jsonl", "results/final_main_gemini_3_6_flash.jsonl", "primary_gemini"),
    "replication": ("static_conflict/gemini_replication_260", "data/replication_cases.jsonl", "results/replication_gemini_3_6_flash_RAW.jsonl", "results/replication_gemini_3_6_flash_CLEAN.jsonl", "replication_gemini"),
    "veto": ("static_conflict/guideline_veto", "data/final_veto_cases.jsonl", "results/final_veto_gemini_3_6_flash.jsonl", "results/final_veto_gemini_3_6_flash.jsonl", "veto_gemini"),
    "gpt_oss_primary": ("static_conflict/gpt_oss_sensitivity", "data/final_main_cases.jsonl", "results/final_main_gpt_oss_120b_RAW.jsonl", "results/final_main_gpt_oss_120b_CLEAN.jsonl", "gpt_oss_primary"),
    "gpt_oss_veto": ("static_conflict/gpt_oss_sensitivity", "data/final_veto_cases.jsonl", "results/final_veto_gpt_oss_120b_RAW.jsonl", "results/final_veto_gpt_oss_120b_CLEAN.jsonl", "gpt_oss_veto"),
    "latent_v2": ("static_conflict/latent_v2", "data/final_main_cases.jsonl", "results/latent_v2_main_gemini_3_6_flash_RAW.jsonl", "results/latent_v2_main_gemini_3_6_flash_CLEAN.jsonl", "latent_v2_gemini"),
}
rows = []


def rd(path):
    return list(csv.DictReader(open(ROOT / path, encoding="utf-8")))


def add(**k):
    rows.append(k)


_bin_rows = rd(SR + "analysis/posthoc_contrasts/binomial_proportions_exact.csv")
BIN_DIFF_KEYS = {(_bin_rows[d["row"] - 1]["cohort"], _bin_rows[d["row"] - 1]["metric"])
                 for d in ph["runs"]["current_env_scipy_1.18.1"]["files"]["binomial_proportions_exact.csv"]["differences"]}


def ph_status(fname, row_key=None):
    s = PH_STATUS[fname]
    if fname == "binomial_proportions_exact.csv" and row_key is not None:
        # Row-level status: only rows listed in the comparison's differences differ.
        s = "NUMERIC_MATCH" if row_key in BIN_DIFF_KEYS else "EXACT_MATCH (row values identical)"
    if s.startswith("NUMERIC_MATCH") and PH_STATUS_116[fname] == "EXACT_MATCH":
        s += " (EXACT_MATCH under scipy 1.16.3)"
    return "REPRODUCED: " + s


# ---------------- GenAI4Health
for cohort, (exp, cases, raw, canon, adir) in COH.items():
    base = dict(paper="GenAI4Health", experiment=exp, source_cohort=SR + cases, source_raw_file=SR + raw, source_canonical_file=SR + canon,
                protocol=SR + "analysis_contract.md")
    prespec_status = "REPRODUCED: " + pre[adir]["status"]
    props = {r["metric"]: r for r in rd(SR + "analysis/posthoc_contrasts/binomial_proportions_exact.csv") if r["cohort"] == cohort}
    for metric in ["accuracy_H", "EDR1", "EDR2", "EDR4", "order_disagreement"] + [m for m in props if m.startswith("VFR_")]:
        if metric not in props:
            continue
        r = props[metric]
        pp = "PRESPECIFIED" if metric in ("EDR4",) else "PRESPECIFIED (endpoint); exact CI POST_HOC"
        add(**base, result_id=f"g4h.{cohort}.{metric}", description=f"{metric} with exact Clopper-Pearson 95% CI",
            analysis_script=f"{SR}posthoc_contrasts.py;{SR}score_results.py",
            analysis_output=f"{SR}analysis/posthoc_contrasts/binomial_proportions_exact.csv;{SR}analysis/{adir}/accuracy_by_condition.csv",
            prespecified_or_posthoc=pp, value=f"{r['numerator']}/{r['denominator']} = {r['percent']} [{r['cp_lo']}, {r['cp_hi']}]",
            reproduced_status=f"{ph_status('binomial_proportions_exact.csv', (cohort, metric))}; prespecified CSVs {prespec_status}",
            notes="EDR conditional on H correct." if metric.startswith("EDR") else "")
    cs = rd(f"{SR}analysis/{adir}/confidence_shift.csv")
    if cs:
        r = cs[0]
        add(**base, result_id=f"g4h.{cohort}.confidence_shift_H_to_H_L4", description="Mean confidence change H -> H_L4 (prespecified secondary; percentile bootstrap)",
            analysis_script=SR + "score_results.py", analysis_output=f"{SR}analysis/{adir}/confidence_shift.csv", prespecified_or_posthoc="PRESPECIFIED",
            value=f"n={r['n']} shift={r['confidence_shift_H_to_H_L4']} [{r['ci_lo']}, {r['ci_hi']}]", reproduced_status=prespec_status, notes="")
    al = rd(f"{SR}analysis/{adir}/aligned_control.csv")
    if al:
        r = al[0]
        add(**base, result_id=f"g4h.{cohort}.aligned_control_delta_accuracy", description="Accuracy(H_L4_ALIGNED) - accuracy(H_L4)",
            analysis_script=SR + "score_results.py", analysis_output=f"{SR}analysis/{adir}/aligned_control.csv", prespecified_or_posthoc="PRESPECIFIED",
            value=f"n={r['n']} delta={r['aligned_control_delta']} [{r['ci_lo']}, {r['ci_hi']}]", reproduced_status=prespec_status, notes="")
    vf = rd(f"{SR}analysis/{adir}/veto_failure_rate.csv")
    if vf and int(vf[0]["n"]) > 0:
        r = vf[0]
        add(**base, result_id=f"g4h.{cohort}.veto_failure_rate_H_L4", description="Veto failure rate at H_L4 (prespecified; percentile bootstrap)",
            analysis_script=SR + "score_results.py", analysis_output=f"{SR}analysis/{adir}/veto_failure_rate.csv", prespecified_or_posthoc="PRESPECIFIED (BOUNDARY cohort)",
            value=f"n={r['n']} rate={r['veto_failure_rate']} [{r['ci_lo']}, {r['ci_hi']}]", reproduced_status=prespec_status,
            notes="score_results bootstrap CI degenerates at 0/n; exact CI in posthoc VFR rows.")
    for r in rd(SR + "analysis/posthoc_contrasts/confidence_contrasts_bootstrap.csv"):
        if r["cohort"] != cohort:
            continue
        add(**base, result_id=f"g4h.{cohort}.{r['contrast']}", description=f"Paired confidence contrast {r['contrast']} (case-level bootstrap, seed {r['boot_seed']})",
            analysis_script=SR + "posthoc_contrasts.py", analysis_output=SR + "analysis/posthoc_contrasts/confidence_contrasts_bootstrap.csv;" + SR + "analysis/posthoc_contrasts/confidence_direction_counts.csv",
            prespecified_or_posthoc="POST_HOC", value=f"n={r['n_cases']} mean={r['mean_difference']} [{r['boot_lo']}, {r['boot_hi']}]",
            reproduced_status=ph_status("confidence_contrasts_bootstrap.csv"),
            notes="conflict_minus_aligned is not a contract endpoint." if r["contrast"] == "conflict_minus_aligned" else "")
    for r in rd(SR + "analysis/posthoc_contrasts/paired_accuracy_mcnemar.csv"):
        if r["cohort"] == cohort:
            add(**base, result_id=f"g4h.{cohort}.mcnemar.{r['comparison']}", description=f"Exact McNemar {r['comparison']}",
                analysis_script=SR + "posthoc_contrasts.py", analysis_output=SR + "analysis/posthoc_contrasts/paired_accuracy_mcnemar.csv",
                prespecified_or_posthoc="POST_HOC", value=f"n={r['n']} p={r['mcnemar_exact_p']}", reproduced_status=ph_status("paired_accuracy_mcnemar.csv"), notes="")
    ft = rd(f"{SR}analysis/{adir}/flip_threshold.csv")
    if ft:
        from collections import Counter
        add(**base, result_id=f"g4h.{cohort}.flip_threshold", description="Flip threshold among H-correct cases",
            analysis_script=SR + "score_results.py", analysis_output=f"{SR}analysis/{adir}/flip_threshold.csv", prespecified_or_posthoc="PRESPECIFIED",
            value=json.dumps(dict(Counter(r["flip_threshold"] for r in ft))), reproduced_status=prespec_status, notes="")

rep = dict(paper="GenAI4Health", experiment="static_conflict/gemini_replication_260", source_cohort=SR + "data/replication_cases.jsonl",
           source_raw_file=SR + "results/replication_gemini_3_6_flash_RAW.jsonl", source_canonical_file=SR + "results/replication_gemini_3_6_flash_CLEAN.jsonl",
           protocol=SR + "analysis_contract.md", analysis_script=SR + "posthoc_contrasts.py", prespecified_or_posthoc="POST_HOC")
for r in rd(SR + "analysis/posthoc_contrasts/replication_conflict_aligned_by_stratum.csv"):
    add(**rep, result_id=f"g4h.replication.stratified.{r['stratum']}", description="Conflict-minus-aligned confidence by stratum",
        analysis_output=SR + "analysis/posthoc_contrasts/replication_conflict_aligned_by_stratum.csv",
        value=f"n={r['n']} mean={r['mean_conflict_minus_aligned']} [{r['ci_lo']}, {r['ci_hi']}]", reproduced_status=ph_status("replication_conflict_aligned_by_stratum.csv"), notes="")
for r in rd(SR + "analysis/posthoc_contrasts/anonymization_sensitivity.csv"):
    if r["subset"] != "excluded case ids":
        add(**rep, result_id=f"g4h.replication.anonymization.{r['subset']}", description="Anonymization sensitivity of conflict-minus-aligned contrast",
            analysis_output=SR + "analysis/posthoc_contrasts/anonymization_sensitivity.csv",
            value=f"n={r['n']} mean={r['mean_conflict_minus_aligned']} [{r['ci_lo']}, {r['ci_hi']}]", reproduced_status=ph_status("anonymization_sensitivity.csv"), notes="")
for r in rd(SR + "analysis/posthoc_contrasts/categorical_degradation_summary.csv"):
    add(**{**rep, "experiment": f"static_conflict ({r['cohort']})"}, result_id=f"g4h.{r['cohort']}.degradation.{r['contrast']}", description="Categorical degradation among H-correct cases",
        analysis_output=SR + "analysis/posthoc_contrasts/categorical_degradation_summary.csv",
        value=f"denom={r['H_correct_denominator']} total={r['categorical_degradation_total']} to_insufficient={r['to_insufficient']} reversal={r['wrong_direction_reversal']}",
        reproduced_status=ph_status("categorical_degradation_summary.csv"), notes="post_hoc_descriptive")
add(paper="GenAI4Health", result_id="g4h.canonical_results_reference", description="Rounded manuscript reference values (canonical_results_reference.md)",
    experiment="static_conflict (all)", source_cohort="", source_raw_file="", source_canonical_file="", analysis_script="NOT RECOVERED (generator unknown)",
    analysis_output=SR + "analysis/canonical_results_reference.md", protocol="", prespecified_or_posthoc="MIXED (labelled per section)",
    value=f"{ph['canonical_results_reference_md']['n_match']}/{ph['canonical_results_reference_md']['n_values_checked']} lines match regenerated outputs",
    reproduced_status="VALUES REPRODUCED (file generator not recovered)", notes="Rounding ROUND_HALF_UP 2 dp as stated in the file.")
add(paper="GenAI4Health", result_id="g4h.figure1", description="Figure 1 decision-confidence dissociation", experiment="static_conflict",
    source_cohort="", source_raw_file="", source_canonical_file="", analysis_script="MISSING", analysis_output=SR + "figures/figure1_decision_confidence_dissociation.pdf",
    protocol="", prespecified_or_posthoc="UNKNOWN", value="", reproduced_status="see docs/figure_reproduction_status.md", notes="")

# ---------------- AgenticLS
gj = json.loads((ROOT / GR / "results/gemini_260_analysis.json").read_text())
gb = dict(paper="AgenticLS", experiment="persistent_context/gemini_persistent_260", source_cohort=GR + "replication_cases_verified.jsonl",
          source_raw_file=GR + "results/gemini_260_attempts.jsonl", source_canonical_file=GR + "results/gemini_260_results.jsonl",
          analysis_script=GR + "analyze_sequential_gemini.py", analysis_output=GR + "results/gemini_260_analysis.json", protocol=GR + "PROTOCOL_FREEZE_GEMINI.md",
          reproduced_status="REPRODUCED: " + gcmp["status"] + f" ({gcmp['n_fields_equal']}/{gcmp['n_fields_compared']} fields)")
t = gj["terminal"]
for rid, desc, keys, pp in [
    ("terminal_categorical_agreement", "Sequential H_L4 vs fresh H_L4 decision agreement", ["decision_agreement_n", "decision_agreement_rate", "decision_disagreement_n", "disagreement_95ci_clopper_pearson"], "PRESPECIFIED (primary)"),
    ("terminal_confidence_difference", "Sequential minus fresh terminal confidence (paired bootstrap 100,000, seed 20260922)", ["confidence_seq_minus_fresh_mean", "confidence_median", "confidence_95ci_paired_bootstrap", "confidence_lower_equal_higher"], "PRESPECIFIED (primary)"),
    ("terminal_E0_transition", "E0 inclusion fresh->sequential", ["E0_transitions_fresh_to_sequential"], "PRESPECIFIED (primary)"),
    ("terminal_accuracy_mcnemar", "Terminal correctness exact McNemar", ["accuracy_mcnemar"], "PRESPECIFIED (secondary)"),
]:
    add(**gb, result_id=f"agl.gemini260.{rid}", description=desc, prespecified_or_posthoc=pp,
        value=json.dumps({k: t[k] for k in keys}), notes=f"JSON path: terminal.{{{','.join(keys)}}}")
st = gj["sequential_trajectory"]
add(**gb, result_id="agl.gemini260.sequential_trajectory", description="Sequential confidence trajectory H..H_L4", prespecified_or_posthoc="PRESPECIFIED (primary)",
    value=json.dumps({k: st[k] for k in ["turn_means", "mean_change_from_initial", "fully_nonincreasing_n", "terminal_le_initial_n"]}), notes="JSON path: sequential_trajectory")
add(**gb, result_id="agl.gemini260.E0_inclusion_by_turn", description="E0 inclusion rate by sequential turn", prespecified_or_posthoc="PRESPECIFIED (primary)",
    value=json.dumps(st["E0_inclusion_rate_by_turn"]), notes="JSON path: sequential_trajectory.E0_inclusion_rate_by_turn")
add(**gb, result_id="agl.gemini260.first_decline_deviation", description="First confidence decline / first categorical deviation turn", prespecified_or_posthoc="PRESPECIFIED (primary)",
    value=json.dumps({k: st[k] for k in ["first_confidence_decline", "first_categorical_deviation"]}), notes="")
add(**gb, result_id="agl.gemini260.threshold_sensitivity", description="Threshold discordance tau=70..95", prespecified_or_posthoc="EXPLORATORY (prespecified as exploratory)",
    value=f"{len(gj['exploratory_threshold_sensitivity'])} thresholds", notes="JSON path: exploratory_threshold_sensitivity")
add(**gb, result_id="agl.gemini260.stratified_reference_decision", description="Seq-minus-fresh by reference decision", prespecified_or_posthoc="PRESPECIFIED (secondary)",
    value=json.dumps(gj["secondary_stratified"]), notes="")

aj = json.loads((ROOT / AR / "results/aligned_control_analysis.json").read_text())
ab = dict(paper="AgenticLS", experiment="persistent_context/gemini_aligned_control_40", source_cohort=AR + "aligned_control_cases_40.jsonl",
          source_raw_file=AR + "results/aligned_control_attempts.jsonl", source_canonical_file=AR + "results/aligned_control_results.jsonl;" + GR + "results/gemini_260_results.jsonl",
          analysis_script=AR + "analyze_aligned_control.py", analysis_output=AR + "results/aligned_control_analysis.json", protocol=AR + "PROTOCOL_FREEZE_ALIGNED_CONTROL.md",
          prespecified_or_posthoc="POST_HOC (frozen control protocol)",
          reproduced_status="REPRODUCED: " + acmp["status"] + f" ({acmp['n_fields_equal']}/{acmp['n_fields_compared']} fields)")
a = aj["aligned_terminal"]
add(**ab, result_id="agl.aligned40.aligned_gap", description="Aligned persistent-minus-fresh terminal confidence (bootstrap 10,000, seed 2026092301)",
    value=json.dumps({k: a[k] for k in ["seq_minus_fresh_mean", "median", "bootstrap_95_ci", "direction_counts"]}), notes="JSON path: aligned_terminal")
add(**ab, result_id="agl.aligned40.aligned_categorical_agreement_E0", description="Aligned terminal categorical agreement and E0 in both",
    value=json.dumps({k: a[k] for k in ["categorical_agreement_n", "e0_in_both_n"]}), notes="n=40")
c = aj["same_40_existing_conflict_terminal"]
add(**ab, result_id="agl.aligned40.conflict_gap_same40", description="Conflict persistent-minus-fresh gap on the same 40 cases",
    value=json.dumps({k: c[k] for k in ["seq_minus_fresh_mean", "median", "bootstrap_95_ci", "direction_counts"]}), notes="JSON path: same_40_existing_conflict_terminal")
i = aj["polarity_by_persistence_interaction"]
add(**ab, result_id="agl.aligned40.interaction", description="Paired (conflict gap) - (aligned gap)",
    value=json.dumps({k: i[k] for k in ["mean", "median", "bootstrap_95_ci", "negative_n", "zero_n", "positive_n"]}), notes="JSON path: polarity_by_persistence_interaction")
add(**ab, result_id="agl.aligned40.trajectories", description="Aligned vs conflict persistent trajectory means (same 40, shared H)",
    value=json.dumps(aj["trajectory_means"]), notes="")

F = ["paper", "result_id", "description", "experiment", "source_cohort", "source_raw_file", "source_canonical_file", "analysis_script",
     "analysis_output", "protocol", "prespecified_or_posthoc", "reproduced_status", "value", "notes",
     # Reserved for Phase 4 per user instruction: camera-ready PDFs are not
     # final yet, so these are placeholders (TODO), not guesses.
     "camera_ready_location", "table_number", "figure_number", "section"]
for r in rows:
    r.setdefault("camera_ready_location", "TODO: camera-ready pending")
    r.setdefault("table_number", "TODO")
    r.setdefault("figure_number", "TODO")
    r.setdefault("section", "TODO")
with open(ROOT / "docs/result_provenance.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=F)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows")
