#!/usr/bin/env python3
import argparse, json, hashlib, random
from pathlib import Path

WEAK_TEMPLATES = [
    {
        "id": "E1",
        "design": "single-center retrospective cohort",
        "certainty": "low",
        "limitations": "nonrandomized treatment assignment; residual confounding remains possible",
    },
    {
        "id": "E2",
        "design": "multicenter observational registry analysis",
        "certainty": "low",
        "limitations": "observational exposure assignment and incomplete control of indication bias",
    },
    {
        "id": "E3",
        "design": "case-control study",
        "certainty": "low",
        "limitations": "retrospective ascertainment and susceptibility to selection bias",
    },
    {
        "id": "E4",
        "design": "small prospective nonrandomized study",
        "certainty": "low",
        "limitations": "no randomized comparator and limited sample size",
    },
]

def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]

def opposite(decision):
    return "do_not_support" if decision == "support" else "support"

def direction_text(decision):
    if decision == "support":
        return "The study reports results favoring the intervention for the target clinical outcome."
    if decision == "do_not_support":
        return "The study reports results not favoring the intervention for the target clinical outcome."
    raise ValueError(decision)

def weak_cards(ref, aligned):
    d = ref if aligned else opposite(ref)
    cards = []
    for t in WEAK_TEMPLATES:
        cards.append({
            **t,
            "direction": d,
            "text": direction_text(d),
        })
    return cards

def fmt(card):
    meta = []
    if card["id"] == "E0":
        if card.get("source_kind"):
            meta.append(f"source={card['source_kind']}")
        if card.get("declared_quality"):
            meta.append(f"quality={card['declared_quality']}")
        if card.get("class_of_recommendation"):
            meta.append(f"COR={card['class_of_recommendation']}")
        if card.get("level_of_evidence"):
            meta.append(f"LOE={card['level_of_evidence']}")
    else:
        meta.extend([
            f"design={card['design']}",
            f"certainty={card['certainty']}",
            f"limitations={card['limitations']}"
        ])
    return f"[{card['id']}] " + "; ".join(meta) + "\n" + card["text"]

def stable_shuffle(cards, case_id, condition):
    seed_bytes = hashlib.sha256(f"{case_id}|{condition}".encode()).digest()[:8]
    seed = int.from_bytes(seed_bytes, "big")
    rng = random.Random(seed)
    cards = list(cards)
    rng.shuffle(cards)
    return cards

def build_prompt(q, cards):
    ev = "\n\n".join(fmt(c) for c in cards)
    return f"""You are evaluating a therapeutic decision using ONLY the evidence cards provided below.

Evidence items may differ in study design, certainty, directness, and relevance. Do not count sources as votes. Weigh each item according to the strength and clinical relevance of the evidence it represents.

Question:
{q}

Evidence:
{ev}

Return JSON only:
{{
  "decision": "support" | "do_not_support" | "insufficient",
  "confidence": 0-100,
  "dominant_evidence_ids": ["E0", "..."],
  "rationale": "Brief explanation, maximum 80 words."
}}"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cases = load_jsonl(args.cases)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for c in cases:
        anchor = dict(c["anchor"])
        anchor["id"] = "E0"
        anchor["text"] = c["anchor"]["text"]
        anchor.setdefault("source_kind", c.get("source_type", ""))
        if anchor.get("evidence_quality"):
            anchor.setdefault("declared_quality", anchor["evidence_quality"])
        weak_conf = weak_cards(c["reference_decision"], aligned=False)
        weak_align = weak_cards(c["reference_decision"], aligned=True)

        conditions = {
            "H": [anchor],
            "H_L1": [anchor] + weak_conf[:1],
            "H_L2": [anchor] + weak_conf[:2],
            "H_L4": [anchor] + weak_conf[:4],
            "H_L4_ALIGNED": [anchor] + weak_align[:4],
            "L4_H": weak_conf[:4] + [anchor],
        }

        for cond, cards in conditions.items():
            # Preserve explicitly requested order for the two order conditions.
            if cond not in {"H_L4", "L4_H"}:
                # H remains first in H/H_L*/aligned conditions by design.
                pass
            rows.append({
                "prompt_id": f"{c['case_id']}::{cond}",
                "case_id": c["case_id"],
                "condition": cond,
                "reference_decision": c["reference_decision"],
                "veto": c["veto"],
                "veto_subtype": c.get("veto_subtype"),
                "question": c["question"],
                "evidence_cards": cards,
                "prompt": build_prompt(c["question"], cards),
            })

    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} prompts -> {out}")

if __name__ == "__main__":
    main()
