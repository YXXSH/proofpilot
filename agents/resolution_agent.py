from ai_service import generate_agent_json


def run_resolution_agent(
    case,
    query_analysis,
    evidence_analysis,
    policy_analysis,
):
    """
    Decide the strongest practical next step
    based on the verified information.
    """

    instructions = """ 
You are the Resolution Analyst.

You must consider the Policy Analyst assessment when recommending a resolution.

A customer claim may be strongly supported by evidence but still be non-compliant with company policy.

Do not recommend an action that clearly contradicts the supplied company policy.

If policy compliance is unclear, recommend human/company review rather than assuming compliance.

Determine the strongest practical resolution path.

You must:

- respect the user's requested outcome;
- rely on supported evidence;
- identify what is still uncertain;
- suggest practical next actions;
- avoid unsupported legal claims;
- never present an AI recommendation as a guaranteed entitlement.

Return:

{
  "recommended_resolution": "...",
  "reasoning": [],
  "evidence_basis": [],
  "additional_evidence_needed": [],
  "next_actions": [],
  "escalation_strategy": [],
  "confidence": 0
}

Confidence must be an integer from 0 to 100.
"""

    result = generate_agent_json(
        "Resolution Analyst Agent",
        instructions,
        payload = {
    "case": case,
    "query_analysis": query_analysis,
    "evidence_analysis": evidence_analysis,
    "policy_analysis": policy_analysis,
},
    )

    if result.get("available"):
        return result["data"]

    # Safe fallback.
    issue = case.get(
        "issue_type",
        "Other",
    )

    requested = case.get(
        "desired_resolution",
        "",
    )

    missing = evidence_analysis.get(
        "missing_evidence",
        [],
    )

    next_actions = [
        "Use the prepared complaint through "
        "the company's official support channel."
    ]

    if missing:
        next_actions.insert(
            0,
            "Collect the missing evidence "
            "identified by ProofPilot.",
        )

    if issue == "Defective product":

        next_actions.append(
            "Attach photos or videos showing "
            "the defect."
        )

    elif issue == "Incorrect bill or charge":

        next_actions.append(
            "Attach the invoice or payment "
            "record showing the disputed amount."
        )

    elif issue == "Delivery problem":

        next_actions.append(
            "Attach the delivery tracking record "
            "and proof of the delivery problem."
        )

    elif issue == "Refund not received":

        next_actions.append(
            "Request written confirmation of "
            "the refund status and processing date."
        )

    assessment = evidence_analysis.get(
        "overall_evidence_assessment",
        "WEAK",
    )

    if assessment == "STRONG":
        confidence = 80
    elif assessment == "CONFLICTED":
        confidence = 35
    else:
        confidence = 60

    return {
        "recommended_resolution": (
            requested
            or "Seek a documented resolution "
            "through the official support channel."
        ),
        "reasoning": [
            "The recommendation is based on "
            "the information currently available.",
            f"Evidence assessment: {assessment}.",
        ],
        "evidence_basis": (
            evidence_analysis.get(
                "confirmed_facts",
                [],
            )
        ),
        "additional_evidence_needed": missing,
        "next_actions": next_actions,
        "escalation_strategy": [
            "Keep the complaint, supporting documents, "
            "and support ticket together.",
            "Escalate through the company's official "
            "grievance/support route if unresolved.",
        ],
        "confidence": confidence,
        "_fallback": True,
    }