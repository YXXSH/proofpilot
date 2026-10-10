from .evidence_agent import run_evidence_agent
from .query_agent import run_query_agent
from .resolution_agent import run_resolution_agent
from .reviewer_agent import run_reviewer_agent
from .policy_agent import run_policy_agent


def run_agentic_workflow(
    case,
    rule_based_result,
):
    query_analysis = run_query_agent(
        case,
        rule_based_result,
    )

    evidence_analysis = run_evidence_agent(
        case,
        rule_based_result.get(
            "evidence_review",
            {},
        ),
    )

    policy_analysis = run_policy_agent(
        case,
        evidence_analysis,
    )

    resolution_analysis = run_resolution_agent(
        case,
        query_analysis,
        evidence_analysis,
        policy_analysis,
    )

    reviewer_analysis = run_reviewer_agent(
        case,
        query_analysis,
        evidence_analysis,
        policy_analysis,
        resolution_analysis,
    )

    if reviewer_analysis.get(
        "decision"
    ) == "CONFLICT_REQUIRES_REVIEW":

        final_status = (
            "CONFLICT_REQUIRES_REVIEW"
        )

    elif reviewer_analysis.get(
        "decision"
    ) == "MORE_EVIDENCE_REQUIRED":

        final_status = (
            "MORE_EVIDENCE_REQUIRED"
        )

    elif policy_analysis.get(
        "compliance_status"
    ) == "NON_COMPLIANT":

        final_status = (
            "POLICY_NON_COMPLIANT"
        )

    elif policy_analysis.get(
        "compliance_status"
    ) == "POLICY_UNCLEAR":

        final_status = (
            "POLICY_REQUIRES_REVIEW"
        )

    else:

        final_status = (
            "READY_FOR_COMPANY_REVIEW"
        )

    return {
        "pipeline": [
            "Query Analyst",
            "Evidence Analyst",
            "Policy Analyst",
            "Resolution Analyst",
            "Reviewer Agent",
        ],
        "query_analysis": query_analysis,
        "evidence_analysis": evidence_analysis,
        "policy_analysis": policy_analysis,
        "resolution_analysis": resolution_analysis,
        "reviewer_analysis": reviewer_analysis,
        "final_status": final_status,
    }