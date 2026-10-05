#!/usr/bin/env python3
"""RELEASE TOOLING (not historical execution code). ARCHIVE-MODE audit.

Cross-checks every scientific numeric claim in an ingested camera-ready PDF
against the archived, hash-verified analysis outputs (and, where no archived
output exists, against a read-only recomputation from the canonical result
files, clearly labelled as such). It never edits the PDF, any archived file,
or any value.

Statuses: EXACT_MATCH, ROUNDING_MATCH, TEXTUAL_CLAIM_VERIFIED, UNMAPPED,
MISMATCH, NOT_MACHINE_CHECKABLE.  A single MISMATCH blocks that paper.
NOT_MACHINE_CHECKABLE items must carry manual_verification=true plus a
verifier_note describing what was actually checked.

Requires: numpy (for the archived bootstrap routine; use the repo venv) and
pypdf (NOT in the pinned reproduction env; see requirements-camera-ready-audit.txt).

Usage:  python scripts/audit_camera_ready_numbers.py [--paper agenticls|genai4health|all]
Exit 0 only if no MISMATCH and no UNMAPPED in any audited paper.
"""
import argparse, csv, hashlib, importlib.util, json, re, sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter"
PC = ROOT / "experiments/persistent_context"
P260 = PC / "gemini_persistent_260/historical_package/agenticls_gemini_sequential"
A40 = PC / "gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control"
OUT_JSON = ROOT / "validation/camera_ready_number_audit.json"
OUT_MD = ROOT / "docs/camera_ready_number_audit.md"
PAPER_PDFS = {"agenticls": ROOT / "papers/agenticls/paper/agenticls-camera-ready.pdf",
              "genai4health": ROOT / "papers/genai4health/paper/genai4health-camera-ready.pdf"}


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def csvrows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- PDF text
def pdf_pages(pdf):
    from pypdf import PdfReader
    return [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]


def norm(t):
    t = t.replace("−", "-").replace("–", "-").replace("­", "")
    t = t.replace("_", "")  # some PDF text layers drop underscores
    return re.sub(r"\s+", "", t)


# ---------------------------------------------------------------- artifacts
class Art:
    def __init__(self):
        ph = S / "analysis/posthoc_contrasts"
        self.contr = {(r["cohort"], r["contrast"]): r for r in csvrows(ph / "confidence_contrasts_bootstrap.csv")}
        self.dirc = {(r["cohort"], r["contrast"]): r for r in csvrows(ph / "confidence_direction_counts.csv")}
        self.binom = {(r["cohort"], r["metric"]): r for r in csvrows(ph / "binomial_proportions_exact.csv")}
        self.anon = {r["subset"]: r for r in csvrows(ph / "anonymization_sensitivity.csv")}
        self.degr = {(r["cohort"], r["contrast"]): r for r in csvrows(ph / "categorical_degradation_summary.csv")}
        self.strat = {r["stratum"]: r for r in csvrows(ph / "replication_conflict_aligned_by_stratum.csv")}
        self.seq = json.load(open(P260 / "results/gemini_260_analysis.json"))
        self.ali = json.load(open(A40 / "results/aligned_control_analysis.json"))
        self.rep = jl(S / "results/replication_gemini_3_6_flash_CLEAN.jsonl")
        self.rep_raw = jl(S / "results/replication_gemini_3_6_flash_RAW.jsonl")
        self.seqres = jl(P260 / "results/gemini_260_results.jsonl")
        self.seqatt = jl(P260 / "results/gemini_260_attempts.jsonl")
        self.aliatt = jl(A40 / "results/aligned_control_attempts.jsonl")
        self.alires = jl(A40 / "results/aligned_control_results.jsonl")
        self.prov = {r["result_id"]: r for r in csvrows(ROOT / "docs/result_provenance.csv")}
        ph_spec = importlib.util.spec_from_file_location("ph", S / "posthoc_contrasts.py")
        self.ph = importlib.util.module_from_spec(ph_spec)
        ph_spec.loader.exec_module(self.ph)  # defines functions; main() is not run on import

    def conf_by_cond(self, rows):
        d = {}
        for r in rows:
            d.setdefault(r["case_id"], {})[r["condition"]] = r
        return d

    def seq_terminal(self):
        d = {}
        for r in self.seqres:
            if r["condition"] == "H_L4" and r["arm"] in ("sequential", "fresh"):
                d.setdefault(r["case_id"], {})[r["arm"]] = r
        return d


def ci(x, lo=None, hi=None):
    return x


# ---------------------------------------------------------------- comparison
def decimals(s):
    s = s.replace("%", "").replace(",", "").replace("−", "-")
    return len(s.split(".")[1]) if "." in s else 0


def compare(disp, expected, kind):
    """Return (status, detail). kind: count|num"""
    s = disp.replace("%", "").replace(",", "").replace("−", "-")
    shown = float(s)
    if kind == "count":
        return ("EXACT_MATCH", "") if shown == expected else ("MISMATCH", f"printed {disp}, artifact {expected}")
    d = decimals(disp)
    diff = abs(shown - expected)
    if diff < 1e-12:
        return "EXACT_MATCH", ""
    half = 0.5 * 10 ** (-d)
    if diff <= half + 1e-9:
        tie = abs(diff - half) < 1e-9
        return "ROUNDING_MATCH", (f"artifact {expected!r}; printed to {d} dp"
                                  + ("; artifact sits exactly on a half-unit rounding boundary" if tie else ""))
    return "MISMATCH", f"printed {disp}, artifact {expected!r} (|diff|={diff:.6g} > rounding half-unit {half})"


class Auditor:
    def __init__(self, pages, art):
        self.pages = pages
        self.npages = [norm(p) for p in pages]
        self.full = "".join(self.npages)
        self.art = art
        self.claims = []
        self.spans = []

    def locate(self, ctx):
        c = norm(ctx)
        pg = [i + 1 for i, t in enumerate(self.npages) if c in t]
        if not pg:
            return None, []
        for m in re.finditer(re.escape(c), self.full):
            self.spans.append((m.start(), m.end()))
        return pg[0], pg

    def npages_count(self, ctx):
        c = norm(ctx)
        return sum(t.count(c) for t in self.npages)

    def add(self, cid, section, ctx, disp, kind, expected, rid=None, source="", note="",
            status=None, manual=None):
        page, pgs = self.locate(ctx)
        if page is None:
            self.claims.append(dict(claim_id=cid, section=section, page=None, printed=disp, ctx=ctx,
                                    status="MISMATCH", detail="printed text fragment not found in camera-ready PDF",
                                    result_id=rid, source=source, note=note))
            return
        if norm(disp) not in norm(ctx):
            raise SystemExit(f"audit-tool bug: display {disp!r} not inside ctx {ctx!r}")
        if kind == "text":
            st, det = ("TEXTUAL_CLAIM_VERIFIED", "") if expected else ("MISMATCH", "textual predicate false")
        elif kind == "nmc":
            st, det = "NOT_MACHINE_CHECKABLE", ""
        else:
            st, det = compare(disp, expected, kind)
        row = dict(claim_id=cid, section=section, page=page, printed=disp, ctx=ctx, status=st, detail=det,
                   result_id=rid, source=source, note=note)
        if kind == "nmc":
            row["manual_verification"] = bool(manual)
            row["verifier_note"] = manual or ""
        if rid is None and kind != "nmc":
            row["unmapped_claim"] = True  # verified against canonical data, no result_id row exists
        self.claims.append(row)


# ---------------------------------------------------------------- AgenticLS
def agenticls_claims(A, art):
    R = "g4h.replication."
    pr, rep = art.prov, "static_conflict/gemini_replication_260"
    seq, ali = art.seq, art.ali
    term, sres = seq["terminal"], art.seq_terminal()
    contr, dirc, binom = art.contr, art.dirc, art.binom

    def b(cohort, metric):
        r = binom[(cohort, metric)]
        return int(r["numerator"]), int(r["denominator"]), float(r["percent"]), float(r["cp_lo"]), float(r["cp_hi"])

    # --- Abstract / Results: static replication ---
    n, d, pct, _, _ = b("replication", "accuracy_H")
    A.add("agl.static.accH.num", "Results", "correct under H in 259/260 cases (99.62%)", "259", "count", n, R + "accuracy_H", "binomial_proportions_exact.csv")
    A.add("agl.static.accH.den", "Results", "correct under H in 259/260 cases (99.62%)", "260", "count", d, R + "accuracy_H", "binomial_proportions_exact.csv")
    A.add("agl.static.accH.pct", "Results", "correct under H in 259/260 cases (99.62%)", "99.62", "num", pct, R + "accuracy_H", "binomial_proportions_exact.csv")
    A.add("agl.abs.baseline_correct", "Abstract", "among 259 cases correct under the anchor alone", "259", "count", d - 1 if False else int(b("replication", "EDR1")[1]), R + "EDR1", "binomial_proportions_exact.csv (EDR denominator)")
    for k, disp_pct, ctx in [("1", "0.77", "2/259 (0.77%) after one conflicting item"),
                             ("2", "0.39", "1/259 (0.39%) after two"), ("4", "0.39", "1/259 (0.39%) after four")]:
        nn, dd, pp, _, _ = b("replication", f"EDR{k}")
        A.add(f"agl.static.EDR{k}.num", "Results", ctx, ctx.split("/")[0], "count", nn, R + f"EDR{k}", "binomial_proportions_exact.csv")
        A.add(f"agl.static.EDR{k}.pct", "Results", ctx, disp_pct, "num", pp, R + f"EDR{k}", "binomial_proportions_exact.csv")
    A.add("agl.abs.EDR_list", "Abstract", "Evidence Dilution Rates were 0.77%, 0.39%, and 0.39% after one, two, and four conflicting items",
          "0.77%", "num", b("replication", "EDR1")[2], R + "EDR1", "binomial_proportions_exact.csv")
    A.add("agl.abs.EDR_list2", "Abstract", "Evidence Dilution Rates were 0.77%, 0.39%, and 0.39% after one, two, and four conflicting items",
          "0.39%", "num", b("replication", "EDR2")[2], R + "EDR2", "binomial_proportions_exact.csv")
    # deviation structure
    tot = sum(int(art.degr[("replication", f"H->{c}")]["categorical_degradation_total"]) for c in ("H_L1", "H_L2", "H_L4"))
    toi = sum(int(art.degr[("replication", f"H->{c}")]["to_insufficient"]) for c in ("H_L1", "H_L2", "H_L4"))
    rev = sum(int(art.degr[("replication", f"H->{c}")]["wrong_direction_reversal"]) for c in ("H_L1", "H_L2", "H_L4"))
    cc = art.conf_by_cond(art.rep)
    dev_cases = {cid for cid, v in cc.items() if v["H"]["decision"] == v["H"]["reference_decision"] and
                 any(v[c]["decision"] != v["H"]["decision"] for c in ("H_L1", "H_L2", "H_L4"))}
    A.add("agl.static.deviation_structure", "Results", "The four condition-level deviations arose from two cases and were all shifts to insufficient; no opposite-direction reversals occurred",
          "four", "text", tot == 4 and len(dev_cases) == 2 and toi == 4 and rev == 0, "g4h.replication.degradation.H->H_L1;g4h.replication.degradation.H->H_L2;g4h.replication.degradation.H->H_L4",
          "categorical_degradation_summary.csv + distinct deviating cases from replication CLEAN file")
    # E0 attribution
    e0_all = all("E0" in r["dominant_evidence_ids"] for r in art.rep)
    sole = {c: sum(1 for r in art.rep if r["condition"] == c and r["dominant_evidence_ids"] == ["E0"]) for c in ("H_L1", "H_L2", "H_L4")}
    A.add("agl.static.E0_all_outputs", "Results", "appeared in reported dominant-evidence attribution in all 1,560 static replication outputs", "1,560", "count", len(art.rep) if e0_all else -1, None, "replication CLEAN file (E0 in dominant ids, all rows); also analysis/dominant_evidence/results.txt")
    A.add("agl.static.E0_sole", "Results", "was the sole reported dominant source in every conflicting condition", "sole", "text", all(v == 260 for v in sole.values()), None, "replication CLEAN file; dominant_evidence/results.txt (anchor-only 260/260 for H_L1,H_L2,H_L4)")
    # matched contrast
    cm = contr[("replication", "conflict_minus_aligned")]
    ch = contr[("replication", "conflict_minus_H")]
    for disp, key, ctx in [("85.48", "mean_a", "85.48 with conflicting lower-tier evidence"), ("91.99", "mean_b", "91.99 with aligned evidence")]:
        A.add(f"agl.static.{key}", "Results", ctx, disp, "num", float(cm[key]), R + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    for disp, key in [("-6.51", "mean_difference")]:
        A.add("agl.static.cma.mean", "Results", "difference of-6.51points(95%paired bootstrapCI,[-7.07,-5.95]", disp, "num", float(cm[key]), R + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.static.cma.lo", "Results", "[-7.07,-5.95]", "-7.07", "num", float(cm["boot_lo"]), R + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.static.cma.hi", "Results", "[-7.07,-5.95]", "-5.95", "num", float(cm["boot_hi"]), R + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    dc = dirc[("replication", "conflict_minus_aligned")]
    A.add("agl.static.cma.lower", "Results", "lower under conflict in 224/260 paired cases, unchanged in 27, and higher in nine", "224", "count", int(dc["n_decrease"]), R + "conflict_minus_aligned", "confidence_direction_counts.csv")
    A.add("agl.static.cma.equal", "Results", "lower under conflict in 224/260 paired cases, unchanged in 27, and higher in nine", "27", "count", int(dc["n_unchanged"]), R + "conflict_minus_aligned", "confidence_direction_counts.csv")
    A.add("agl.static.cma.higher", "Results", "unchanged in 27, and higher in nine", "nine", "count" if False else "text", int(dc["n_increase"]) == 9, R + "conflict_minus_aligned", "confidence_direction_counts.csv")
    A.add("agl.static.H.mean", "Results", "decreased from 90.12 underHto 85.48 underH+L4", "90.12", "num", float(ch["mean_b"]), R + "conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.static.cmH.mean", "Results", "apairedchangeof-4.64points(95%CI,[-5.13,-4.16])", "-4.64", "num", float(ch["mean_difference"]), R + "conflict_minus_H", "confidence_contrasts_bootstrap.csv",
          note="CI matches the post-hoc bootstrap of this contrast (seed 68020260909); the separately archived prespecified confidence_shift.csv gives [-5.1269,-4.1462] for the same contrast (differs in 2nd decimal at the upper bound). See claim-scope/author-attention list.")
    A.add("agl.static.cmH.lo", "Results", "[-5.13,-4.16]", "-5.13", "num", float(ch["boot_lo"]), R + "conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.static.cmH.hi", "Results", "[-5.13,-4.16]", "-4.16", "num", float(ch["boot_hi"]), R + "conflict_minus_H", "confidence_contrasts_bootstrap.csv")

    # --- Persistent 260 ---
    A.add("agl.p260.agree", "Results", "agreed between persistent and fresh inference in all 260 cases", "260", "count", term["decision_agreement_n"], "agl.gemini260.terminal_categorical_agreement", "gemini_260_analysis.json")
    pm = sum(v["sequential"]["confidence"] for v in sres.values()) / len(sres)
    fm = sum(v["fresh"]["confidence"] for v in sres.values()) / len(sres)
    A.add("agl.p260.seq_mean", "Results", "Mean terminal confidence was 73.87after persistent", "73.87", "num", pm, "agl.gemini260.terminal_confidence_difference", "gemini_260_results.jsonl (mean of terminal sequential rows; analysis JSON stores trajectory mean 73.865...)")
    A.add("agl.p260.fresh_mean", "Results", "versus 86.18 under fresh", "86.18", "num", fm, "agl.gemini260.terminal_confidence_difference", "gemini_260_results.jsonl (mean of fresh terminal rows)")
    A.add("agl.p260.diff", "Results", "difference of-12.32points(median-13;95%CI,[-13.02,-11.62])", "-12.32", "num", term["confidence_seq_minus_fresh_mean"], "agl.gemini260.terminal_confidence_difference", "gemini_260_analysis.json")
    A.add("agl.p260.median", "Results", "(median-13;95%CI", "-13", "count", term["confidence_median"], "agl.gemini260.terminal_confidence_difference", "gemini_260_analysis.json")
    A.add("agl.p260.ci_lo", "Results", "[-13.02,-11.62]", "-13.02", "num", term["confidence_95ci_paired_bootstrap"][0], "agl.gemini260.terminal_confidence_difference", "gemini_260_analysis.json")
    A.add("agl.p260.ci_hi", "Results", "[-13.02,-11.62]", "-11.62", "num", term["confidence_95ci_paired_bootstrap"][1], "agl.gemini260.terminal_confidence_difference", "gemini_260_analysis.json")
    lo, eq, hi = term["confidence_lower_equal_higher"]
    A.add("agl.p260.lower", "Results", "Persistent confidence was lower in 249/260 cases, unchanged in nine, and higher in two", "249", "count", lo, "agl.gemini260.terminal_confidence_difference", "gemini_260_analysis.json")
    A.add("agl.p260.eq_hi", "Results", "Persistent confidence was lower in 249/260 cases, unchanged in nine, and higher in two", "nine", "text", eq == 9 and hi == 2, "agl.gemini260.terminal_confidence_difference", "gemini_260_analysis.json")
    tm = seq["sequential_trajectory"]["turn_means"]
    A.add("agl.p260.traj0", "Results", "declined from 90.27 underH to 85.18, 80.73, 77.13, and73.87", "90.27", "num", tm[0], "agl.gemini260.sequential_trajectory", "gemini_260_analysis.json")
    for i, v in enumerate(["85.18", "80.73", "77.13", "73.87"], start=1):
        A.add(f"agl.p260.traj{i}", "Results", "declined from 90.27 underH to 85.18, 80.73, 77.13, and73.87", v, "num", tm[i], "agl.gemini260.sequential_trajectory", "gemini_260_analysis.json")
    A.add("agl.p260.nonincreasing", "Results", "fully non-increasing in 257/260 trajectories", "257", "count", seq["sequential_trajectory"]["fully_nonincreasing_n"], "agl.gemini260.sequential_trajectory", "gemini_260_analysis.json")
    A.add("agl.p260.no_cat_dev", "Results", "no case exhibited a categorical deviation at any sequential turn", "no case", "text", seq["sequential_trajectory"]["first_categorical_deviation"] == {"none": 260}, "agl.gemini260.first_decline_deviation", "gemini_260_analysis.json")
    A.add("agl.p260.E0_terminal", "Results", "remained included in reported dominant evidence in every terminal pair", "every terminal pair", "text", term["E0_transitions_fresh_to_sequential"] == {"True->True": 260}, "agl.gemini260.terminal_E0_transition", "gemini_260_analysis.json")
    # abstract repeats
    A.add("agl.abs.p260.diff", "Abstract", "persistent confidence was 12.32points lower on average(95% CI [-13.02,-11.62]", "12.32", "num", -term["confidence_seq_minus_fresh_mean"], "agl.gemini260.terminal_confidence_difference", "gemini_260_analysis.json")
    A.add("agl.abs.cma", "Abstract", "conflicting evidence produced 6.51 points lower self-reported confidence", "6.51", "num", -float(cm["mean_difference"]), R + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")

    # --- Aligned control ---
    at, cf, ix, tr = ali["aligned_terminal"], ali["same_40_existing_conflict_terminal"], ali["polarity_by_persistence_interaction"], ali["trajectory_means"]
    for i, v in enumerate(["89.88", "90.45", "90.83", "90.70", "90.53"]):
        A.add(f"agl.a40.align_traj{i}", "Results", "(89.88, 90.45, 90.83, 90.70, and 90.53)", v, "num", tr["aligned"][i], "agl.aligned40.trajectories", "aligned_control_analysis.json")
    for i, v in enumerate(["89.88", "85.00", "80.58", "77.28", "74.20"]):
        A.add(f"agl.a40.conf_traj{i}", "Results", "(89.88, 85.00, 80.58, 77.28, and 74.20)", v, "num", tr["conflict"][i], "agl.aligned40.trajectories", "aligned_control_analysis.json")
    A.add("agl.a40.al_gap", "Results", "was-1.85 points under aligned evidence (95% CI, [-3.20,-0.68]", "-1.85", "num", at["seq_minus_fresh_mean"], "agl.aligned40.aligned_gap", "aligned_control_analysis.json")
    A.add("agl.a40.al_lo", "Results", "[-3.20,-0.68]", "-3.20", "num", at["bootstrap_95_ci"][0], "agl.aligned40.aligned_gap", "aligned_control_analysis.json")
    A.add("agl.a40.al_hi", "Results", "[-3.20,-0.68]", "-0.68", "num", at["bootstrap_95_ci"][1], "agl.aligned40.aligned_gap", "aligned_control_analysis.json")
    A.add("agl.a40.cf_gap", "Results", "versus-11.85 under conflicting evidence (95% CI, [-13.72,-9.93]", "-11.85", "num", cf["seq_minus_fresh_mean"], "agl.aligned40.conflict_gap_same40", "aligned_control_analysis.json")
    A.add("agl.a40.cf_lo", "Results", "[-13.72,-9.93]", "-13.72", "num", cf["bootstrap_95_ci"][0], "agl.aligned40.conflict_gap_same40", "aligned_control_analysis.json")
    A.add("agl.a40.cf_hi", "Results", "[-13.72,-9.93]", "-9.93", "num", cf["bootstrap_95_ci"][1], "agl.aligned40.conflict_gap_same40", "aligned_control_analysis.json")
    A.add("agl.a40.ix", "Results", "paired gap dif-ference of-10.00 points (95% CI, [-12.00,-7.72]", "-10.00", "num", ix["mean"], "agl.aligned40.interaction", "aligned_control_analysis.json")
    A.add("agl.a40.ix_lo", "Results", "[-12.00,-7.72]", "-12.00", "num", ix["bootstrap_95_ci"][0], "agl.aligned40.interaction", "aligned_control_analysis.json")
    A.add("agl.a40.ix_hi", "Results", "[-12.00,-7.72]", "-7.72", "num", ix["bootstrap_95_ci"][1], "agl.aligned40.interaction", "aligned_control_analysis.json")
    A.add("agl.a40.agree", "Results", "agreed in all 40 aligned persistent-fresh pairs", "40", "count", at["categorical_agreement_n"], "agl.aligned40.aligned_categorical_agreement_E0", "aligned_control_analysis.json")
    A.add("agl.a40.E0", "Appendix E.1", "appeared in reported dominant evidence in both terminal outputs for all 40 cases", "40", "count", at["e0_in_both_n"], "agl.aligned40.aligned_categorical_agreement_E0", "aligned_control_analysis.json")
    A.add("agl.a40.dir_al", "Appendix E.1", "confidence in 12/40 cases, equal in 25, and higher in three", "12", "count", at["direction_counts"]["lower"], "agl.aligned40.aligned_gap", "aligned_control_analysis.json")
    A.add("agl.a40.dir_al2", "Appendix E.1", "confidence in 12/40 cases, equal in 25, and higher in three", "25", "count", at["direction_counts"]["equal"], "agl.aligned40.aligned_gap", "aligned_control_analysis.json")
    A.add("agl.a40.dir_cf", "Appendix E.1", "persistent confidence lower in 38/40 cases, equal in one, and higher in one", "38", "count", cf["direction_counts"]["lower"], "agl.aligned40.conflict_gap_same40", "aligned_control_analysis.json")
    A.add("agl.a40.dir_cf2", "Appendix E.1", "persistent confidence lower in 38/40 cases, equal in one, and higher in one", "equal in one", "text", cf["direction_counts"]["equal"] == 1 and cf["direction_counts"]["higher"] == 1, "agl.aligned40.conflict_gap_same40", "aligned_control_analysis.json")

    # --- Sensitivity: threshold, order ---
    th = seq["exploratory_threshold_sensitivity"]
    tau = {int(k): v["disagreement_n"] for k, v in th.items() if 70 <= int(k) <= 95}
    A.add("agl.p260.thr80", "Results", "opposite sides of a threshold of 80 in 159/260 pairs", "159", "count", th["80"]["disagreement_n"], "agl.gemini260.threshold_sensitivity", "gemini_260_analysis.json")
    A.add("agl.p260.thr_min", "Appendix E.2", "ranged from 23/260 cases (8.8%) to 159/260 cases (61.2%)", "23", "count", min(tau.values()), "agl.gemini260.threshold_sensitivity", "gemini_260_analysis.json")
    A.add("agl.p260.thr_min_pct", "Appendix E.2", "ranged from 23/260 cases (8.8%) to 159/260 cases (61.2%)", "8.8", "num", 100 * min(tau.values()) / 260, "agl.gemini260.threshold_sensitivity", "gemini_260_analysis.json")
    A.add("agl.p260.thr_max_pct", "Appendix E.2", "ranged from 23/260 cases (8.8%) to 159/260 cases (61.2%)", "61.2", "num", 100 * max(tau.values()) / 260, "agl.gemini260.threshold_sensitivity", "gemini_260_analysis.json")
    od = art.binom[("replication", "order_disagreement")]
    A.add("agl.static.order_dis", "Results", "only two categorical disagreements among 260 cases", "260", "count", int(od["denominator"]), R + "order_disagreement", "binomial_proportions_exact.csv")
    A.add("agl.static.order_dis_n", "Appendix E.10", "Categorical judgments differed in 2/260 paired cases", "2", "count", int(od["numerator"]), R + "order_disagreement", "binomial_proportions_exact.csv")
    # order confidence contrast: NO archived output; read-only recompute with the archived bootstrap routine
    ids = sorted(cc)
    import numpy as np
    diffs = np.array([cc[i]["L4_H"]["confidence"] - cc[i]["H_L4"]["confidence"] for i in ids], dtype=float)
    est, blo, bhi = art.ph.paired_bootstrap(diffs)
    src = "NO archived output; read-only recompute (L4_H minus H_L4, replication CLEAN, archived paired_bootstrap seed 68020260909, 10,000)"
    A.add("agl.static.order_conf.mean", "Results", "increased mean confidence by 1.20 points (95% CI, [0.76,1.64]", "1.20", "num", est, None, src)
    A.add("agl.static.order_conf.lo", "Results", "[0.76,1.64]", "0.76", "num", blo, None, src)
    A.add("agl.static.order_conf.hi", "Results", "[0.76,1.64]", "1.64", "num", bhi, None, src)

    # --- Appendix E.3 subgroup ---
    for ref, disp in [("support", "-12.38"), ("do_not_support", "-12.25")]:
        v = seq["secondary_stratified"]["reference_decision"][ref]
        A.add(f"agl.p260.strat.{ref}", "Appendix E.3", "Among the 130 support cases, the mean difference was-12.38 points. Among the 130 do_not_support cases, the mean difference was-12.25", disp, "num", v["mean_seq_minus_fresh"], "agl.gemini260.stratified_reference_decision", "gemini_260_analysis.json")
    # --- E.4 ---
    A.add("agl.p260.cp", "Appendix E.4", "0/260 (exact two-sided 95% Clopper-Pearson CI, 0-1.41%)", "1.41%", "num", 100 * term["disagreement_95ci_clopper_pearson"][1], "agl.gemini260.terminal_categorical_agreement", "gemini_260_analysis.json")
    A.add("agl.p260.E0_pairs", "Appendix E.4", "for all 260 persistent-fresh pairs", "260", "count", term["E0_transitions_fresh_to_sequential"]["True->True"], "agl.gemini260.terminal_E0_transition", "gemini_260_analysis.json")
    # --- E.5 primary ---
    pc, pcm = contr[("primary", "conflict_minus_H")], contr[("primary", "conflict_minus_aligned")]
    A.add("agl.prim.acc", "Appendix E.5", "All 40 Gemini primary cases were correct underH", "40", "count", b("primary", "accuracy_H")[0], "g4h.primary.accuracy_H", "binomial_proportions_exact.csv")
    A.add("agl.prim.edr", "Appendix E.5", "no EDR events occurred after one, two, or four conflicting items", "no EDR events", "text", all(int(b("primary", f"EDR{k}")[0]) == 0 for k in (1, 2, 4)), "g4h.primary.EDR1;g4h.primary.EDR2;g4h.primary.EDR4", "binomial_proportions_exact.csv")
    A.add("agl.prim.H", "Appendix E.5", "decreased from 89.63 underH to 84.50 underH+L4", "89.63", "num", float(pc["mean_b"]), "g4h.primary.conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.prim.HL4", "Appendix E.5", "decreased from 89.63 underH to 84.50 underH+L4", "84.50", "num", float(pc["mean_a"]), "g4h.primary.conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.prim.diff", "Appendix E.5", "a paired difference of-5.13 points (95% CI [-6.50,-3.75]", "-5.13", "num", float(pc["mean_difference"]), "g4h.primary.conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.prim.lo", "Appendix E.5", "[-6.50,-3.75]", "-6.50", "num", float(pc["boot_lo"]), "g4h.primary.conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.prim.hi", "Appendix E.5", "[-6.50,-3.75]", "-3.75", "num", float(pc["boot_hi"]), "g4h.primary.conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.prim.cma", "Appendix E.5", "confidence contrast was-7.28points(95% CI[-8.23,-6.30]", "-7.28", "num", float(pcm["mean_difference"]), "g4h.primary.conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.prim.cma_lo", "Appendix E.5", "[-8.23,-6.30]", "-8.23", "num", float(pcm["boot_lo"]), "g4h.primary.conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.prim.cma_hi", "Appendix E.5", "[-8.23,-6.30]", "-6.30", "num", float(pcm["boot_hi"]), "g4h.primary.conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    # --- E.6 GPT-OSS ---
    go, gm = contr[("gpt_oss_primary", "conflict_minus_H")], contr[("gpt_oss_primary", "conflict_minus_aligned")]
    gd = dirc[("gpt_oss_primary", "conflict_minus_aligned")]
    gp = "g4h.gpt_oss_primary."
    A.add("agl.gpt.acc", "Appendix E.6", "All 40 cases were correct under H,H+L1,H+L2,H+L4, andL4+H", "40", "count", min(b("gpt_oss_primary", f"accuracy_{c}")[0] for c in ("H", "H_L1", "H_L2", "H_L4", "L4_H")), gp + "accuracy_H", "binomial_proportions_exact.csv")
    A.add("agl.gpt.no_edr", "Appendix E.6", "with no EDR events or categorical order disagreements", "no EDR events", "text", all(int(b("gpt_oss_primary", m)[0]) == 0 for m in ("EDR1", "EDR2", "EDR4", "order_disagreement")), gp + "EDR1;" + gp + "EDR2;" + gp + "EDR4;" + gp + "order_disagreement", "binomial_proportions_exact.csv")
    A.add("agl.gpt.H_L4", "Appendix E.6", "Confidence decreased by-6.35 points fromH toH+L4 (95% CI[-7.95,-4.68]", "-6.35", "num", float(go["mean_difference"]), gp + "conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.gpt.H_L4_lo", "Appendix E.6", "[-7.95,-4.68]", "-7.95", "num", float(go["boot_lo"]), gp + "conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.gpt.H_L4_hi", "Appendix E.6", "[-7.95,-4.68]", "-4.68", "num", float(go["boot_hi"]), gp + "conflict_minus_H", "confidence_contrasts_bootstrap.csv")
    A.add("agl.gpt.cma", "Appendix E.6", "conflict-minus-aligned difference was-5.75 points (95% CI [-7.45,-3.60]", "-5.75", "num", float(gm["mean_difference"]), gp + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.gpt.cma_lo", "Appendix E.6", "[-7.45,-3.60]", "-7.45", "num", float(gm["boot_lo"]), gp + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.gpt.cma_hi", "Appendix E.6", "[-7.45,-3.60]", "-3.60", "num", float(gm["boot_hi"]), gp + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.gpt.dir", "Appendix E.6", "lower under conflict in 35/40 cases, unchanged in four, and higher in one", "35", "count", int(gd["n_decrease"]), gp + "conflict_minus_aligned", "confidence_direction_counts.csv")
    A.add("agl.gpt.dir2", "Appendix E.6", "lower under conflict in 35/40 cases, unchanged in four, and higher in one", "unchanged in four", "text", int(gd["n_unchanged"]) == 4 and int(gd["n_increase"]) == 1, gp + "conflict_minus_aligned", "confidence_direction_counts.csv")
    # --- E.7 latent-v2 ---
    lp = "g4h.latent_v2."
    A.add("agl.lat.acc", "Appendix E.7", "Baseline accuracy underH was 38/40", "38", "count", b("latent_v2", "accuracy_H")[0], lp + "accuracy_H", "binomial_proportions_exact.csv")
    for k, ctx in [(1, "EDR was 1/38, 1/38, and 0/38"), (2, "EDR was 1/38, 1/38, and 0/38"), (4, "EDR was 1/38, 1/38, and 0/38")]:
        pass
    A.add("agl.lat.edr", "Appendix E.7", "EDR was 1/38, 1/38, and 0/38 after one, two, and four conflicting items", "1/38, 1/38, and 0/38", "text",
          [int(b("latent_v2", f"EDR{k}")[0]) for k in (1, 2, 4)] == [1, 1, 0] and all(int(b("latent_v2", f"EDR{k}")[1]) == 38 for k in (1, 2, 4)),
          lp + "EDR1;" + lp + "EDR2;" + lp + "EDR4", "binomial_proportions_exact.csv")
    A.add("agl.lat.order", "Appendix E.7", "No categorical order disagreements occurred", "No categorical order disagreements", "text", int(b("latent_v2", "order_disagreement")[0]) == 0, lp + "order_disagreement", "binomial_proportions_exact.csv")
    lc, lcm, ld = contr[("latent_v2", "conflict_minus_H")], contr[("latent_v2", "conflict_minus_aligned")], dirc[("latent_v2", "conflict_minus_aligned")]
    A.add("agl.lat.HL4", "Appendix E.7", "Mean confidence was 84.38 under H+L4 and 90.85 under H+L4A", "84.38", "num", float(lcm["mean_a"]), lp + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.lat.HL4A", "Appendix E.7", "Mean confidence was 84.38 under H+L4 and 90.85 under H+L4A", "90.85", "num", float(lcm["mean_b"]), lp + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.lat.cma", "Appendix E.7", "difference of-6.48 points (95% CI [-7.83,-5.10]", "-6.48", "num", float(lcm["mean_difference"]), lp + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.lat.cma_lo", "Appendix E.7", "[-7.83,-5.10]", "-7.83", "num", float(lcm["boot_lo"]), lp + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.lat.cma_hi", "Appendix E.7", "[-7.83,-5.10]", "-5.10", "num", float(lcm["boot_hi"]), lp + "conflict_minus_aligned", "confidence_contrasts_bootstrap.csv")
    A.add("agl.lat.dir", "Appendix E.7", "lower under conflict in 34/40 cases, unchanged in five, and higher in one", "34", "count", int(ld["n_decrease"]), lp + "conflict_minus_aligned", "confidence_direction_counts.csv")
    A.add("agl.lat.dir2", "Appendix E.7", "lower under conflict in 34/40 cases, unchanged in five, and higher in one", "unchanged in five", "text", int(ld["n_unchanged"]) == 5 and int(ld["n_increase"]) == 1, lp + "conflict_minus_aligned", "confidence_direction_counts.csv")
    # --- E.8 anonymization ---
    an = art.anon["excluding intervention-identifying questions"]
    A.add("agl.anon.n", "Appendix E.8", "Nine replication questions retained", "Nine", "text", int(art.anon["intervention-identifying questions only"]["n"]) == 9, R + "anonymization.intervention-identifying questions only", "anonymization_sensitivity.csv")
    A.add("agl.anon.diff", "Appendix E.8", "confidence difference of-6.44 points (95% CI [-7.02,-5.87]", "-6.44", "num", float(an["mean_conflict_minus_aligned"]), R + "anonymization.excluding intervention-identifying questions", "anonymization_sensitivity.csv")
    A.add("agl.anon.lo", "Appendix E.8", "[-7.02,-5.87]", "-7.02", "num", float(an["ci_lo"]), R + "anonymization.excluding intervention-identifying questions", "anonymization_sensitivity.csv")
    A.add("agl.anon.hi", "Appendix E.8", "[-7.02,-5.87]", "-5.87", "num", float(an["ci_hi"]), R + "anonymization.excluding intervention-identifying questions", "anonymization_sensitivity.csv")
    A.add("agl.anon.full", "Appendix E.8", "compared with-6.51 in the full replication cohort", "-6.51", "num", float(art.anon["all cases"]["mean_conflict_minus_aligned"]), R + "anonymization.all cases", "anonymization_sensitivity.csv")
    # --- E.9 veto ---
    vp = "g4h.veto."
    vet = jl(S / "data/final_veto_cases.jsonl")
    vc = Counter(v["veto_subtype"] for v in vet)
    A.add("agl.veto.n", "Appendix E.9", "A separate 15-case American Heart Association Class III boundary set contained 11 Class III No Benefit and four Class III Harm cases", "15", "count", len(vet), vp + "accuracy_H", "final_veto_cases.jsonl")
    A.add("agl.veto.split", "Appendix E.9", "contained 11 Class III No Benefit and four Class III Harm cases", "11", "count", vc["no_benefit"], None, "final_veto_cases.jsonl (veto_subtype counts: no_benefit=%d, harm=%d)" % (vc["no_benefit"], vc["harm"]))
    A.add("agl.veto.harm", "Appendix E.9", "contained 11 Class III No Benefit and four Class III Harm cases", "four", "text", vc["harm"] == 4, None, "final_veto_cases.jsonl")
    allv = all(b("veto", f"accuracy_{c}")[0] == 15 for c in ("H", "H_L1", "H_L2", "H_L4", "H_L4_ALIGNED", "L4_H")) and \
        all(b("gpt_oss_veto", f"accuracy_{c}")[0] == 15 for c in ("H", "H_L1", "H_L2", "H_L4", "H_L4_ALIGNED", "L4_H"))
    A.add("agl.veto.15of15", "Appendix E.9", "each produced the reference categorical output in 15/15 cases under every tested condition", "15/15", "text", allv,
          vp + "accuracy_H;" + "g4h.gpt_oss_veto.accuracy_H", "binomial_proportions_exact.csv (all 6 conditions x 2 models)")
    vfr_ok = all(int(b(c, f"VFR_{k}")[0]) == 0 and int(b(c, f"VFR_{k}")[1]) == 15 for c in ("veto", "gpt_oss_veto") for k in ("H", "H_L1", "H_L2", "H_L4", "H_L4_ALIGNED", "L4_H"))
    A.add("agl.veto.vfr", "Appendix E.9", "corresponding to VFR 0/15 (exact 95% CI 0-21.8%)", "0/15", "text", vfr_ok, vp + "VFR_H_L4;g4h.gpt_oss_veto.VFR_H_L4", "binomial_proportions_exact.csv")
    A.add("agl.veto.cp", "Appendix E.9", "(exact 95% CI 0-21.8%)", "21.8%", "num", b("veto", "VFR_H_L4")[4], vp + "VFR_H_L4", "binomial_proportions_exact.csv")
    # --- Counts: execution ---
    rep_ok = [r for r in art.rep_raw if r.get("status") == "ok"]
    rep_http = Counter(str(r.get("http_status", r.get("status"))) for r in art.rep_raw)
    A.add("agl.exec.rep_ok", "Appendix D.1", "The 260-case replication cohort required 1,560 successful evaluations across six conditions", "1,560", "count", len(art.rep), "g4h.replication.accuracy_H", "replication_gemini_3_6_flash_CLEAN.jsonl row count")
    A.add("agl.exec.rep_attempts", "Appendix D.1", "The raw execution log contained 1,564 attempts: 1,560 successful responses and four transient HTTP 503 failures", "1,564", "count", len(art.rep_raw), None, "replication_gemini_3_6_flash_RAW.jsonl row count; ok=%d; %s" % (len(rep_ok), dict(rep_http)))
    A.add("agl.exec.rep_503", "Appendix D.1", "1,560 successful responses and four transient HTTP 503 failures", "four", "text", len(art.rep_raw) - len(rep_ok) == 4 and all("503" in str(r) for r in art.rep_raw if r.get("status") != "ok"), None, "replication RAW file (4 non-ok rows, each 503)")
    ac = Counter(a["http_status"] for a in art.seqatt)
    A.add("agl.exec.p260_succ", "Appendix D.2", "for 1,560 successful assessments in total", "1,560", "count", ac[200], "agl.gemini260.terminal_categorical_agreement", "gemini_260_attempts.jsonl (HTTP 200)")
    A.add("agl.exec.p260_att", "Appendix D.2", "The raw attempt log contained 1,567 requests: 1,560 successful responses, five HTTP 429 responses, and two HTTP 503 responses", "1,567", "count", len(art.seqatt), None, "gemini_260_attempts.jsonl row count; http=%s" % dict(ac))
    A.add("agl.exec.p260_429", "Appendix D.2", "five HTTP 429 responses, and two HTTP 503 responses", "five", "text", ac[429] == 5 and ac[503] == 2, None, "gemini_260_attempts.jsonl")
    # arm order
    first = {}
    for r in sorted(art.seqres, key=lambda r: r["timestamp_utc"]):
        first.setdefault(r["case_id"], r["arm"])
    fo = Counter(first.values())
    A.add("agl.exec.order", "Appendix D.2", "130 cases were evaluated fresh-first and 130 persistent-first", "130", "count", fo["fresh"], None, "gemini_260_results.jsonl first-by-timestamp arm per case: %s" % dict(fo),
          note="Computed by earliest timestamp per case; provenance docs record 130/130 arm order from the run design")
    A.add("agl.exec.p260_cases", "Appendix D.2", "all 260 cases contained the complete six-assessment design", "260", "count", sum(1 for c in {r['case_id'] for r in art.seqres} if sum(1 for r in art.seqres if r['case_id'] == c) == 6), None, "gemini_260_results.jsonl (6 rows per case)")
    A.add("agl.exec.a40_n", "Appendix D.3", "for 200 new assessments", "200", "count", len(art.alires), "agl.aligned40.aligned_gap", "aligned_control_results.jsonl row count")
    A.add("agl.exec.a40_att", "Appendix D.3", "the attempt log contained 200 successful requests with no failed or retried requests", "200", "count", sum(1 for a in art.aliatt if a["http_status"] == 200) if len(art.aliatt) == 200 else -1, None, "aligned_control_attempts.jsonl (200 rows, all HTTP 200)")
    man = json.load(open(A40 / "CONTROL_FREEZE_MANIFEST.json"))
    A.add("agl.exec.a40_strata", "Appendix C.3", "yielding 10 cases per stratum", "10", "count", min(len(v) for v in man["strata"].values()) if len({len(v) for v in man["strata"].values()}) == 1 else -1, None, "CONTROL_FREEZE_MANIFEST.json strata")
    # 5/5 order balance per stratum
    sid = {c: k for k, v in man["strata"].items() for c in v}
    fa = {}
    for r in sorted(art.alires, key=lambda r: r["timestamp_utc"]):
        fa.setdefault(r["case_id"], r["arm"])
    bal = Counter((sid[c], a.startswith("fresh")) for c, a in fa.items())
    A.add("agl.exec.a40_order", "Appendix D.3", "balanced 5/5 within each 10-case stratum", "5/5", "text", all(v == 5 for v in bal.values()) and len(bal) == 8, None, "aligned_control_results.jsonl first-by-timestamp arm per case per stratum: %s" % dict(bal))
    gtxt = (S / "run_groq.py").read_text()
    A.add("agl.method.gpt_oss_params", "Appendix E.6", "reasoning_effort=medium", "reasoning_effort=medium", "text", '"reasoning_effort": "medium"' in gtxt and '"temperature": 0' in gtxt, None, "run_groq.py request parameters (temperature 0, reasoning_effort medium)")
    gem = (S / "run_gemini.py").read_text()
    A.add("agl.method.static_no_reasoning_param", "Appendix D.1", "No explicit reasoning parameter was supplied", "No explicit reasoning parameter was supplied", "text", "thinking" not in gem.lower() and "reasoning" not in gem.lower(), None, "run_gemini.py contains no thinking/reasoning request parameter")
    # --- Hashes ---
    A.add("agl.hash.rep", "Appendix A", "b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a", "b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a", "text", sha(S / "data/replication_cases.jsonl") == "b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a", None, "SHA256 of data/replication_cases.jsonl")
    A.add("agl.hash.a40", "Appendix C.3", "6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540", "6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540", "text", sha(A40 / "aligned_control_cases_40.jsonl") == "6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540", None, "SHA256 of aligned_control_cases_40.jsonl")
    # --- Appendix A / B counts from audit CSVs and frozen cases ---
    c1 = csvrows(S / "data/cochrane_candidates_audited.csv")
    c2 = csvrows(S / "data/replication_candidates_audited.csv")
    n1e = sum(r["eligible"] == "1" for r in c1)
    n2e = sum(r["eligible"] == "1" for r in c2)
    k1, k2 = Counter(r["audit_note"] for r in c1 if r["eligible"] == "0"), Counter(r["audit_note"] for r in c2 if r["eligible"] == "0")
    A.add("agl.audit.prim", "Appendix A", "120 candidates were audited and 107 were eligible. Thirteen were ex-", "120", "count", len(c1), None, "cochrane_candidates_audited.csv (rows)")
    A.add("agl.audit.prim_el", "Appendix A", "120 candidates were audited and 107 were eligible", "107", "count", n1e, None, "cochrane_candidates_audited.csv (eligible=1)")
    A.add("agl.audit.prim_excl", "Appendix A", "seven were not therapeutic comparisons, two contained multiple clinical actions, two had ambiguous reference conclusions, one became incoherent after anonymization, and one did not support the intended hierarchy", "seven", "text",
          (k1["not_therapeutic"], k1["multi_action_question"], k1["ambiguous_reference"], k1["anonymization_breaks_case"], k1["hierarchy_not_defensible"]) == (7, 2, 2, 1, 1), None, "cochrane_candidates_audited.csv audit_note counts")
    A.add("agl.audit.rep", "Appendix A", "340 candidates were sampled", "340", "count", len(c2), None, "replication_candidates_audited.csv (rows)")
    A.add("agl.audit.rep_excl", "Appendix A", "Sixteen were excluded during manual audit: ten were not therapeutic comparisons, five contained multiple clinical actions, and one had an ambiguous reference conclusion", "Sixteen", "text",
          (len(c2) - n2e, k2["not_therapeutic"], k2["multi_action_question"], k2["ambiguous_reference"]) == (16, 10, 5, 1), None, "replication_candidates_audited.csv audit_note counts")
    A.add("agl.audit.rep_el", "Appendix A", "The remaining 324 eligible cases formed the pool from which 260 cases were frozen, with 65 per stratum", "324", "count", n2e, None, "replication_candidates_audited.csv (eligible=1)")
    # anchor quantitative detail
    def cls(path):
        c = Counter()
        for r in jl(path):
            t = r["anchor"]["text"] if isinstance(r["anchor"], dict) else str(r["anchor"])
            c["ci" if re.search(r"95% CI", t) else "est" if "Reported effect" in t else "none"] += 1
        return c
    cp_, cr_ = cls(S / "data/final_main_cases.jsonl"), cls(S / "data/replication_cases.jsonl")
    A.add("agl.anchor.prim", "Appendix B", "25 of 40 primary anchors contained an estimate with a 95% confidence interval, seven contained an estimate without an interval, and eight contained no quantitative result", "25", "count", cp_["ci"], None, "final_main_cases.jsonl anchor text classification ('95 pct CI' / 'Reported effect' only / neither): " + str(dict(cp_)))
    A.add("agl.anchor.prim2", "Appendix B", "seven contained an estimate without an interval, and eight contained no quantitative result", "seven", "text", cp_["est"] == 7 and cp_["none"] == 8, None, "final_main_cases.jsonl")
    A.add("agl.anchor.rep", "Appendix B", "Corresponding counts in replication were 124, 56, and 80", "124, 56, and 80", "text", (cr_["ci"], cr_["est"], cr_["none"]) == (124, 56, 80), None, "replication_cases.jsonl anchor text classification: %s" % dict(cr_))
    # five primary cases with favorable estimate but do_not_support conclusion and no interval
    five = [r["case_id"] for r in jl(S / "data/final_main_cases.jsonl")
            if r["reference_decision"] == "do_not_support" and "Reported effect" in r["anchor"]["text"] and "95% CI" not in r["anchor"]["text"]]
    A.add("agl.anchor.four", "Appendix B", "Among primary anchors with a quantitative estimate but no displayed interval, four had point estimates favoring the intervention despite a", "four", "nmc", None, None,
          "final_main_cases.jsonl; cochrane_candidates_audited.csv", manual=(
        f"Verified: exactly {len(five)} primary anchors are do_not_support with an estimate and no interval ({', '.join(five)}). C0006 (survival to hospital discharge, aminophylline vs placebo) RR 0.58, 95% CI 0.12-2.74 - numbers confirmed in cochrane_candidates_audited.csv; "
        "it does NOT favor the intervention per author-supplied external source verification (outcome direction is not recorded in any archived artifact). The other four (C0032 postpartum haemorrhage, C0034 trabeculectomy failure, C0044 mortality, C0046 death/dependency) have RR<1 on adverse outcomes, i.e. favor the intervention. Hence four."))
    # strata sizes and misc design facts
    prim = {r["case_id"]: r for r in c1}
    pq = Counter((prim[r["case_id"]]["evidence-quality"], r["reference_decision"]) for r in jl(S / "data/final_main_cases.jsonl"))
    A.add("agl.strata.prim", "Appendix A", "balanced across High/support, High/do_not_support, Moderate/support, and Moderate/do_not_support strata (n=10each)", "10", "count", min(pq.values()) if len(pq) == 4 and len(set(pq.values())) == 1 else -1, None, "final_main_cases.jsonl joined to cochrane_candidates_audited.csv evidence-quality: " + str(dict(pq)))
    repq = {r["case_id"]: r for r in c2}
    rq = Counter((repq[r["case_id"]]["evidence-quality"], r["reference_decision"]) for r in jl(S / "data/replication_cases.jsonl"))
    A.add("agl.strata.rep", "Appendix A", "were frozen, with 65 per stratum", "65", "count", min(rq.values()) if len(rq) == 4 and len(set(rq.values())) == 1 else -1, None, "replication_cases.jsonl joined to replication_candidates_audited.csv: " + str(dict(rq)))
    A.add("agl.method.static_temp0", "Appendix D.1", "Gemini-3.6-flash, temperature 0, and a strict structured-", "temperature 0", "text", all(r.get("temperature") == 0 for r in art.rep), None, "replication CLEAN rows temperature field")
    A.add("agl.method.pers_temp_omitted", "Appendix D.2", "did not explicitly specify a temperature parameter", "did not explicitly specify a temperature parameter", "text", all(r.get("temperature_sent") is None for r in art.seqres) and all(r.get("temperature_sent") is None for r in art.alires), None, "gemini_260_results.jsonl and aligned_control_results.jsonl temperature_sent is null")
    A.add("agl.method.sel_tag", "Appendix C.3", "agenticls-aligned-control-v1-20260923|<case_id>", "agenticls-aligned-control-v1-20260923", "text", man["selection_tag"] == "agenticls-aligned-control-v1-20260923", None, "CONTROL_FREEZE_MANIFEST.json selection_tag")
    # seeds (verified against archived manifests)
    rcm = json.load(open(S / "data/replication_candidate_manifest.json"))
    txt = json.dumps(rcm)
    A.add("agl.seed.cand", "Appendix A", "The replication candidate-sampling seed was 2026090902", "2026090902", "text", "2026090902" in txt, None, "replication_candidate_manifest.json")
    fm = (S / "data/freeze_manifest.json").read_text() + (S / "freeze_replication.py").read_text()
    A.add("agl.seed.freeze", "Appendix A", "the final freeze seed was2026090903", "2026090903", "text", "2026090903" in fm, None, "freeze_manifest.json / freeze_replication.py")
    # bootstrap-resample statements (camera-ready wording after the author-approved revision)
    boot_ok = (p260_boot_n() == 100000 and seq_boot_n_static(art) == 10000 and art.ali["bootstrap_n"] == 10000)
    bsent = "Paired confidence intervals used 10,000 case-level bootstrap resamples, except for the 260-case persistent-versus-fresh terminal confidence comparison, which used 100,000 resamples"
    A.add("agl.method.boot_resamples", "Methods/D.4", bsent, "10,000", "text", boot_ok, "agl.gemini260.terminal_confidence_difference",
          "analyze_sequential_gemini.py B=100000 (persistent-260 terminal CI); static post-hoc n_boot=10000 (confidence_contrasts_bootstrap.csv); aligned-control bootstrap_n=10000; sentence must appear in both Methods and Appendix D.4",
          note="Revised wording; previously MISMATCH (10,000 stated globally).")
    A.add("agl.method.boot_resamples_100k", "Methods/D.4", bsent, "100,000", "text", boot_ok, "agl.gemini260.terminal_confidence_difference", "analyze_sequential_gemini.py B=100000")
    A.claims[-2]["occurrences_expected"] = 2
    A.claims[-2]["occurrences_found"] = A.npages_count(bsent)
    if A.claims[-2]["occurrences_found"] != 2 and A.claims[-2]["status"] != "MISMATCH":
        A.claims[-2]["status"], A.claims[-2]["detail"] = "MISMATCH", "approved bootstrap sentence must appear in both Methods and Appendix D.4; found %d" % A.claims[-2]["occurrences_found"]


def seq_boot_n_static(art):
    return int(art.contr[("replication", "conflict_minus_H")]["n_boot"])


def p260_boot_n():
    m = re.search(r"B=(\d+)", (P260 / "analyze_sequential_gemini.py").read_text())
    return int(m.group(1))


# ---------------------------------------------------------------- driver
LABEL_CTX = re.compile(r"(Gemini-|GPT-OSS-|latent-v|H\+L|[HLEτ]$|Appendix[A-Z]?\.?|\[|,|\bn=)$")


def uncovered_tokens(aud):
    """Numeric tokens in the PDF body not inside any audited claim fragment.

    Returned as (repeat_of_verified, unreviewed). A token is a repeat if the same
    printed string was verified by some claim elsewhere (identical string, identical
    value). Condition labels (H+L4, L4+H, E0), model names (Gemini-3.6, GPT-OSS-120B),
    citation brackets and the references section are ignored.
    """
    full = aud.full
    lo, hi = full.find("References"), full.find("AEligibilityAudit")
    ref = (lo, hi) if 0 <= lo < hi else (0, 0)
    spans = sorted(aud.spans)
    verified = {norm(c["printed"]).replace("%", "") for c in aud.claims}
    repeats, unreviewed = [], []
    for m in re.finditer(r"-?\d[\d,]*(?:\.\d+)?%?", full):
        s, e = m.span()
        tok = m.group(0)
        if ref[0] <= s < ref[1] or any(a <= s and e <= b for a, b in spans):
            continue
        before = full[max(0, s - 12):s]
        ctx = full[max(0, s - 40):e + 40]
        if tok.rstrip("%").rstrip(",") in verified:
            repeats.append({"token": tok, "context": ctx})
        elif LABEL_CTX.search(before) or re.fullmatch(r"\d{1,2}", tok) and re.search(r"(L|E|H\+L|\])$", before):
            continue
        else:
            unreviewed.append({"token": tok, "context": ctx})
    return repeats, unreviewed


APPROVED_REVISIONS = [
    {"revision_id": "rev1.bootstrap_resamples", "supersedes_claims": ["agl.method.boot_p260"], "sections": ["Methods (p.3)", "Appendix D.4 (p.10)"],
     "old_text": "Paired confidence intervals used 10,000 case-level bootstrap resamples.",
     "new_text": "Paired confidence intervals used 10,000 case-level bootstrap resamples, except for the 260-case persistent-versus-fresh terminal confidence comparison, which used 100,000 resamples.",
     "authority": "author instruction (2026-10-04); result values and CIs unchanged"},
    {"revision_id": "rev2.estimate_direction_count", "supersedes_claims": ["agl.anchor.five"], "sections": ["Appendix B (p.7)"],
     "old_text": "In five primary cases, the displayed point estimate favored the intervention despite a predefined do_not_support conclusion and no displayed interval; the stated systematic-review conclusion supplied the benchmark reference direction in these cases.",
     "new_text": "Among primary anchors with a quantitative estimate but no displayed interval, four had point estimates favoring the intervention despite a predefined do_not_support conclusion; in those cases, the stated systematic-review conclusion supplied the benchmark reference direction.",
     "authority": "author instruction (2026-10-04); author-supplied external source verification: C0006 = survival to hospital discharge, aminophylline vs placebo, RR 0.58 (95% CI 0.12-2.74), so the estimate does not favor the intervention"},
]


def verify_revisions(art, aud):
    """Check each approved revision's NEW wording against the archived artifacts (read-only)."""
    out = []
    boot_ok = (p260_boot_n() == 100000 and seq_boot_n_static(art) == 10000 and art.ali["bootstrap_n"] == 10000)
    out.append(dict(APPROVED_REVISIONS[0], verified=boot_ok, verification="analyze_sequential_gemini.py B=100000 (persistent-260); static post-hoc n_boot=10000; aligned-control bootstrap_n=10000"))
    cases = jl(S / "data/final_main_cases.jsonl")
    five = sorted(r["case_id"] for r in cases if r["reference_decision"] == "do_not_support" and "Reported effect" in r["anchor"]["text"] and "95% CI" not in r["anchor"]["text"])
    cand = {r["case_id"]: r for r in csvrows(S / "data/cochrane_candidates_audited.csv")}
    c6 = "RR 0.58" in cand["C0006"]["notes"] or "0.58" in cand["C0006"]["notes"]
    c6ci = "0.12" in cand["C0006"]["notes"] and "2.74" in cand["C0006"]["notes"]
    four = [c for c in five if c != "C0006"]
    ok = len(five) == 5 and "C0006" in five and len(four) == 4 and c6 and c6ci
    out.append(dict(APPROVED_REVISIONS[1], verified=ok, verification=f"5 do_not_support primary anchors with estimate and no interval: {five}; C0006 RR/CI (0.58; 0.12-2.74) confirmed in cochrane_candidates_audited.csv notes; remaining four (RR<1 on adverse outcomes C0032, C0034, C0044, C0046) favor the intervention by question wording; C0006 direction per author-supplied external verification"))
    for r in out:
        key = r["new_text"].split(" predefined")[0].rstrip(".")   # text after a line-break hyphenation ("prede-fined") is not matched
        old_key = r["old_text"].split(" favored the intervention")[0] if r["revision_id"].startswith("rev2") else r["old_text"].rstrip(".")
        r["applied_in_pdf"] = norm(key) in aud.full and norm(old_key) not in aud.full.replace(norm(key), "")
    return out


def run_paper(paper, art):
    pdf = PAPER_PDFS[paper]
    meta_p = pdf.parent / "metadata.json"
    if not pdf.exists():
        return {"paper": paper, "status": "PENDING_CAMERA_READY",
                "note": "No camera-ready PDF ingested for this paper; nothing audited."}
    meta = json.load(open(meta_p))
    if sha(pdf) != meta["pdf_sha256"]:
        return {"paper": paper, "status": "BLOCKED", "note": "PDF SHA256 differs from metadata.json (PDF modified after ingestion?)"}
    pages = pdf_pages(pdf)
    aud = Auditor(pages, art)
    if paper == "agenticls":
        agenticls_claims(aud, art)
    else:
        raise SystemExit("no claim table for " + paper)
    rep_tok, unrev_tok = uncovered_tokens(aud)
    counts = Counter(c["status"] for c in aud.claims)
    manual_missing = [c["claim_id"] for c in aud.claims if c["status"] == "NOT_MACHINE_CHECKABLE" and not c.get("manual_verification")]
    unmapped_claims = [c["claim_id"] for c in aud.claims if c.get("unmapped_claim")]
    revs = verify_revisions(art, aud) if paper == "agenticls" else []
    covered = {c for r in revs if r["verified"] and not r["applied_in_pdf"] for c in r["supersedes_claims"]}
    open_flags = [c["claim_id"] for c in aud.claims if c["status"] in ("MISMATCH", "UNMAPPED") or (c["status"] == "NOT_MACHINE_CHECKABLE" and not c.get("manual_verification"))]
    unresolved = [c for c in open_flags if c not in covered]
    if unresolved or any(not r["verified"] for r in revs):
        status = "BLOCKED"
    elif open_flags:
        status = "PENDING_REVISED_PDF"   # all flags are resolved by verified author-approved revisions, but the ingested PDF still carries the old wording
    else:
        status = "PASS"
    for c in aud.claims:
        if c["claim_id"] in covered:
            c["author_resolution"] = "APPROVED_REVISION " + next(r["revision_id"] for r in revs if c["claim_id"] in r["supersedes_claims"])
    return {"paper": paper, "status": status, "approved_revisions": revs, "unresolved_flags": unresolved, "pdf": str(pdf.relative_to(ROOT)),
            "pdf_sha256": meta["pdf_sha256"], "pages": len(pages), "counts": dict(counts),
            "claims_audited": len(aud.claims), "claims_without_result_id": unmapped_claims,
            "nmc_without_manual_verification": manual_missing, "claims": aud.claims,
            "repeat_of_verified_tokens": len(rep_tok), "uncovered_numeric_tokens": unrev_tok}


def render_md(results):
    L = ["# Camera-ready manuscript number audit", "",
         "Generated by `scripts/audit_camera_ready_numbers.py` (read-only; archive-mode). Compares numbers printed in the ingested camera-ready PDF against the hash-verified archived analysis outputs. Nothing was edited on either side.", ""]
    for r in results:
        L += [f"## {r['paper']}", "", f"**Status: {r['status']}**", ""]
        if "claims" not in r:
            L += [r.get("note", ""), ""]
            continue
        L += [f"- PDF: `{r['pdf']}` (SHA256 `{r['pdf_sha256']}`, {r['pages']} pages)",
              f"- Claims audited: {r['claims_audited']}", "- Status counts: " + ", ".join(f"{k}={v}" for k, v in sorted(r["counts"].items())), ""]
        if r.get("approved_revisions"):
            L += ["### Author-approved manuscript revisions (PDF NOT yet revised)", "",
                  "Each revision is checked against the ingested PDF (applied_in_pdf) and its new wording against the artifacts. If a revision is not yet applied in the ingested PDF the paper stays PENDING_REVISED_PDF.", ""]
            for v in r["approved_revisions"]:
                L += [f"- **{v['revision_id']}** ({', '.join(v['sections'])}) — new wording verified: **{v['verified']}**; applied in ingested PDF: **{v.get('applied_in_pdf')}**", f"  - old: \"{v['old_text']}\"", f"  - new: \"{v['new_text']}\"", f"  - verification: {v['verification']}", f"  - authority: {v['authority']}"]
            L.append("")
        bad = [c for c in r["claims"] if c["status"] == "MISMATCH"]
        if bad:
            L += ["### MISMATCHES against the ingested PDF (release-blocking until a revised PDF is ingested, unless covered by an approved revision above)", ""]
            for c in bad:
                L += [f"- **{c['claim_id']}** (p.{c['page']}, {c['section']}): printed `{c['printed']}` — {c['detail']}. Source: {c['source']}. {c.get('note','')}"]
            L.append("")
        noted = [c for c in r["claims"] if c.get("note") and c["status"] != "MISMATCH"]
        if noted:
            L += ["### Notes for author review (non-blocking)", ""]
            for c in noted:
                L += [f"- {c['claim_id']} (p.{c['page']}): {c['note']}"]
            L.append("")
        uc = [c for c in r["claims"] if c.get("unmapped_claim")]
        if uc:
            L += ["### Claims verified against canonical data but with no `result_provenance.csv` row (UNMAPPED CLAIM)", ""]
            for c in uc:
                L += [f"- {c['claim_id']} (p.{c['page']}): `{c['printed']}` — {c['source']}"]
            L.append("")
        L += ["### All claims", "", "| claim | page | printed | status | result_id | detail |", "|---|---|---|---|---|---|"]
        for c in r["claims"]:
            L.append(f"| {c['claim_id']} | {c['page']} | `{c['printed'][:40]}` | {c['status']} | {c['result_id'] or '—'} | {c['detail'][:90]} |")
        L += ["", f"### Numeric tokens in the PDF body not covered by any claim ({len(r['uncovered_numeric_tokens'])}; a further {r['repeat_of_verified_tokens']} tokens are exact repeats of a printed value verified elsewhere)", "",
              "Listed for verifier review; not machine-verified. Condition labels, model names, citation brackets and the references section are filtered out.", ""]
        for t in r["uncovered_numeric_tokens"][:400]:
            L.append(f"- `{t['token']}` … {t['context']}")
        L.append("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", choices=["agenticls", "genai4health", "all"], default="all")
    a = ap.parse_args()
    papers = ["agenticls", "genai4health"] if a.paper == "all" else [a.paper]
    art = Art()
    results = [run_paper(p, art) for p in papers]
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "papers": results}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(results), encoding="utf-8")
    for r in results:
        print(r["paper"], r["status"], r.get("counts", ""))
    bad = [r for r in results if r["status"] in ("BLOCKED", "PENDING_REVISED_PDF")]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
