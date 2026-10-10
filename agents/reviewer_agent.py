from ai_service import generate_agent_json


def run_reviewer_agent(
    case,
    query_analysis,
    evidence_analysis,
    policy_analysis,
    resolution_analysis,
):
    """
    Review the proposed resolution before it
    reaches the final user-facing package.
    """

    instructions = """
You are the Reviewer Agent.

Your job is to challenge the proposed resolution.

The Policy Analyst assessment is an important part of the review.

Check whether the proposed resolution is consistent with the company policy.

If the policy is clearly violated, do not approve the resolution without appropriate escalation.

If policy compliance is unclear, identify this as a concern.

The reviewer should check the complete chain:

customer claim → evidence → policy → proposed resolution.

Ask:

1. Is the recommendation supported?
2. Is important evidence missing?
3. Are there contradictions?
4. Is the recommendation stronger than the evidence permits?
5. Does the recommendation accidentally make a legal
   or policy claim that has not been established?

Return:

{
  "decision": "READY_FOR_USER_REVIEW|MORE_EVIDENCE_REQUIRED|CONFLICT_REQUIRES_REVIEW",
  "approved_for_user_review": true,
  "supporting_reasons": [],
  "concerns": [],
  "required_changes": [],
  "reviewer_confidence": 0
}

Never say that a customer is legally entitled to something
unless the input explicitly establishes that fact.
"""

    result = generate_agent_json(
        "Reviewer / Critic Agent",
        instructions,
        payload = {
    "case": case,
    "query_analysis": query_analysis,
    "evidence_analysis": evidence_analysis,
    "policy_analysis": policy_analysis,
    "resolution_analysis": resolution_analysis,
},
    )

    if result.get("available"):
        return result["data"]

    # Deterministic fallback.
    conflicts = evidence_analysis.get(
        "conflicts",
        [],
    )

    missing = evidence_analysis.get(
        "missing_evidence",
        [],
    )

    assessment = evidence_analysis.get(
        "overall_evidence_assessment",
        "WEAK",
    )

    if conflicts:
        decision = (
            "CONFLICT_REQUIRES_REVIEW"
        )

        approved = False

    elif (
        assessment != "STRONG"
        or missing
    ):
        decision = (
            "MORE_EVIDENCE_REQUIRED"
        )

        approved = False

    else:
        decision = (
            "READY_FOR_USER_REVIEW"
        )

        approved = True

    concerns = []

    if missing:
        concerns.extend(
            [
                f"Missing: {item}"
                for item in missing
            ]
        )

    if conflicts:
        concerns.extend(
            conflicts
        )

    return {
        "decision": decision,
        "approved_for_user_review": approved,
        "supporting_reasons": [
            "The recommendation was reviewed "
            "against the available evidence."
        ],
        "concerns": concerns,
        "required_changes": (
            ["Collect stronger supporting evidence."]
            if not approved
            else []
        ),
        "reviewer_confidence": (
            80
            if approved
            else 60
        ),
        "_fallback": True,
    }