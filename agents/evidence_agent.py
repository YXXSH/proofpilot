from ai_service import generate_agent_json


def run_evidence_agent(
    case,
    evidence_review,
):
    """
    Analyse what each document actually supports.
    """

    instructions = """
You are the Evidence Analyst.

Your job is NOT to blindly trust documents.

For every evidence document:

1. Identify what it supports.
2. Identify what it does not prove.
3. Identify conflicts.
4. Identify missing evidence.

Create claim-to-evidence mappings.

Use these evidence strength labels:

- DIRECT
- SUPPORTING
- WEAK
- NOT_PROVEN
- CONFLICTING

Return exactly:

{
  "claim_evidence_map": [
    {
      "claim": "...",
      "documents": [],
      "strength": "DIRECT",
      "reason": "..."
    }
  ],
  "confirmed_facts": [],
  "unsupported_claims": [],
  "conflicts": [],
  "missing_evidence": [],
  "overall_evidence_assessment": "STRONG|PARTIAL|WEAK|CONFLICTED"
}
"""

    payload = {
        "case": case,
        "evidence_review": evidence_review,
    }

    result = generate_agent_json(
        "Evidence Analyst Agent",
        instructions,
        payload,
    )

    if result.get("available"):
        return result["data"]

    # Deterministic fallback.
    items = (
        evidence_review.get(
            "items",
            [],
        )
    )

    mappings = []
    confirmed = []
    conflicts = []
    missing = []

    for item in items:

        verification = (
            item.get(
                "verification"
            )
            or {}
        )

        status = verification.get(
            "status",
            "NOT_REVIEWED",
        )

        matched = verification.get(
            "matched_signals",
            [],
        )

        item_name = item.get(
            "filename",
            "Unknown document",
        )

        if status == "STRONG_MATCH":

            strength = "DIRECT"

            confirmed.append(
                f"{item_name} strongly supports "
                "the case."
            )

        elif status == "PARTIAL_MATCH":

            strength = "SUPPORTING"

            confirmed.append(
                f"{item_name} provides partial "
                "support."
            )

        elif status == "CONFLICTS_FOUND":

            strength = "CONFLICTING"

            conflicts.extend(
                verification.get(
                    "conflicts",
                    [],
                )
            )

        else:

            strength = "NOT_PROVEN"

        mappings.append(
            {
                "claim": (
                    "Case information is supported "
                    f"by {item_name}"
                ),
                "documents": [
                    item_name
                ],
                "strength": strength,
                "reason": (
                    "; ".join(matched)
                    or "No strong matching signal."
                ),
            }
        )

    if conflicts:
        assessment = "CONFLICTED"

    elif confirmed:
        assessment = "STRONG"

    elif items:
        assessment = "WEAK"

    else:
        assessment = "WEAK"

        missing.append(
            "Supporting documents"
        )

    return {
        "claim_evidence_map": mappings,
        "confirmed_facts": confirmed,
        "unsupported_claims": [],
        "conflicts": conflicts,
        "missing_evidence": missing,
        "overall_evidence_assessment": assessment,
        "_fallback": True,
    }