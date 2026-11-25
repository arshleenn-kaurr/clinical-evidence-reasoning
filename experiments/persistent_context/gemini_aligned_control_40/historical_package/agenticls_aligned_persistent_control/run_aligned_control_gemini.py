#!/usr/bin/env python3
"""AgenticLS aligned persistent-context control on Gemini 3.6 Flash.

Post-hoc control designed to probe the generic multi-turn-drift alternative.

For each frozen case, the runner reuses the *existing successful persistent H turn*
from the completed conflicting-evidence experiment as an identical branch point,
then runs:
  * aligned persistent continuation: +L1_A -> +L2_A -> +L3_A -> +L4_A (4 new calls)
  * fresh aligned terminal arm: H+L1_A+L2_A+L3_A+L4_A in a new conversation (1 new call)

Thus 5 new calls/case. With 40 frozen cases: 200 successful new calls total.

Only successful aligned sequential responses enter later conversation history.
Failed attempts are retained in a separate attempts JSONL. Resume-safe: rerun the
identical command with identical paths after interruption.

Uses only Python standard library. Set GEMINI_API_KEY before running.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

API_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODEL = "gemini-3.6-flash"
SELECTION_TAG = "agenticls-aligned-control-v1-20260923"

HISTORICAL_TEMPERATURE = 0
SAMPLING_NOTE = (
    "Historical static benchmark supplied temperature=0; the completed persistent-context "
    "experiment omitted sampling fields. This control matches that persistent runner and also "
    "omits temperature/top_p/top_k."
)

WEAK = [
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

SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {
            "type": "string",
            "enum": ["support", "do_not_support", "insufficient"],
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 100},
        "dominant_evidence_ids": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
    },
    "required": ["decision", "confidence", "dominant_evidence_ids", "rationale"],
    "additionalProperties": False,
}


class RateLimitExhausted(RuntimeError):
    pass


class FatalAPIError(RuntimeError):
    pass


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path, row):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
        f.flush()


def canonical_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def direction_text(direction):
    if direction == "support":
        return "The study reports results favoring the intervention for the target clinical outcome."
    if direction == "do_not_support":
        return "The study reports results not favoring the intervention for the target clinical outcome."
    raise ValueError(f"Unsupported reference decision: {direction}")


def aligned_cards_for(case):
    anchor = dict(case["anchor"])
    anchor.update({"id": "E0", "source_kind": case.get("source_type", "")})
    if anchor.get("evidence_quality"):
        anchor["declared_quality"] = anchor["evidence_quality"]

    weak = []
    for template in WEAK:
        card = dict(template)
        card["direction"] = case["reference_decision"]
        card["text"] = direction_text(card["direction"])
        weak.append(card)
    return anchor, weak


def format_card(card):
    if card["id"] == "E0":
        meta = []
        if card.get("source_kind"):
            meta.append(f"source={card['source_kind']}")
        if card.get("declared_quality"):
            meta.append(f"quality={card['declared_quality']}")
    else:
        meta = [
            f"design={card['design']}",
            f"certainty={card['certainty']}",
            f"limitations={card['limitations']}",
        ]
    return f"[{card['id']}] " + "; ".join(meta) + "\n" + card["text"]


def batch_prompt(question, cards):
    evidence = "\n\n".join(format_card(card) for card in cards)
    return f'''You are evaluating a therapeutic decision using ONLY the evidence cards provided below.

Evidence items may differ in study design, certainty, directness, and relevance. Do not count sources as votes. Weigh each item according to the strength and clinical relevance of the evidence it represents.

Question:
{question}

Evidence:
{evidence}

Return JSON only:
{{
  "decision": "support" | "do_not_support" | "insufficient",
  "confidence": 0-100,
  "dominant_evidence_ids": ["E0", "..."],
  "rationale": "Brief explanation, maximum 80 words."
}}'''


def update_message(card):
    return f'''Additional evidence has arrived for the same therapeutic question:

{format_card(card)}

Update the assessment using all evidence cards supplied in this conversation. The original evidence-weighting instructions continue to apply. Return the same JSON object only.'''


def validate_answer(obj):
    if not isinstance(obj, dict):
        raise ValueError("response is not an object")
    if obj.get("decision") not in {"support", "do_not_support", "insufficient"}:
        raise ValueError("invalid decision")
    obj["confidence"] = float(obj["confidence"])
    if not 0 <= obj["confidence"] <= 100:
        raise ValueError("confidence out of range")
    if not isinstance(obj.get("dominant_evidence_ids"), list):
        raise ValueError("dominant_evidence_ids is not a list")
    obj["dominant_evidence_ids"] = [str(x) for x in obj["dominant_evidence_ids"]]
    if not isinstance(obj.get("rationale"), str):
        raise ValueError("rationale is not a string")
    extra = set(obj) - {"decision", "confidence", "dominant_evidence_ids", "rationale"}
    if extra:
        raise ValueError(f"unexpected output fields: {sorted(extra)}")
    return obj


def parse_retry_after(headers, attempt):
    raw = headers.get("Retry-After") if headers else None
    if raw:
        try:
            return max(0.0, float(raw))
        except ValueError:
            pass
    base = min(60.0, 2 ** attempt)
    return base + random.Random(attempt).random() * 0.25


def to_gemini_contents(messages):
    contents = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else msg["role"]
        if role not in {"user", "model"}:
            raise ValueError(f"Unsupported Gemini conversation role: {role}")
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    if contents and contents[-1]["role"] != "user":
        raise ValueError("Gemini request must end with a user turn")
    return contents


def make_request_body(messages):
    return {
        "contents": to_gemini_contents(messages),
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": SCHEMA,
        },
    }


def extract_response_text(provider):
    candidates = provider.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini response has no candidates")
    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    texts = []
    for part in parts:
        if part.get("thought") is True:
            continue
        t = part.get("text")
        if isinstance(t, str):
            texts.append(t)
    raw = "".join(texts).strip()
    if not raw:
        raise RuntimeError("Gemini response has no non-thought text")
    return raw, candidates[0]


def call_gemini(messages, api_key, model, retries, attempt_log, meta):
    body = make_request_body(messages)
    request_sha = hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    url = API_TEMPLATE.format(model=urllib.parse.quote(model, safe="-._"))

    for attempt in range(1, retries + 1):
        started = time.time()
        started_at = utc_now()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "agenticls-aligned-persistent-control/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                raw_bytes = response.read()
                status_code = response.status
                headers = dict(response.headers.items())
            provider = json.loads(raw_bytes.decode("utf-8", "replace"))
            raw_text, candidate = extract_response_text(provider)
            answer = validate_answer(json.loads(raw_text))
            append_jsonl(
                attempt_log,
                {
                    **meta,
                    "attempt": attempt,
                    "status": "ok",
                    "http_status": status_code,
                    "request_sha256": request_sha,
                    "started_at_utc": started_at,
                    "elapsed_seconds": round(time.time() - started, 6),
                    "finish_reason": candidate.get("finishReason"),
                    "usage_metadata": provider.get("usageMetadata", {}),
                    "model_version": provider.get("modelVersion"),
                    "response_headers": {
                        k: v for k, v in headers.items()
                        if k.lower() in {"retry-after", "x-request-id", "x-goog-request-id"}
                    },
                    "raw_provider_response": provider,
                },
            )
            return answer, raw_text, provider, candidate, attempt, request_sha
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", "replace")
            append_jsonl(
                attempt_log,
                {
                    **meta,
                    "attempt": attempt,
                    "status": "http_error",
                    "http_status": exc.code,
                    "request_sha256": request_sha,
                    "started_at_utc": started_at,
                    "elapsed_seconds": round(time.time() - started, 6),
                    "error_body": response_body,
                },
            )
            if exc.code in {400, 401, 403, 404}:
                raise FatalAPIError(f"HTTP {exc.code}: {response_body}") from exc
            if exc.code == 429:
                if attempt >= retries:
                    raise RateLimitExhausted(
                        "Gemini rate/quota limit remained active after retries. Stop now and resume later "
                        "with the identical command and output paths."
                    ) from exc
                time.sleep(parse_retry_after(exc.headers, attempt))
                continue
            if exc.code in {408, 409, 500, 502, 503, 504} and attempt < retries:
                time.sleep(parse_retry_after(exc.headers, attempt))
                continue
            raise RuntimeError(f"HTTP {exc.code}: {response_body}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
            append_jsonl(
                attempt_log,
                {
                    **meta,
                    "attempt": attempt,
                    "status": "client_or_parse_error",
                    "request_sha256": request_sha,
                    "started_at_utc": started_at,
                    "elapsed_seconds": round(time.time() - started, 6),
                    "error": repr(exc),
                },
            )
            if attempt < retries:
                time.sleep(parse_retry_after({}, attempt))
                continue
            raise


def case_stratum(case):
    return (case.get("anchor", {}).get("evidence_quality", ""), case["reference_decision"])


def build_arm_plan(cases):
    """Exactly 5 sequential-first / 5 fresh-first within each 10-case stratum."""
    groups = defaultdict(list)
    for case in cases:
        groups[case_stratum(case)].append(case)
    plan = {}
    for key, items in groups.items():
        if len(items) != 10:
            raise ValueError(f"Expected 10 cases in frozen control stratum {key}; got {len(items)}")
        ordered = sorted(
            items,
            key=lambda c: hashlib.sha256(("arm-order-v1|" + c["case_id"]).encode()).hexdigest(),
        )
        seq_ids = {c["case_id"] for c in ordered[:5]}
        for case in ordered:
            plan[case["case_id"]] = "sequential" if case["case_id"] in seq_ids else "fresh"
    return plan


def successful_rows(path):
    return [r for r in load_jsonl(path) if r.get("status") == "ok"]


def completed_ids(path):
    return {r["run_id"] for r in successful_rows(path)}


def load_source_h(source_results, cases, model):
    wanted = {c["case_id"]: c for c in cases}
    found = defaultdict(list)
    for r in successful_rows(source_results):
        if r.get("case_id") in wanted and r.get("arm") == "sequential" and r.get("condition") == "H":
            found[r["case_id"]].append(r)
    source = {}
    for cid, case in wanted.items():
        rows = found.get(cid, [])
        if len(rows) != 1:
            raise RuntimeError(f"Expected exactly one successful source sequential H row for {cid}; got {len(rows)}")
        row = rows[0]
        if row.get("model") != model:
            raise RuntimeError(f"Source H model mismatch for {cid}: {row.get('model')} != {model}")
        anchor, _ = aligned_cards_for(case)
        h_prompt = batch_prompt(case["question"], [anchor])
        expected_sha = sha256_text(h_prompt)
        if row.get("prompt_sha256") and row.get("prompt_sha256") != expected_sha:
            raise RuntimeError(f"Source H prompt hash mismatch for {cid}")
        validate_answer(json.loads(row["raw_text"]))
        source[cid] = row
    return source


def row_base(case, args, arm, step, condition, new_evidence_id, prompt_text, messages, source_h=None):
    row = {
        "run_id": f"{case['case_id']}::{arm}::{condition}",
        "case_id": case["case_id"],
        "arm": arm,
        "step": step,
        "condition": condition,
        "new_evidence_id": new_evidence_id,
        "evidence_ids_available": [f"E{i}" for i in range(step)],
        "evidence_polarity": "aligned",
        "reference_decision": case["reference_decision"],
        "model": args.model,
        "temperature_sent": None,
        "sampling_parameters_note": SAMPLING_NOTE,
        "thinking_configuration": "provider_default_no_explicit_thinking_parameter",
        "response_schema_mode": "responseJsonSchema",
        "prompt_sha256": sha256_text(prompt_text),
        "message_count": len(messages),
        "timestamp_utc": utc_now(),
        "selection_tag": SELECTION_TAG,
    }
    if source_h is not None:
        row.update({
            "source_h_run_id": source_h["run_id"],
            "source_h_raw_text_sha256": sha256_text(source_h["raw_text"]),
            "source_h_prompt_sha256": source_h.get("prompt_sha256"),
            "source_h_timestamp_utc": source_h.get("timestamp_utc"),
            "source_h_model_version": source_h.get("model_version"),
        })
    return row


def reconstruct_aligned_history(case, anchor, weak, source_h, output, before_step):
    # Exact branch point: original H user prompt + original successful H model output.
    h_prompt = batch_prompt(case["question"], [anchor])
    messages = [
        {"role": "user", "content": h_prompt},
        {"role": "assistant", "content": source_h["raw_text"]},
    ]
    if before_step <= 2:
        return messages
    rows = [
        r for r in successful_rows(output)
        if r.get("case_id") == case["case_id"] and r.get("arm") == "aligned_sequential"
    ]
    by_step = {r["step"]: r for r in rows}
    for step in range(2, before_step):
        if step not in by_step:
            raise RuntimeError(f"Cannot resume {case['case_id']} step {before_step}: missing aligned step {step}")
        card = weak[step - 2]
        messages.append({"role": "user", "content": update_message(card)})
        messages.append({"role": "assistant", "content": by_step[step]["raw_text"]})
    return messages


def run_aligned_sequential(case, anchor, weak, source_h, key, args, done):
    states = [
        (2, "H_L1_ALIGNED", weak[0]),
        (3, "H_L2_ALIGNED", weak[1]),
        (4, "H_L3_ALIGNED", weak[2]),
        (5, "H_L4_ALIGNED", weak[3]),
    ]
    for step, condition, new_card in states:
        run_id = f"{case['case_id']}::aligned_sequential::{condition}"
        if run_id in done:
            continue
        history = reconstruct_aligned_history(case, anchor, weak, source_h, args.output, before_step=step)
        user_text = update_message(new_card)
        request_messages = history + [{"role": "user", "content": user_text}]
        base = row_base(case, args, "aligned_sequential", step, condition, new_card["id"], user_text, request_messages, source_h)
        base["history_turns_before"] = len(history) // 2
        meta = {k: base[k] for k in ["run_id", "case_id", "arm", "step", "condition"]}
        try:
            answer, raw_text, provider, candidate, attempts, request_sha = call_gemini(
                request_messages, key, args.model, args.retries, args.attempt_log, meta
            )
            append_jsonl(args.output, {
                **base, **answer, "status": "ok", "raw_text": raw_text,
                "attempts": attempts, "request_sha256": request_sha,
                "finish_reason": candidate.get("finishReason"),
                "usage_metadata": provider.get("usageMetadata", {}),
                "model_version": provider.get("modelVersion"),
            })
        except (RateLimitExhausted, FatalAPIError):
            raise
        except Exception as exc:
            append_jsonl(args.output, {**base, "status": "error", "error": repr(exc)})
            return
        time.sleep(args.sleep)
        done = completed_ids(args.output)


def run_fresh_aligned(case, anchor, weak, key, args, done):
    condition = "H_L4_ALIGNED"
    run_id = f"{case['case_id']}::fresh_aligned::{condition}"
    if run_id in done:
        return
    prompt = batch_prompt(case["question"], [anchor, *weak])
    messages = [{"role": "user", "content": prompt}]
    base = row_base(case, args, "fresh_aligned", 5, condition, None, prompt, messages)
    meta = {k: base[k] for k in ["run_id", "case_id", "arm", "step", "condition"]}
    try:
        answer, raw_text, provider, candidate, attempts, request_sha = call_gemini(
            messages, key, args.model, args.retries, args.attempt_log, meta
        )
        append_jsonl(args.output, {
            **base, **answer, "status": "ok", "raw_text": raw_text,
            "attempts": attempts, "request_sha256": request_sha,
            "finish_reason": candidate.get("finishReason"),
            "usage_metadata": provider.get("usageMetadata", {}),
            "model_version": provider.get("modelVersion"),
        })
    except (RateLimitExhausted, FatalAPIError):
        raise
    except Exception as exc:
        append_jsonl(args.output, {**base, "status": "error", "error": repr(exc)})
    time.sleep(args.sleep)


def dry_run(cases, source_h, args, arm_plan):
    print(f"model={args.model}")
    print("new_calls_per_case=5 (4 aligned sequential continuations + 1 fresh aligned terminal)")
    print("source_branch=existing successful sequential H response from completed conflict experiment")
    print("sampling_parameters_sent=none")
    for case in cases:
        anchor, weak = aligned_cards_for(case)
        print(
            case["case_id"],
            f"stratum={case_stratum(case)}",
            f"arm-first={arm_plan[case['case_id']]}",
            "source_H=" + source_h[case["case_id"]]["run_id"],
            "L1A_update_sha256=" + sha256_text(update_message(weak[0]))[:16],
            "fresh_HL4A_sha256=" + sha256_text(batch_prompt(case["question"], [anchor, *weak]))[:16],
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--source-results", required=True, help="Completed gemini_260_results.jsonl from the conflict persistent experiment")
    ap.add_argument("--output", required=True)
    ap.add_argument("--attempt-log")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--retries", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.attempt_log is None:
        out = Path(args.output)
        args.attempt_log = str(out.with_name(out.stem + "_attempts.jsonl"))

    cases = load_jsonl(args.cases)
    if args.limit:
        cases = cases[:args.limit]
    arm_plan = build_arm_plan(load_jsonl(args.cases))
    source_h = load_source_h(args.source_results, cases, args.model)

    if args.dry_run:
        dry_run(cases, source_h, args, arm_plan)
        return

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")

    done = completed_ids(args.output)
    for i, case in enumerate(cases, 1):
        anchor, weak = aligned_cards_for(case)
        first = arm_plan[case["case_id"]]
        print(f"[{i}/{len(cases)}] {case['case_id']} arm-first={first}", flush=True)
        try:
            if first == "sequential":
                run_aligned_sequential(case, anchor, weak, source_h[case["case_id"]], key, args, done)
                done = completed_ids(args.output)
                run_fresh_aligned(case, anchor, weak, key, args, done)
            else:
                run_fresh_aligned(case, anchor, weak, key, args, done)
                done = completed_ids(args.output)
                run_aligned_sequential(case, anchor, weak, source_h[case["case_id"]], key, args, done)
            done = completed_ids(args.output)
        except RateLimitExhausted as exc:
            print(f"STOPPING CLEANLY: {exc}", flush=True)
            print("Resume later with the exact same command and output paths.", flush=True)
            raise SystemExit(75)
        except FatalAPIError as exc:
            print(f"FATAL API ERROR: {exc}", flush=True)
            raise SystemExit(2)


if __name__ == "__main__":
    main()
