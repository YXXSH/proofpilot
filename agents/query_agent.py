from ai_service import generate_agent_json


def run_query_agent(
    case,
    rule_based_result,
):
    """
    Understand what the customer is asking,
    without solving the case yet.
    """

    instructions = """
You are the Query Analyst.

Your job is to understand the user's problem.

Extract:

- user_goal
- core_problem
- important_facts
- requested_resolution
- missing_information
- clarification_questions
- risk_flags

Do not recommend a solution yet.

Return exactly one JSON object with this shape:

{
  "user_goal": "...",
  "core_problem": "...",
  "important_facts": [],
  "requested_resolution": "...",
  "missing_information": [],
  "clarification_questions": [],
  "risk_flags": []
}
"""

    payload = {
        "case": case,
        "rule_based_result": {
            "extracted_facts": rule_based_result.get(
                "extracted_facts",
                {},
            ),
            "consistency_warnings": (
                rule_based_result.get(
                    "consistency_warnings",
                    [],
                )
            ),
            "evidence_gaps": (
                rule_based_result.get(
                    "evidence_gaps",
                    [],
                )
            ),
        },
    }

    result = generate_agent_json(
        "Query Analyst Agent",
        instructions,
        payload,
    )

    if result.get("available"):
        return result["data"]

    # Safe deterministic fallback.
    return {
        "user_goal": case.get(
            "desired_resolution",
            "",
        ),
        "core_problem": case.get(
            "description",
            "",
        ),
        "important_facts": (
            rule_based_result
            .get(
                "extracted_facts",
                {},
            )
        ),
        "requested_resolution": case.get(
            "desired_resolution",
            "",
        ),
        "missing_information": (
            rule_based_result
            .get(
                "evidence_gaps",
                [],
            )
        ),
        "clarification_questions": [],
        "risk_flags": (
            rule_based_result
            .get(
                "consistency_warnings",
                [],
            )
        ),
        "_fallback": True,
    }