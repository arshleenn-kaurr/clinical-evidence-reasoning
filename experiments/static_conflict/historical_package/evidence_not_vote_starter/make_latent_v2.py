#!/usr/bin/env python3

import copy
import csv
import json
import re
from collections import Counter
from pathlib import Path

CASES = Path("data/final_main_cases.jsonl")
AUDIT = Path("data/cochrane_candidates_audited.csv")
PROMPTS = Path("data/final_main_prompts.jsonl")

OUT = Path("data/latent_v2_main_prompts.jsonl")
AUDIT_OUT = Path("data/latent_v2_anchor_audit.csv")


def load_jsonl(path):
    return [
        json.loads(x)
        for x in open(path, encoding="utf-8")
        if x.strip()
    ]


# Cases whose source result is better represented directly than by
# generic effect-measure extraction.
MANUAL = {
    "C0074":
        "Systematic-review evidence. For the target outcome, "
        "Intervention A produced more rapid pain relief than the "
        "alternative routes of administration.",

    "C0077":
        "Systematic-review evidence. For the target outcome, "
        "Intervention A and Comparator B showed similar effectiveness "
        "for iodine-131 thyroid remnant ablation.",

    "C0020":
        "Systematic-review evidence. Overall survival and "
        "recurrence-free survival were similar between the treatment "
        "arms, except for one trial reporting lower survival with "
        "chemotherapy.",

    "C0014":
        "Systematic-review evidence. The comparison found no reduction "
        "in stroke risk with Intervention A relative to Comparator B.",

    "C0015":
        "Systematic-review evidence. The pooled comparison found no "
        "statistically significant improvement in symptoms with "
        "Intervention A relative to placebo.",

    "C0026":
        "Systematic-review evidence. No statistically significant "
        "improvement in asthma control was observed with Intervention A "
        "relative to control.",

    "C0091":
        "Systematic-review evidence. Intervention A was associated with "
        "a mean reduction of 1.5 recurrent acute otitis media episodes "
        "during the first six months relative to no treatment.",

    "C0098":
        "Systematic-review evidence. Five randomized trials at the "
        "lowest reported risk of bias found improvements in both "
        "medication adherence and clinical outcomes with Intervention A.",

    "C0086":
        "Systematic-review evidence. At least 50% pain relief was "
        "achieved by 73% receiving Intervention A versus 52% receiving "
        "Comparator B.",

    "C0087":
        "Systematic-review evidence. The target outcome differed by "
        "-13.36 units with Intervention A relative to placebo "
        "(95% CI -16.13 to -10.58).",

    "C0101":
        "Systematic-review evidence. Time to return to sport was "
        "4.88 days shorter with Intervention A than Comparator B "
        "(95% CI 1.50 to 8.25 days shorter).",
}


EFFECT_PATTERNS = [
    (
        "RR",
        r"(?:risk ratio(?:\s*\(RR\))?|relative risk(?:\s*\(RR\))?|\bRR\b)"
        r"[^0-9\-]{0,50}(-?\d+(?:\.\d+)?)"
    ),
    (
        "OR",
        r"(?:odds ratio(?:\s*\(OR\))?|Peto OR|\bOR\b)"
        r"[^0-9\-]{0,50}(-?\d+(?:\.\d+)?)"
    ),
    (
        "HR",
        r"(?:hazard ratio(?:\s*\(HR\))?|\bHR\b)"
        r"[^0-9\-]{0,50}(-?\d+(?:\.\d+)?)"
    ),
    (
        "SMD",
        r"(?:standardized mean difference|standardised mean difference|\bSMD\b)"
        r"[^0-9\-]{0,50}(-?\d+(?:\.\d+)?)"
    ),
    (
        "MD",
        r"(?:mean difference|\bMD\b)"
        r"[^0-9\-]{0,50}(-?\d+(?:\.\d+)?)"
    ),
    (
        "WMD",
        r"(?:weighted mean difference|\bWMD\b)"
        r"[^0-9\-]{0,50}(-?\d+(?:\.\d+)?)"
    ),
]


CI_PATTERN = re.compile(
    r"(95|99)%\s*"
    r"(?:confidence interval(?:\s*\(CI\))?|credible interval|CI|CrI)?"
    r"[^0-9\-]{0,20}"
    r"(-?\d+(?:\.\d+)?)%?"
    r"\s*(?:to|[-–—])\s*"
    r"(-?\d+(?:\.\d+)?)%?",
    re.I,
)


def neutral_anchor(cid, row):
    if cid in MANUAL:
        return MANUAL[cid]

    note = str(row.get("notes", "")).strip()

    found = None

    for label, pattern in EFFECT_PATTERNS:
        m = re.search(pattern, note, re.I)
        if m:
            found = (label, m.group(1))
            break

    ci = CI_PATTERN.search(note)

    if not found or not ci:
        raise ValueError(
            f"{cid}: could not construct a self-contained "
            f"effect + CI card from source notes:\n{note}"
        )

    label, value = found
    level, lo, hi = ci.groups()

    return (
        "Systematic-review evidence. "
        "For the target outcome in the clinical question, "
        f"the reported estimate was {label} {value} "
        f"({level}% CI {lo} to {hi})."
    )


def scrub_card(card, e0_text):
    card = copy.deepcopy(card)

    # Remove explicit evidence-strength labels from ALL cards.
    for key in [
        "evidence_quality",
        "declared_quality",
        "quality",
        "certainty",
    ]:
        card.pop(key, None)

    if card.get("id") == "E0":
        # Keep only design + evidence content.
        card = {
            "id": "E0",
            "design": "systematic review/meta-analysis",
            "text": e0_text,
        }
    else:
        # Direction is already expressed in the evidence text.
        # Do not hand the model an extra hidden categorical label.
        card.pop("direction", None)
        card.pop("source_kind", None)

    return card


def render_prompt(question, cards):
    parts = [
        "You are evaluating a therapeutic decision using ONLY the "
        "evidence cards provided below.",
        "",
        "Evidence items may differ in study design, sample size, "
        "precision, limitations, and clinical relevance. Do not count "
        "sources as votes. Weigh each item according to the "
        "methodological strength and clinical relevance of the evidence "
        "it represents.",
        "",
        "Question:",
        question,
        "",
        "Evidence:",
    ]

    for c in cards:
        meta = []

        if c.get("design"):
            meta.append(f"design={c['design']}")

        if c.get("limitations"):
            meta.append(f"limitations={c['limitations']}")

        header = f"[{c['id']}]"

        if meta:
            header += " " + "; ".join(meta)

        parts.append(header)
        parts.append(c["text"])
        parts.append("")

    parts.extend([
        "Return JSON only:",
        '{'
        '"decision":"support" | "do_not_support" | "insufficient",'
        '"confidence":0-100,'
        '"dominant_evidence_ids":["E0","..."],'
        '"rationale":"Brief explanation, maximum 80 words."'
        '}'
    ])

    return "\n".join(parts)


cases = load_jsonl(CASES)
prompts = load_jsonl(PROMPTS)

assert len(cases) == 40, len(cases)
assert len(prompts) == 240, len(prompts)

with open(AUDIT, encoding="utf-8-sig", newline="") as f:
    audit_rows = list(csv.DictReader(f))

audit = {
    r["case_id"]: r
    for r in audit_rows
}

case_ids = {
    c["case_id"]
    for c in cases
}

missing = sorted(case_ids - set(audit))

if missing:
    raise RuntimeError(
        f"Missing primary cases from audited CSV: {missing}"
    )

anchors = {}

for cid in sorted(case_ids):
    anchors[cid] = neutral_anchor(cid, audit[cid])

# Save an explicit provenance table.
with open(
    AUDIT_OUT,
    "w",
    encoding="utf-8",
    newline=""
) as f:
    w = csv.writer(f)
    w.writerow([
        "case_id",
        "reference_decision",
        "source_notes",
        "latent_v2_anchor",
    ])

    case_map = {
        c["case_id"]: c
        for c in cases
    }

    for cid in sorted(case_ids):
        w.writerow([
            cid,
            case_map[cid]["reference_decision"],
            audit[cid]["notes"],
            anchors[cid],
        ])


out = []

for p in prompts:
    cid = p["case_id"]

    q = copy.deepcopy(p)

    cards = [
        scrub_card(c, anchors[cid])
        for c in q["evidence_cards"]
    ]

    q["evidence_cards"] = cards
    q["prompt"] = render_prompt(
        q["question"],
        cards
    )

    q["prompt_id"] = (
        "LATENTV2_" + str(q["prompt_id"])
    )

    q["ablation"] = (
        "latent_hierarchy_v2_posthoc"
    )

    out.append(q)


# ---------------------------------------------------------
# HARD PRE-INFERENCE AUDITS
# ---------------------------------------------------------

assert len(out) == 240

conditions = Counter(
    r["condition"]
    for r in out
)

expected = {
    "H": 40,
    "H_L1": 40,
    "H_L2": 40,
    "H_L4": 40,
    "H_L4_ALIGNED": 40,
    "L4_H": 40,
}

assert dict(conditions) == expected, conditions


BANNED_IN_RENDERED_PROMPT = [
    "quality=",
    "certainty=",
    "high quality",
    "moderate quality",
    "high-quality",
    "moderate-quality",
    "high certainty",
    "moderate certainty",
    "declared_quality",
    "evidence_quality",
    "supports the proposition",
    "does not support the proposition",
]

hits = []

for r in out:
    text = r["prompt"].lower()

    for banned in BANNED_IN_RENDERED_PROMPT:
        if banned.lower() in text:
            hits.append(
                (r["prompt_id"], banned)
            )

if hits:
    print("\nSTOP — ANSWER/HIERARCHY CUES REMAIN:")
    for x in hits[:50]:
        print(x)
    raise SystemExit(1)


# Ensure no explicit quality/certainty metadata survived in cards.
for r in out:
    for card in r["evidence_cards"]:
        for forbidden_key in [
            "quality",
            "certainty",
            "evidence_quality",
            "declared_quality",
        ]:
            if forbidden_key in card:
                raise RuntimeError(
                    f"{r['prompt_id']} still contains "
                    f"{forbidden_key}"
                )


with open(
    OUT,
    "w",
    encoding="utf-8",
    newline="\n"
) as f:
    for r in out:
        f.write(
            json.dumps(
                r,
                ensure_ascii=False
            ) + "\n"
        )


print("=" * 72)
print("LATENT V2 — PRE-INFERENCE AUDIT")
print("=" * 72)
print("CASES:", len(case_ids))
print("PROMPTS:", len(out))
print("CONDITIONS:", conditions)
print("EXPLICIT QUALITY/CERTAINTY CUE HITS:", len(hits))

print("\n40 E0 CARDS:")
for cid in sorted(anchors):
    print(f"{cid}: {anchors[cid]}")

print("\nLATENT V2 PROMPTS PASS")
print("WROTE:", OUT)
print("AUDIT:", AUDIT_OUT)
