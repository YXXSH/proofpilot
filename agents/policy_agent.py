from ai_service import generate_agent_json


def run_policy_agent(
    case,
    evidence_analysis,
):
    """
    Evaluate the customer claim against
    the company's supplied policy.
    """

    company_policy = (
        case.get(
            "company_policy",
            "",
        )
        or ""
    )

    if not company_policy.strip():

        return {
            "available": True,
            "agent": "Policy Analyst",
            "policy_applicable": False,
            "compliance_status": (
                "NO_POLICY_PROVIDED"
            ),
            "rule_checks": [],
            "violations": [],
            "missing_policy_evidence": [],
            "reasoning": [
                "No company policy was "
                "provided for this case."
            ],
            "recommended_policy_action": (
                "HUMAN_REVIEW"
            ),
        }

    instructions = """
You are the Policy Analyst in an
agentic company-side case assessment
system called ProofPilot.

Your job is to evaluate whether the
customer's claim and requested resolution
comply with the company policy supplied
for this case.

Do NOT decide the case solely from the
customer's request.

Compare:
1. Customer claim
2. Case facts
3. Available evidence assessment
4. Company policy

Identify each relevant policy rule and
determine whether the case satisfies it.

Important:
- Do not invent policy rules.
- Do not assume missing facts.
- If the policy is ambiguous, say so.
- If evidence needed to apply a policy rule
  is missing, identify it.
- A strong evidence case can still be
  policy non-compliant.
- Policy compliance does not itself prove
  the customer's claim.

Return ONLY valid JSON using exactly
this structure:

{
  "policy_applicable": true,
  "compliance_status": "COMPLIANT",
  "rule_checks": [
    {
      "rule": "string",
      "status": "SATISFIED",
      "reason": "string"
    }
  ],
  "violations": [],
  "missing_policy_evidence": [],
  "reasoning": [],
  "recommended_policy_action": "APPROVE"
}

Allowed compliance_status values:
- COMPLIANT
- PARTIALLY_COMPLIANT
- NON_COMPLIANT
- POLICY_UNCLEAR
- NO_POLICY_PROVIDED

Allowed rule status values:
- SATISFIED
- NOT_SATISFIED
- UNCLEAR
- NOT_APPLICABLE

Allowed recommended_policy_action values:
- APPROVE
- REQUEST_MORE_EVIDENCE
- REJECT
- ESCALATE
- HUMAN_REVIEW
"""

    payload = {
        "case": case,
        "company_policy": company_policy,
        "evidence_analysis": (
            evidence_analysis
        ),
    }

    result = generate_agent_json(
        "Policy Analyst",
        instructions,
        payload,
    )

    if result.get("available"):

        data = (
            result.get("data")
            or {}
        )

        return {
            "available": True,
            "agent": "Policy Analyst",
            "policy_applicable": data.get(
                "policy_applicable",
                True,
            ),
            "compliance_status": data.get(
                "compliance_status",
                "POLICY_UNCLEAR",
            ),
            "rule_checks": data.get(
                "rule_checks",
                [],
            ),
            "violations": data.get(
                "violations",
                [],
            ),
            "missing_policy_evidence": data.get(
                "missing_policy_evidence",
                [],
            ),
            "reasoning": data.get(
                "reasoning",
                [],
            ),
            "recommended_policy_action": data.get(
                "recommended_policy_action",
                "HUMAN_REVIEW",
            ),
            "model": result.get(
                "model"
            ),
        }

    # Deterministic fallback
    # if the AI policy analysis is unavailable.

    return {
        "available": False,
        "agent": "Policy Analyst",
        "policy_applicable": True,
        "compliance_status": (
            "POLICY_UNCLEAR"
        ),
        "rule_checks": [],
        "violations": [],
        "missing_policy_evidence": [
            "Policy analysis could not "
            "be completed automatically."
        ],
        "reasoning": [
            "The Policy Analyst was "
            "unavailable."
        ],
        "recommended_policy_action": (
            "HUMAN_REVIEW"
        ),
    }