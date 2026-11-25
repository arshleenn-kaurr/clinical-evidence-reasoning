#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

BOOT_SEED = 68020260909
N_BOOT = 10000

def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]

def pct_ci(values, stat=np.mean, n=N_BOOT, seed=BOOT_SEED):
    x = np.asarray(values)
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    boots = np.empty(n)
    for i in range(n):
        boots[i] = stat(rng.choice(x, size=len(x), replace=True))
    return float(stat(x)), float(np.quantile(boots, .025)), float(np.quantile(boots, .975))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out-dir", default="analysis")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    res = pd.DataFrame(read_jsonl(args.results))
    cases = pd.DataFrame(read_jsonl(args.cases))
    key = cases[["case_id","reference_decision","veto"]]
    df = res.merge(key, on="case_id", how="left", suffixes=("", "_case"))
    if "reference_decision_case" in df:
        df["reference_decision"] = df["reference_decision_case"].fillna(df.get("reference_decision"))
    df["correct"] = (df["decision"] == df["reference_decision"]).astype(int)

    # Accuracy table
    acc_rows = []
    for (model, cond), g in df.groupby(["model","condition"]):
        est, lo, hi = pct_ci(g["correct"].values)
        acc_rows.append({
            "model": model, "condition": cond, "n": len(g),
            "accuracy": est, "ci_lo": lo, "ci_hi": hi
        })
    pd.DataFrame(acc_rows).to_csv(out / "accuracy_by_condition.csv", index=False)

    # Wide per-case model table
    wide = df.pivot_table(
        index=["model","case_id"], columns="condition",
        values=["decision","confidence","correct"], aggfunc="first"
    )

    edr_rows = []
    order_rows = []
    veto_rows = []

    for model in sorted(df["model"].dropna().unique()):
        dm = df[df["model"] == model]
        h = dm[dm["condition"] == "H"][["case_id","correct","decision","confidence"]].rename(
            columns={"correct":"H_correct","decision":"H_decision","confidence":"H_confidence"}
        )
        base = h[h["H_correct"] == 1].copy()

        for cond, nweak in [("H_L1",1),("H_L2",2),("H_L4",4)]:
            c = dm[dm["condition"] == cond][["case_id","correct","decision","confidence"]]
            m = base.merge(c, on="case_id", how="inner")
            flips = (m["correct"] == 0).astype(int).values
            est, lo, hi = pct_ci(flips)
            edr_rows.append({
                "model": model, "condition": cond, "n_weak": nweak,
                "eligible_H_correct_cases": len(m),
                "EDR": est, "ci_lo": lo, "ci_hi": hi
            })

        a = dm[dm["condition"] == "H_L4"][["case_id","decision"]].rename(columns={"decision":"d1"})
        b = dm[dm["condition"] == "L4_H"][["case_id","decision"]].rename(columns={"decision":"d2"})
        m = a.merge(b, on="case_id")
        os = (m["d1"] != m["d2"]).astype(int).values
        est, lo, hi = pct_ci(os)
        order_rows.append({"model":model,"n":len(m),"order_sensitivity":est,"ci_lo":lo,"ci_hi":hi})

        v = dm[(dm["condition"] == "H_L4") & (dm["veto"] == True)]
        fail = (v["decision"] == "support").astype(int).values
        est, lo, hi = pct_ci(fail)
        veto_rows.append({"model":model,"n":len(v),"veto_failure_rate":est,"ci_lo":lo,"ci_hi":hi})

    pd.DataFrame(edr_rows).to_csv(out / "evidence_dilution_rate.csv", index=False)
    pd.DataFrame(order_rows).to_csv(out / "order_sensitivity.csv", index=False)
    pd.DataFrame(veto_rows).to_csv(out / "veto_failure_rate.csv", index=False)

    # Prespecified secondary metrics:
    # 1. aligned-control delta = accuracy(H_L4_ALIGNED) - accuracy(H_L4)
    # 2. confidence shift from H to H_L4
    # 3. flip threshold among cases correct under H

    aligned_rows = []
    confidence_rows = []
    flip_rows = []

    for model in sorted(df["model"].dropna().unique()):
        dm = df[df["model"] == model]

        # -----------------------------
        # Aligned-control comparison
        # -----------------------------
        h4 = dm[dm["condition"] == "H_L4"][
            ["case_id", "correct"]
        ].rename(columns={"correct": "correct_h4"})

        aligned = dm[dm["condition"] == "H_L4_ALIGNED"][
            ["case_id", "correct"]
        ].rename(columns={"correct": "correct_aligned"})

        m = h4.merge(aligned, on="case_id", how="inner")

        if len(m):
            paired_delta = (
                m["correct_aligned"].astype(float)
                - m["correct_h4"].astype(float)
            ).values

            est, lo, hi = pct_ci(paired_delta)

            aligned_rows.append({
                "model": model,
                "n": len(m),
                "accuracy_H_L4": float(
                    m["correct_h4"].mean()
                ),
                "accuracy_H_L4_ALIGNED": float(
                    m["correct_aligned"].mean()
                ),
                "aligned_control_delta": est,
                "ci_lo": lo,
                "ci_hi": hi,
            })

        # -----------------------------
        # Confidence shift H -> H_L4
        # -----------------------------
        hc = dm[dm["condition"] == "H"][
            ["case_id", "confidence"]
        ].rename(columns={"confidence": "confidence_H"})

        h4c = dm[dm["condition"] == "H_L4"][
            ["case_id", "confidence"]
        ].rename(columns={"confidence": "confidence_H_L4"})

        cm = hc.merge(h4c, on="case_id", how="inner")

        if len(cm):
            cm["confidence_H"] = pd.to_numeric(
                cm["confidence_H"],
                errors="coerce"
            )
            cm["confidence_H_L4"] = pd.to_numeric(
                cm["confidence_H_L4"],
                errors="coerce"
            )
            cm = cm.dropna()

        if len(cm):
            shifts = (
                cm["confidence_H_L4"]
                - cm["confidence_H"]
            ).values

            est, lo, hi = pct_ci(shifts)

            confidence_rows.append({
                "model": model,
                "n": len(cm),
                "mean_confidence_H": float(
                    cm["confidence_H"].mean()
                ),
                "mean_confidence_H_L4": float(
                    cm["confidence_H_L4"].mean()
                ),
                "confidence_shift_H_to_H_L4": est,
                "ci_lo": lo,
                "ci_hi": hi,
            })

        # -----------------------------
        # Flip threshold
        # -----------------------------
        hh = dm[dm["condition"] == "H"][
            ["case_id", "correct"]
        ].rename(columns={"correct": "correct_H"})

        eligible = hh[hh["correct_H"] == 1][
            ["case_id"]
        ].copy()

        for cond, nweak in [
            ("H_L1", 1),
            ("H_L2", 2),
            ("H_L4", 4),
        ]:
            cc = dm[dm["condition"] == cond][
                ["case_id", "correct"]
            ].rename(
                columns={"correct": f"correct_{cond}"}
            )

            eligible = eligible.merge(
                cc,
                on="case_id",
                how="left"
            )

        thresholds = []

        for _, r in eligible.iterrows():
            threshold = None

            for cond, nweak in [
                ("H_L1", 1),
                ("H_L2", 2),
                ("H_L4", 4),
            ]:
                val = r.get(f"correct_{cond}")

                if pd.notna(val) and int(val) == 0:
                    threshold = nweak
                    break

            thresholds.append({
                "model": model,
                "case_id": r["case_id"],
                "H_correct": 1,
                "flip_threshold": (
                    threshold if threshold is not None
                    else ">4"
                ),
                "flipped_by_4": int(
                    threshold is not None
                ),
            })

        flip_rows.extend(thresholds)

    pd.DataFrame(aligned_rows).to_csv(
        out / "aligned_control.csv",
        index=False
    )

    pd.DataFrame(confidence_rows).to_csv(
        out / "confidence_shift.csv",
        index=False
    )

    pd.DataFrame(flip_rows).to_csv(
        out / "flip_threshold.csv",
        index=False
    )

    # Raw merged results for audit.
    df.to_csv(out / "merged_scored_results.csv", index=False)
    print(f"Analysis written to {out}")

if __name__ == "__main__":
    main()
