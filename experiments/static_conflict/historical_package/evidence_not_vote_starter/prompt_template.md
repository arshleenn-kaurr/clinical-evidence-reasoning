You are evaluating a therapeutic decision using ONLY the evidence cards provided below.

Evidence items may differ in study design, certainty, directness, and relevance. Do not count sources as votes. Weigh each item according to the strength and clinical relevance of the evidence it represents.

Question:
{question}

Evidence:
{evidence_cards}

Return JSON only:
{
  "decision": "support" | "do_not_support" | "insufficient",
  "confidence": 0-100,
  "dominant_evidence_ids": ["E0", "..."],
  "rationale": "Brief explanation, maximum 80 words."
}
