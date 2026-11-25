#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
import pandas as pd
from datasets import load_dataset

SEED = 20260909

RAW_FILES = {
    "systematic": "QA-systematic-review.jsonl",
    "aha": "recommendation-aha-guideline-clean.jsonl",
}

def norm(x):
    return "" if x is None else str(x).strip()

def load_medal(search_dirs):
    """Load the two MEDAL release files.

    Prefers a local copy of the released JSONL files when both are present in
    one of `search_dirs`; otherwise pulls them from the Hub. The records are
    identical either way -- this only changes where the bytes come from, so
    that the pipeline still runs where huggingface.co is unreachable.
    """
    for d in search_dirs:
        if d is None:
            continue
        d = Path(d)
        local = {k: d / v for k, v in RAW_FILES.items()}
        if all(f.is_file() for f in local.values()):
            print(f"Loading MEDAL from local files in {d}")
            # One builder per file: the two releases have different columns,
            # so a single multi-file load casts them to one schema and fails.
            return {
                k: load_dataset("json", data_files=str(v), split="train")
                for k, v in local.items()
            }
    print("Loading MEDAL from the Hugging Face Hub (cwang271/MEDAL)")
    return {
        k: load_dataset("cwang271/MEDAL", data_files=v, split="train")
        for k, v in RAW_FILES.items()
    }

_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4}

def cor_class(x):
    """Numeric AHA Class of Recommendation, or None.

    MEDAL stores COR as free text: 'Class 1', '2A', '2B', 'Class 3: Harm',
    'Class 3: No Benefit'. Roman numerals are accepted too. Only the class
    number is extracted; the harm / no-benefit distinction is deliberately
    left to the manual audit (`veto_subtype`).
    """
    s = norm(x).upper().split(":")[0].replace("CLASS", "").strip()
    m = re.match(r"^(III|II|IV|I|\d+)", s)
    if not m:
        return None
    tok = m.group(1)
    return _ROMAN.get(tok) or (int(tok) if tok.isdigit() else None)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="data")
    ap.add_argument("--main-candidates", type=int, default=120)
    ap.add_argument("--veto-candidates", type=int, default=50)
    ap.add_argument(
        "--raw-dir",
        default=None,
        help="Directory holding local copies of the MEDAL release JSONL files. "
             "Defaults to --out-dir, then the script directory.",
    )
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    ds = load_medal([args.raw_dir, out, Path(__file__).resolve().parent])

    sys_df = ds["systematic"].to_pandas()
    # Normalize likely field names exactly as documented by MEDAL.
    sys_df["answer_norm"] = sys_df["answer"].map(norm).str.lower()
    sys_df["quality_norm"] = sys_df["evidence-quality"].map(norm).str.lower()
    sys_df["notes_norm"] = sys_df["notes"].map(norm)

    main_df = sys_df[
        sys_df["answer_norm"].isin(["yes", "no"]) &
        sys_df["quality_norm"].isin(["high", "moderate"]) &
        (sys_df["notes_norm"].str.len() >= 20)
    ].copy()

    main_df["reference_decision"] = main_df["answer_norm"].map(
        {"yes": "support", "no": "do_not_support"}
    )
    main_df["source_type"] = "cochrane"
    main_df["source_id"] = (
        main_df["doi"].map(norm)
        if "doi" in main_df.columns
        else pd.Series([str(i) for i in range(len(main_df))], index=main_df.index)
    )

    # Stratified candidate pool: answer x evidence quality.
    chunks = []
    selected_idx = set()
    strata = list(main_df.groupby(["answer_norm", "quality_norm"], dropna=False))
    per = max(1, args.main_candidates // max(1, len(strata)))
    for j, (_, g) in enumerate(strata):
        take = g.sample(n=min(per, len(g)), random_state=SEED + j)
        chunks.append(take)
        selected_idx.update(take.index.tolist())
    cand = pd.concat(chunks, axis=0)
    if len(cand) < args.main_candidates:
        remaining = main_df.loc[~main_df.index.isin(selected_idx)]
        if len(remaining):
            extra = remaining.sample(
                n=min(args.main_candidates - len(cand), len(remaining)),
                random_state=SEED + 100
            )
            cand = pd.concat([cand, extra], axis=0)
    cand = cand.head(args.main_candidates).reset_index(drop=True).copy()

    cand["case_id"] = [f"C{i:04d}" for i in range(1, len(cand)+1)]
    cand["eligible"] = ""
    cand["anonymized_question"] = ""
    cand["anonymized_anchor"] = ""
    cand["audit_note"] = ""
    keep = [
        "case_id","source_type","source_id","publication_year","question",
        "reference_decision","evidence-quality","discrepancy","notes",
        "anonymized_question","anonymized_anchor","eligible","audit_note"
    ]
    for k in keep:
        if k not in cand.columns:
            cand[k] = ""
    cand[keep].to_csv(out / "cochrane_candidates.csv", index=False)

    aha = ds["aha"].to_pandas()
    aha["COR_norm"] = aha["COR"].map(norm).str.upper()
    aha["COR_class"] = aha["COR"].map(cor_class)
    aha["LOE_norm"] = aha["LOE"].map(norm).str.upper()
    aha["rec_norm"] = aha["Recommendation"].map(norm)

    veto = aha[
        (aha["COR_class"] == 3) &
        aha["LOE_norm"].str.startswith(("A", "B")) &
        (aha["rec_norm"].str.len() >= 30)
    ].copy()

    veto = veto.sample(
        n=min(args.veto_candidates, len(veto)),
        random_state=SEED
    ).reset_index(drop=True)
    veto["case_id"] = [f"V{i:04d}" for i in range(1, len(veto)+1)]
    veto["source_type"] = "aha_veto"
    veto["source_id"] = (
        veto["id"].map(norm)
        if "id" in veto.columns
        else pd.Series([str(i) for i in range(len(veto))], index=veto.index)
    )
    veto["reference_decision"] = "do_not_support"
    veto["eligible"] = ""
    veto["anonymized_question"] = ""
    veto["anonymized_anchor"] = ""
    veto["veto_subtype"] = ""
    veto["audit_note"] = ""

    vkeep = [
        "case_id","source_type","source_id","Year","COR","LOE","Recommendation",
        "reference_decision","anonymized_question","anonymized_anchor",
        "veto_subtype","eligible","audit_note"
    ]
    for k in vkeep:
        if k not in veto.columns:
            veto[k] = ""
    veto[vkeep].to_csv(out / "aha_veto_candidates.csv", index=False)

    print(f"Wrote {len(cand)} Cochrane candidates and {len(veto)} AHA veto candidates to {out}")

if __name__ == "__main__":
    main()
