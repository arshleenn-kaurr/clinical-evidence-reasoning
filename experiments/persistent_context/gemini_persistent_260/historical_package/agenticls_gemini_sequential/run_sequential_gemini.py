#!/usr/bin/env python3
"""AgenticLS persistent-context experiment on Gemini 3.6 Flash.

Optimized six-call design per case:
  * persistent sequential arm: H -> L1 -> L2 -> L3 -> L4 (5 calls)
  * fresh terminal arm: H+L1+L2+L3+L4 in a new conversation (1 call)

Only successful sequential responses enter later conversation history. Failed
attempts are retained in a separate attempts JSONL. The runner is resume-safe:
rerun the identical command with the same output paths after interruption.

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

# Historical static execution supplied temperature=0. Current Gemini 3.6 Flash
# API guidance deprecates/ignores temperature/top_p/top_k, so this runner omits
# them and records that operational change explicitly in every canonical row.
HISTORICAL_TEMPERATURE = 0
SAMPLING_NOTE = (
    "Historical static benchmark supplied temperature=0; current Gemini 3.6 Flash "
    "API deprecates/ignores temperature/top_p/top_k, so sampling fields are omitted."
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
        "dominant_evidence_ids": {
            "type": "array",
            "items": {"type": "string"},
        },
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


def opposite(decision):
    if decision == "support":
        return "do_not_support"
    if decision == "do_not_support":
        return "support"
    raise ValueError(f"Unsupported reference decision: {decision}")


def direction_text(direction):
    if direction == "support":
        return "The study reports results favoring the intervention for the target clinical outcome."
    return "The study reports results not favoring the intervention for the target clinical outcome."


def cards_for(case):
    anchor = dict(case["anchor"])
    anchor.update({"id": "E0", "source_kind": case.get("source_type", "")})
    if anchor.get("evidence_quality"):
        anchor["declared_quality"] = anchor["evidence_quality"]

    weak = []
    for template in WEAK:
        card = dict(template)
        card["direction"] = opposite(case["reference_decision"])
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
        role = msg["role"]
        if role == "assistant":
            role = "model"
        if role not in {"user", "model"}:
            raise ValueError(f"Unsupported Gemini conversation role: {role}")
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    if contents and contents[-1]["role"] != "user":
        raise ValueError("Gemini request must end with a user turn")
    return contents


def make_request_body(messages):
    # responseJsonSchema is the current generateContent JSON-Schema field.
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
        # If the provider ever exposes thought parts, do not parse those as JSON.
        if part.get("thought") is True:
            continue
        text = part.get("text")
        if isinstance(text, str):
            texts.append(text)
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
                "User-Agent": "agenticls-persistent-context/1.0",
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
                        k: v
                        for k, v in headers.items()
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
    """Deterministically balance fresh-first/sequential-first within frozen strata."""
    groups = defaultdict(list)
    for case in cases:
        groups[case_stratum(case)].append(case)

    # In the frozen 65x4 cohort this yields exact 130/130 overall balance.
    extra_seq = {("High", "support"), ("Moderate", "do_not_support")}
    plan = {}
    for key, items in groups.items():
        ordered = sorted(
            items,
            key=lambda c: hashlib.sha256(c["case_id"].encode("utf-8")).hexdigest(),
        )
        n_seq = len(ordered) // 2 + (1 if len(ordered) % 2 and key in extra_seq else 0)
        seq_ids = {c["case_id"] for c in ordered[:n_seq]}
        for case in ordered:
            plan[case["case_id"]] = "sequential" if case["case_id"] in seq_ids else "fresh"
    return plan


def successful_rows(output):
    return [row for row in load_jsonl(output) if row.get("status") == "ok"]


def completed_ids(output):
    return {row["run_id"] for row in successful_rows(output)}


def evidence_ids_for_step(step):
    return [f"E{i}" for i in range(step)]


def row_base(case, args, arm, step, condition, new_evidence_id, prompt_text, messages):
    return {
        "run_id": f"{case['case_id']}::{arm}::{condition}",
        "case_id": case["case_id"],
        "arm": arm,
        "step": step,
        "condition": condition,
        "new_evidence_id": new_evidence_id,
        "evidence_ids_available": evidence_ids_for_step(step),
        "reference_decision": case["reference_decision"],
        "model": args.model,
        "historical_temperature_supplied": HISTORICAL_TEMPERATURE,
        "temperature_sent": None,
        "sampling_parameters_note": SAMPLING_NOTE,
        "thinking_configuration": "provider_default_no_explicit_thinking_parameter",
        "response_schema_mode": "responseJsonSchema",
        "prompt_sha256": sha256_text(prompt_text),
        "message_count": len(messages),
        "timestamp_utc": utc_now(),
    }


def run_fresh(case, anchor, weak, key, args, done):
    run_id = f"{case['case_id']}::fresh::H_L4"
    if run_id in done:
        return

    prompt = batch_prompt(case["question"], [anchor, *weak])
    messages = [{"role": "user", "content": prompt}]
    base = row_base(case, args, "fresh", 5, "H_L4", None, prompt, messages)
    meta = {k: base[k] for k in ["run_id", "case_id", "arm", "step", "condition"]}
    try:
        answer, raw_text, provider, candidate, attempts, request_sha = call_gemini(
            messages, key, args.model, args.retries, args.attempt_log, meta
        )
        row = {
            **base,
            **answer,
            "status": "ok",
            "raw_text": raw_text,
            "attempts": attempts,
            "request_sha256": request_sha,
            "finish_reason": candidate.get("finishReason"),
            "usage_metadata": provider.get("usageMetadata", {}),
            "model_version": provider.get("modelVersion"),
        }
        append_jsonl(args.output, row)
    except (RateLimitExhausted, FatalAPIError):
        raise
    except Exception as exc:
        append_jsonl(args.output, {**base, "status": "error", "error": repr(exc)})
    time.sleep(args.sleep)


def reconstruct_sequential_history(case, anchor, weak, output, before_step):
    rows = [
        row for row in successful_rows(output)
        if row.get("case_id") == case["case_id"]
        and row.get("arm") == "sequential"
        and row.get("step", 999) < before_step
    ]
    by_step = {row["step"]: row for row in rows}
    messages = []
    for step in range(1, before_step):
        if step not in by_step:
            raise RuntimeError(
                f"Cannot resume {case['case_id']} step {before_step}: missing successful sequential step {step}"
            )
        user_text = batch_prompt(case["question"], [anchor]) if step == 1 else update_message(weak[step - 2])
        messages.append({"role": "user", "content": user_text})
        messages.append({"role": "assistant", "content": by_step[step]["raw_text"]})
    return messages


def run_sequential(case, anchor, weak, key, args, done):
    states = [
        ("H", anchor),
        ("H_L1", weak[0]),
        ("H_L2", weak[1]),
        ("H_L3", weak[2]),
        ("H_L4", weak[3]),
    ]
    messages = reconstruct_sequential_history(case, anchor, weak, args.output, before_step=1)

    for step, (condition, new_card) in enumerate(states, 1):
        run_id = f"{case['case_id']}::sequential::{condition}"
        if run_id in done:
            messages = reconstruct_sequential_history(case, anchor, weak, args.output, before_step=step + 1)
            continue

        user_text = batch_prompt(case["question"], [anchor]) if step == 1 else update_message(new_card)
        preturn = list(messages)
        request_messages = preturn + [{"role": "user", "content": user_text}]
        base = row_base(
            case,
            args,
            "sequential",
            step,
            condition,
            "E0" if step == 1 else new_card["id"],
            user_text,
            request_messages,
        )
        base["history_turns_before"] = len(preturn) // 2
        meta = {k: base[k] for k in ["run_id", "case_id", "arm", "step", "condition"]}

        try:
            answer, raw_text, provider, candidate, attempts, request_sha = call_gemini(
                request_messages, key, args.model, args.retries, args.attempt_log, meta
            )
            row = {
                **base,
                **answer,
                "status": "ok",
                "raw_text": raw_text,
                "attempts": attempts,
                "request_sha256": request_sha,
                "finish_reason": candidate.get("finishReason"),
                "usage_metadata": provider.get("usageMetadata", {}),
                "model_version": provider.get("modelVersion"),
            }
            append_jsonl(args.output, row)
            messages = request_messages + [{"role": "assistant", "content": raw_text}]
        except (RateLimitExhausted, FatalAPIError):
            raise
        except Exception as exc:
            append_jsonl(args.output, {**base, "status": "error", "error": repr(exc)})
            return
        time.sleep(args.sleep)


def dry_run(cases, args, arm_plan):
    print(f"model={args.model}")
    print("sampling_parameters_sent=none")
    print("thinking_configuration=provider_default_no_explicit_thinking_parameter")
    print("response_schema_mode=responseJsonSchema")
    for case in cases:
        anchor, weak = cards_for(case)
        print(
            case["case_id"],
            f"arm-first={arm_plan[case['case_id']]}",
            "states=sequential:H,H_L1,H_L2,H_L3,H_L4 + fresh:H_L4",
            "H_sha256=" + sha256_text(batch_prompt(case["question"], [anchor]))[:16],
            "L1_update_sha256=" + sha256_text(update_message(weak[0]))[:16],
            "fresh_HL4_sha256=" + sha256_text(batch_prompt(case["question"], [anchor, *weak]))[:16],
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--attempt-log")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.attempt_log is None:
        out = Path(args.output)
        args.attempt_log = str(out.with_name(out.stem + "_attempts.jsonl"))

    cases = load_jsonl(args.cases)
    if args.limit:
        cases = cases[: args.limit]
    arm_plan = build_arm_plan(cases)

    if args.dry_run:
        dry_run(cases, args, arm_plan)
        return

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")

    done = completed_ids(args.output)
    for index, case in enumerate(cases, 1):
        anchor, weak = cards_for(case)
        first = arm_plan[case["case_id"]]
        print(f"[{index}/{len(cases)}] {case['case_id']} arm-first={first}", flush=True)
        try:
            if first == "sequential":
                run_sequential(case, anchor, weak, key, args, done)
                done = completed_ids(args.output)
                run_fresh(case, anchor, weak, key, args, done)
            else:
                run_fresh(case, anchor, weak, key, args, done)
                done = completed_ids(args.output)
                run_sequential(case, anchor, weak, key, args, done)
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
