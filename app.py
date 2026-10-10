import streamlit as st

from agent import analyse_case
from agents import run_agentic_workflow
from evidence import process_uploaded_file
from storage import (
    add_evidence_to_case,
    load_cases,
    save_case,
    update_case_analysis,
    update_agentic_analysis,
    update_case_status,
    update_company_decision,
)
def calculate_case_strength(
    case,
    result,
    agentic_analysis,
):
    """
    Calculate a transparent 0-100 case strength score.

    The score is based on:
    - evidence coverage
    - evidence quality
    - claim support
    - consistency
    - conflicts
    - missing evidence
    """

    evidence_review = (
        result.get(
            "evidence_review",
            {},
        )
        or {}
    )

    evidence_analysis = (
        (agentic_analysis or {}).get(
            "evidence_analysis",
            {},
        )
        or {}
    )

    # -------------------------
    # Evidence coverage
    # -------------------------

    documents_checked = int(
        evidence_review.get(
            "documents_checked",
            0,
        )
        or 0
    )

    strong_matches = int(
        evidence_review.get(
            "strong_matches",
            0,
        )
        or 0
    )

    partial_matches = int(
        evidence_review.get(
            "partial_matches",
            0,
        )
        or 0
    )

    if documents_checked == 0:

        evidence_coverage = 0

    else:

        evidence_coverage = min(
            25,
            int(
                (
                    (
                        strong_matches
                        + (
                            partial_matches
                            * 0.5
                        )
                    )
                    / documents_checked
                )
                * 25
            ),
        )

    # -------------------------
    # Evidence quality
    # -------------------------

    assessment = str(
        evidence_analysis.get(
            "overall_evidence_assessment",
            "",
        )
    ).upper()

    if (
        "STRONG" in assessment
        or "HIGH" in assessment
    ):

        evidence_quality = 20

    elif (
        "PARTIAL" in assessment
        or "MODERATE" in assessment
    ):

        evidence_quality = 12

    elif assessment:

        evidence_quality = 6

    else:

        evidence_quality = 0

    # -------------------------
    # Claim support
    # -------------------------

    mappings = (
        evidence_analysis.get(
            "claim_evidence_map",
            [],
        )
        or []
    )

    supported_claims = 0
    total_claims = len(mappings)

    for mapping in mappings:

        strength = str(
            mapping.get(
                "strength",
                "",
            )
        ).upper()

        if strength in (
            "DIRECT",
            "STRONG",
        ):

            supported_claims += 1

        elif strength in (
            "SUPPORTING",
            "PARTIAL",
        ):

            supported_claims += 0.5

    if total_claims:

        claim_support = int(
            (
                supported_claims
                / total_claims
            )
            * 20
        )

    else:

        claim_support = 0

    # -------------------------
    # Consistency
    # -------------------------

    warnings = result.get(
        "consistency_warnings",
        [],
    ) or []

    if not warnings:

        consistency = 20

    elif len(warnings) == 1:

        consistency = 12

    elif len(warnings) == 2:

        consistency = 7

    else:

        consistency = 3

    # -------------------------
    # Conflicts
    # -------------------------

    conflicts = (
        evidence_review.get(
            "conflicts",
            0,
        )
        or 0
    )

    try:
        conflicts = int(conflicts)

    except (
        TypeError,
        ValueError,
    ):

        conflicts = 0

    conflict_penalty = min(
        15,
        conflicts * 5,
    )

    # -------------------------
    # Missing evidence
    # -------------------------

    missing_evidence = (
        evidence_analysis.get(
            "missing_evidence",
            [],
        )
        or []
    )

    missing_penalty = min(
        10,
        len(missing_evidence) * 2,
    )

    # -------------------------
    # Final score
    # -------------------------

    score = (
        evidence_coverage
        + evidence_quality
        + claim_support
        + consistency
        - conflict_penalty
        - missing_penalty
    )

    score = max(
        0,
        min(
            100,
            int(score),
        ),
    )

    if score >= 75:

        strength = "STRONG"

    elif score >= 50:

        strength = "MODERATE"

    elif score >= 25:

        strength = "WEAK"

    else:

        strength = "INSUFFICIENT"

    return {
        "score": score,
        "strength": strength,
        "breakdown": {
            "evidence_coverage": evidence_coverage,
            "evidence_quality": evidence_quality,
            "claim_support": claim_support,
            "consistency": consistency,
            "conflict_penalty": conflict_penalty,
            "missing_evidence_penalty": (
                missing_penalty
            ),
        },
    }



def build_resolution_package(
    case,
    result,
    case_id,
    evidence_items,
    ai_analysis,
    agentic_analysis,
):
    timeline_lines = "\n".join(
        f"- {item['date']} — {item['event']}"
        for item in result.get("timeline", [])
    ) or "- No timeline available."

    action_lines = "\n".join(
        f"{number}. {step}"
        for number, step in enumerate(
            result.get("action_plan", []),
            start=1,
        )
    ) or "- No action plan available."

    gap_lines = "\n".join(
        f"- {gap}"
        for gap in result.get("evidence_gaps", [])
    ) or "- No immediate gaps detected."

    evidence_lines = "\n".join(
        (
            f"- {item.get('filename', 'Unknown file')} | "
            f"{(item.get('verification') or {}).get('status', 'NOT REVIEWED')} | "
            f"SHA256: {item.get('sha256', 'N/A')}"
        )
        for item in (evidence_items or [])
    ) or "- No evidence files uploaded yet."

    evidence_review = (
        result.get("evidence_review")
        or {}
    )

    evidence_status = evidence_review.get(
        "overall_status",
        "NO_EVIDENCE_YET",
    )

    ai_data = ai_analysis or {}

    ai_text = ai_data.get(
        "text",
        "AI review not run.",
    )

    agentic_data = agentic_analysis or {}

    final_agent_status = agentic_data.get(
        "final_status",
        "NOT_RUN",
    )

    reviewer_data = (
        agentic_data.get(
            "reviewer_analysis",
            {},
        )
        or {}
    )

    reviewer_decision = reviewer_data.get(
        "decision",
        "NOT_RUN",
    )

    reviewer_confidence = reviewer_data.get(
        "reviewer_confidence",
        "N/A",
    )

    reviewer_concerns = (
        reviewer_data.get(
            "concerns",
            [],
        )
        or []
    )

    reviewer_concern_lines = "\n".join(
        f"- {item}"
        for item in reviewer_concerns
    ) or "- None recorded."

    return f"""# ProofPilot Resolution Package

## Case ID

{case_id}

## Company

{case.get("company", "")}

## Issue Type

{case.get("issue_type", "")}

## Requested Resolution

{case.get("desired_resolution", "")}

## Timeline

{timeline_lines}

## Evidence Files

{evidence_lines}

## Evidence Review Status

{evidence_status}

## Evidence Gaps

{gap_lines}

## Recommended Action Plan

{action_lines}

## Complaint Draft

{result.get("complaint", "")}

## AI Review

{ai_text}

## Multi-Agent Review

### Final Agent Status

{final_agent_status}

### Reviewer Decision

{reviewer_decision}

### Reviewer Confidence

{reviewer_confidence}

### Reviewer Concerns

{reviewer_concern_lines}
"""


def load_saved_case(record):

    st.session_state.active_case = (
        record["case"]
    )

    st.session_state.analysis_result = (
        record.get("analysis")
        or analyse_case(
            record["case"],
            record.get(
                "evidence",
                [],
            ),
        )
    )

    st.session_state.case_id = (
        record["case_id"]
    )

    st.session_state.evidence_items = (
        record.get(
            "evidence",
            [],
        )
    )

    st.session_state.ai_analysis = (
        record.get(
            "ai_analysis"
        )
    )

    st.session_state.agentic_analysis = (
        record.get(
            "agentic_analysis"
        )
    )

    st.session_state.case_status = (
        record.get(
            "status",
            "DRAFT",
        )
    )

    st.session_state.company_decision = (
        record.get(
            "company_decision"
        )
    )

    st.session_state.decision_reason = (
        record.get(
            "decision_reason"
        )
    )


st.set_page_config(
    page_title="ProofPilot",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)


def status_label(status):
    """Return a concise, human-friendly label for a workflow state."""
    return str(status or "DRAFT").replace("_", " ").title()


def status_icon(status):
    """Return a visual severity cue without changing stored status values."""
    status = str(status or "DRAFT").upper()
    if status in {"APPROVED", "READY_FOR_COMPANY_REVIEW"}:
        return "🟢"
    if status in {
        "REJECTED_ESCALATED",
        "COMPANY_ESCALATED",
        "CONFLICT_REQUIRES_REVIEW",
        "POLICY_NON_COMPLIANT",
    }:
        return "🔴"
    if status in {
        "MORE_EVIDENCE_REQUIRED",
        "MORE_EVIDENCE_REQUESTED",
        "POLICY_REQUIRES_REVIEW",
    }:
        return "🟡"
    return "⚪"


st.markdown(
    """
    <style>
      .block-container { max-width: 1440px; padding-top: 1.7rem; padding-bottom: 3rem; }
      [data-testid="stSidebar"] { background: #0c1525; }
      [data-testid="stSidebar"] * { color: #e8eef9; }
      [data-testid="stSidebar"] .stButton > button {
        background: #16233a; border: 1px solid #2b3c5a; text-align: left;
      }
      [data-testid="stSidebar"] .stButton > button:hover {
        border-color: #5b8cff; background: #1b2d4c;
      }
      .proofpilot-hero { padding: .55rem 0 1.35rem; }
      .proofpilot-kicker { color: #4f7cff; font-weight: 700; font-size: .8rem;
        letter-spacing: .11em; text-transform: uppercase; }
      .proofpilot-hero h1 { margin: .18rem 0 .25rem; font-size: 2.45rem;
        letter-spacing: -.04em; }
      .proofpilot-hero p { color: #64748b; font-size: 1.05rem; margin: 0; }
      div[data-testid="stMetric"] { background: #f8fafc; border: 1px solid #e2e8f0;
        border-radius: 12px; padding: .7rem .9rem; }
      .stTabs [data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid #e2e8f0; }
      .stTabs [data-baseweb="tab"] { height: 48px; padding: 0 1rem;
        border-radius: 8px 8px 0 0; }
      .stTabs [aria-selected="true"] { color: #2855c8; font-weight: 700; }
      .stExpander { border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important; }
      @media (max-width: 760px) {
        .block-container { padding: 1rem .75rem 2rem; }
        .proofpilot-hero h1 { font-size: 2rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# SESSION STATE
# -------------------------

if "active_case" not in st.session_state:
    st.session_state.active_case = None

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "case_id" not in st.session_state:
    st.session_state.case_id = None

if "evidence_items" not in st.session_state:
    st.session_state.evidence_items = []

if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = None

if "agentic_analysis" not in st.session_state:
    st.session_state.agentic_analysis = None

if "case_status" not in st.session_state:
    st.session_state.case_status = "DRAFT"

if "company_decision" not in st.session_state:
    st.session_state.company_decision = None
if "company_policy" not in st.session_state:
    st.session_state.company_policy = ""
if "decision_reason" not in st.session_state:
    st.session_state.decision_reason = None


# -------------------------
# HEADER
# -------------------------

st.markdown(
    """
    <div class="proofpilot-hero">
      <div class="proofpilot-kicker">Company case assessment</div>
      <h1>ProofPilot</h1>
      <p>Evidence-led decisions, policy-aware recommendations, and a clear human decision gate.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# SIDEBAR
# -------------------------

with st.sidebar:
    st.header("Case portfolio")
    st.caption("Select an active case or begin a new assessment.")

    saved_cases = load_cases()

    if saved_cases:

        for saved_case in saved_cases[:8]:

            saved_status = saved_case.get("status", "DRAFT")
            label = (
                f"{status_icon(saved_status)} {saved_case['case_id']}\n"
                f"{saved_case['case']['company']} · {status_label(saved_status)}"
            )

            if st.button(
                label,
                key=(
                    f"load_"
                    f"{saved_case['case_id']}"
                ),
                use_container_width=True,
            ):
                load_saved_case(
                    saved_case
                )

                st.rerun()

    else:
        st.caption(
            "No saved cases yet."
        )

    if st.session_state.case_id:

        st.divider()

        st.success(f"Active case · {st.session_state.case_id}")

        if st.button(
            "Clear active case",
            use_container_width=True,
        ):
            st.session_state.active_case = None
            st.session_state.analysis_result = None
            st.session_state.case_id = None
            st.session_state.evidence_items = []
            st.session_state.ai_analysis = None
            st.session_state.agentic_analysis = None
            st.session_state.case_status = "DRAFT"
            st.session_state.company_decision = None

            st.rerun()


# -------------------------
# TABS
# -------------------------

workspace_tab, evidence_tab, agent_tab, package_tab = st.tabs(
    [
        "01  Case intake",
        "02  Evidence vault",
        "03  Assessment",
        "04  Resolution",
    ]
)


# =========================================================
# 1. CASE WORKSPACE
# =========================================================

with workspace_tab:

    st.subheader("Create a company review case")
    st.caption("Capture the customer’s issue, requested outcome, and relevant company policy.")

    with st.form(
        "case_intake"
    ):

        left, right = st.columns(2)

        with left:

            company = st.text_input(
                "Company or service provider",
                placeholder="Example: Flipkart",
            )

            issue_type = st.selectbox(
                "Issue type",
                [
                    "Defective product",
                    "Refund not received",
                    "Incorrect bill or charge",
                    "Delivery problem",
                    "Subscription problem",
                    "Service complaint",
                    "Other",
                ],
            )

            event_date = st.text_input(
                "Date of purchase, delivery, charge, or incident",
                placeholder="Example: 13 February 2022",
            )

        with right:

            order_id = st.text_input(
                "Order ID, booking ID, or account reference"
            )

            contacted_support = st.checkbox(
                "I have already contacted customer support"
            )

            desired_resolution = st.text_input(
                "What outcome do you want?",
                placeholder="Example: Full refund or replacement",
            )

        description = st.text_area(
            "Describe what happened",
            height=180,
              )
        st.markdown(
                "### 🏢 Company Policy"
            )
        st.caption(
                "Provide the policy or rules that "
                "ProofPilot should use when assessing "
                "the customer's claim."
            )

        company_policy = st.text_area(
                "Applicable company policy",
                value=st.session_state.company_policy,
                height=180,
                placeholder=(
                    "Example:\n"
                    "- Damaged products can be returned "
                    "within 7 days.\n"
                    "- Invoice or proof of purchase is required.\n"
                    "- Photos showing physical damage are required.\n"
                    "- Customer may receive a refund or replacement."
                ),
            )

        submitted = st.form_submit_button(
            "Create case and start analysis",
            type="primary",
        )

    if submitted:

        required_fields = {
            "company/service provider": company,
            "problem description": description,
            "desired resolution": desired_resolution,
        }

        missing_fields = [
            name
            for name, value
            in required_fields.items()
            if not value.strip()
        ]

        if missing_fields:

            st.error(
                "Please add: "
                + ", ".join(
                    missing_fields
                )
            )

        else:

            case = {
    "company": company,
    "issue_type": issue_type,
    "event_date": event_date,
    "order_id": order_id,
    "contacted_support": contacted_support,
    "description": description,
    "desired_resolution": desired_resolution,
    "company_policy": company_policy,
}

            result = analyse_case(
                case
            )

            case_id = save_case(
                case,
                result,
            )

            st.session_state.active_case = case
            st.session_state.company_policy = (
    company_policy
)
            st.session_state.analysis_result = result
            st.session_state.case_id = case_id
            st.session_state.evidence_items = []
            st.session_state.ai_analysis = None
            st.session_state.agentic_analysis = None
            st.session_state.case_status = "DRAFT"
            st.session_state.company_decision = None

            st.success(
                f"Case created. "
                f"Case ID: {case_id}"
            )


# =========================================================
# 2. EVIDENCE VAULT
# =========================================================

with evidence_tab:

    st.subheader("Evidence vault")
    st.caption("Upload source documents and review verification signals before assessing the claim.")

    if not st.session_state.active_case:

        st.info(
            "Create or load a case first."
        )

    else:

        st.write(
            "Upload PDF or text evidence such as "
            "invoices, order confirmations, "
            "support chats, and policy documents. "
            "ProofPilot will compare each document "
            "with the active case."
        )

        uploaded_files = st.file_uploader(
            "Upload evidence",
            type=[
                "pdf",
                "txt",
            ],
            accept_multiple_files=True,
        )

        if st.button(
            "Process uploaded evidence",
            type="primary",
        ):

            if not uploaded_files:

                st.warning(
                    "Choose at least one "
                    "PDF or text file first."
                )

            else:

                processed_items = []

                with st.spinner(
                    "ProofPilot is reading "
                    "and checking the evidence files..."
                ):

                    for uploaded_file in uploaded_files:

                        item = (
                            process_uploaded_file(
                                uploaded_file,
                                st.session_state.case_id,
                            )
                        )

                        processed_items.append(
                            item
                        )

                st.session_state.evidence_items.extend(
                    processed_items
                )

                add_evidence_to_case(
                    st.session_state.case_id,
                    processed_items,
                )

                # Re-run the agent
                # including evidence.

                st.session_state.analysis_result = (
                    analyse_case(
                        st.session_state.active_case,
                        st.session_state.evidence_items,
                    )
                )

                update_case_analysis(
                    st.session_state.case_id,
                    st.session_state.analysis_result,
                )

                st.success(
                    f"Processed "
                    f"{len(processed_items)} "
                    "evidence file(s)."
                )

        review = {}

        if st.session_state.analysis_result:

            review = (
                st.session_state
                .analysis_result
                .get(
                    "evidence_review",
                    {},
                )
            )

        # -------------------------
        # Overall status
        # -------------------------

        if review:

            st.markdown(
                "### Evidence status"
            )

            status = review.get(
                "overall_status",
                "NO_EVIDENCE_YET",
            )

            if status == "CONFLICTS_FOUND":

                st.error(
                    "Conflicts found — "
                    "review the documents before "
                    "relying on the case analysis."
                )

            elif status == "STRONGLY_SUPPORTED":

                st.success(
                    "Case is strongly supported "
                    "by the uploaded evidence."
                )

            elif status == "PARTIALLY_SUPPORTED":

                st.warning(
                    "Some evidence supports the case, "
                    "but support is incomplete."
                )

            else:

                st.info(
                    "No uploaded document currently "
                    "provides a strong matching signal."
                )

        # -------------------------
        # Documents
        # -------------------------

        if st.session_state.evidence_items:

            st.markdown(
                "### Processed evidence"
            )

            for item in (
                st.session_state.evidence_items
            ):

                verification = (
                    item.get(
                        "verification"
                    )
                    or {}
                )

                with st.expander(
                    item["filename"]
                ):

                    st.write(
                        f"**Type:** "
                        f"{item['file_type']}  \n"
                        f"**Text extracted:** "
                        f"{item['characters_extracted']} characters  \n"
                        f"**SHA-256:** "
                        f"`{item.get('sha256', 'N/A')}`"
                    )

                    st.write(
                        f"**Verification:** "
                        f"{verification.get('status', 'NOT REVIEWED')}  \n"
                        f"**Confidence:** "
                        f"{verification.get('score', 0)}/"
                        f"{verification.get('max_score', 10)}"
                    )

                    if verification.get(
                        "matched_signals"
                    ):

                        st.success(
                            "Matched: "
                            + " | ".join(
                                verification[
                                    "matched_signals"
                                ]
                            )
                        )

                    if verification.get(
                        "conflicts"
                    ):

                        for conflict in verification[
                            "conflicts"
                        ]:

                            st.error(
                                conflict
                            )

                    signals = item.get(
                        "signals",
                        {},
                    )

                    st.write(
                        f"**References found:** "
                        f"{', '.join(signals.get('references', [])) or 'None'}  \n"
                        f"**Dates found:** "
                        f"{', '.join(signals.get('dates', [])) or 'None'}  \n"
                        f"**Amounts found:** "
                        f"{', '.join(signals.get('amounts', [])) or 'None'}"
                    )

                    if item.get(
                        "text_preview"
                    ):

                        st.text_area(
                            "Extracted text preview",
                            value=item[
                                "text_preview"
                            ],
                            height=220,
                            disabled=True,
                            key=(
                                "preview_"
                                + item.get(
                                    "evidence_id",
                                    item["filename"],
                                )
                            ),
                        )

                    else:

                        st.warning(
                            "No readable text was extracted "
                            "from this file. It may be "
                            "a scanned PDF."
                        )


# =========================================================
# 3. MULTI-AGENT ASSESSMENT
# =========================================================

with agent_tab:

    st.subheader("Multi-agent assessment")
    st.caption("Run the full evidence, policy, resolution, and reviewer workflow before making a company decision.")

    if not st.session_state.active_case:

        st.info(
            "Create or load a case first."
        )

    else:

        case = (
            st.session_state.active_case
        )

        result = (
            st.session_state.analysis_result
        )

        # -------------------------
        # Multi-Agent Workflow
        # -------------------------

        st.markdown(
            "## 🤖 Multi-Agent ProofPilot"
        )

        st.caption(
            "Query Analyst → Evidence Analyst → "
            "Policy Analyst → Resolution Analyst → Reviewer Agent"
        )

        st.write(
            "Four specialised agents independently "
            "analyse the case before ProofPilot "
            "recommends a resolution."
        )

        if st.button(
            "Run Multi-Agent Workflow",
            type="primary",
            key="run_multi_agent",
        ):

            with st.spinner(
                "ProofPilot agents are analysing "
                "the case..."
            ):

                agentic_result = (
                    run_agentic_workflow(
                        case,
                        result,
                    )
                )

                st.session_state.agentic_analysis = (
                agentic_result
            )

            update_agentic_analysis(
                st.session_state.case_id,
                agentic_result,
            )

            final_status = (
                agentic_result.get(
                    "final_status",
                    "UNKNOWN",
                )
            )

            if final_status == (
                "MORE_EVIDENCE_REQUIRED"
            ):

                company_status = (
                    "MORE_EVIDENCE_REQUIRED"
                )

            elif final_status == (
                "CONFLICT_REQUIRES_REVIEW"
            ):

                company_status = (
                    "COMPANY_ESCALATED"
                )

            elif final_status == (
                "POLICY_NON_COMPLIANT"
            ):

                company_status = (
                    "COMPANY_ESCALATED"
                )

            elif final_status == (
                "POLICY_REQUIRES_REVIEW"
            ):

                company_status = (
                    "POLICY_REQUIRES_REVIEW"
                )

            elif final_status == (
                "READY_FOR_COMPANY_REVIEW"
            ):

                company_status = (
                    "READY_FOR_COMPANY_REVIEW"
                )

            else:

                company_status = "AI_ASSESSED"

            st.session_state.case_status = (
                company_status
            )

            update_case_status(
                st.session_state.case_id,
                company_status,
            )

            st.success(
                "Multi-agent analysis completed."
            )

agentic_result = (
            st.session_state.get(
                "agentic_analysis"
            )
        )

if agentic_result:

            # -------------------------
            # Final decision
            # -------------------------

            final_status = (
                agentic_result.get(
                    "final_status",
                    "UNKNOWN",
                )
            )

            st.markdown(
                "### 🎯 Final Agent Decision"
            )

            if final_status == (
                "READY_FOR_COMPANY_REVIEW"
            ):

                st.success(
                    "🟢 READY FOR COMPANY REVIEW"
                )

            elif final_status == (
                "MORE_EVIDENCE_REQUIRED"
            ):

                st.warning(
                    "🟡 MORE EVIDENCE REQUIRED"
                )

            elif final_status == (
                "CONFLICT_REQUIRES_REVIEW"
            ):

                st.error(
                    "🔴 CONFLICT REQUIRES REVIEW"
                )

            elif final_status == (
                "POLICY_NON_COMPLIANT"
            ):

                st.error(
                    "🔴 POLICY NON-COMPLIANT — ESCALATE"
                )

            elif final_status == (
                "POLICY_REQUIRES_REVIEW"
            ):

                st.warning(
                    "🟡 POLICY REVIEW REQUIRED"
                )

            else:

                st.info(
                    final_status
                )

            # -------------------------
            # Pipeline
            # -------------------------

            st.markdown(
                "### 🔄 Agent Pipeline"
            )

            pipeline = (
                agentic_result.get(
                    "pipeline",
                    [],
                )
                or []
            )

            if pipeline:

                st.write(
                    " → ".join(
                        pipeline
                    )
                )

            # -------------------------
            # Query Analyst
            # -------------------------

            query = (
                agentic_result.get(
                    "query_analysis",
                    {},
                )
                or {}
            )

            with st.expander(
                "🔎 Query Analyst",
                expanded=True,
            ):

                st.write(
                    f"**User goal:** "
                    f"{query.get('user_goal', '')}"
                )

                st.write(
                    f"**Core problem:** "
                    f"{query.get('core_problem', '')}"
                )

                st.write(
                    f"**Requested resolution:** "
                    f"{query.get('requested_resolution', '')}"
                )

                if query.get(
                    "important_facts"
                ):

                    st.markdown(
                        "**Important facts**"
                    )

                    for item in query[
                        "important_facts"
                    ]:

                        st.write(
                            f"- {item}"
                        )

                if query.get(
                    "missing_information"
                ):

                    st.markdown(
                        "**Missing information**"
                    )

                    for item in query[
                        "missing_information"
                    ]:

                        st.write(
                            f"- {item}"
                        )

                if query.get(
                    "risk_flags"
                ):

                    st.markdown(
                        "**Risk flags**"
                    )

                    for item in query[
                        "risk_flags"
                    ]:

                        st.warning(
                            item
                        )

            # -------------------------
            # Evidence Analyst
            # -------------------------

            evidence = (
                agentic_result.get(
                    "evidence_analysis",
                    {},
                )
                or {}
            )

            with st.expander(
                "📁 Evidence Analyst",
                expanded=True,
            ):

                st.write(
                    f"**Overall evidence assessment:** "
                    f"{evidence.get('overall_evidence_assessment', 'UNKNOWN')}"
                )

                mappings = (
                    evidence.get(
                        "claim_evidence_map",
                        [],
                    )
                    or []
                )

                if mappings:

                    st.markdown(
                        "**Claim → Evidence mapping**"
                    )

                    for mapping in mappings:

                        st.write(
                            f"**Claim:** "
                            f"{mapping.get('claim', '')}"
                        )

                        st.write(
                            f"**Documents:** "
                            f"{', '.join(mapping.get('documents', []) or [])}"
                        )

                        st.write(
                            f"**Strength:** "
                            f"{mapping.get('strength', '')}"
                        )

                        st.caption(
                            mapping.get(
                                "reason",
                                "",
                            )
                        )

                        st.divider()

                if evidence.get(
                    "unsupported_claims"
                ):

                    st.markdown(
                        "**Unsupported claims**"
                    )

                    for item in evidence[
                        "unsupported_claims"
                    ]:

                        st.warning(
                            item
                        )

                if evidence.get(
                    "conflicts"
                ):

                    st.markdown(
                        "**Conflicts**"
                    )

                    for item in evidence[
                        "conflicts"
                    ]:

                        st.error(
                            item
                        )

                if evidence.get(
                    "missing_evidence"
                ):

                    st.markdown(
                        "**Missing evidence**"
                    )

                    for item in evidence[
                        "missing_evidence"
                    ]:

                        st.warning(
                            item
                        )
            # -------------------------
            # Policy Analyst
            # -------------------------

            policy = (
                agentic_result.get(
                    "policy_analysis",
                    {},
                )
                or {}
            )

            with st.expander(
                "📜 Policy Analyst",
                expanded=True,
            ):

                policy_status = policy.get(
                    "compliance_status",
                    "UNKNOWN",
                )

                if policy_status == (
                    "COMPLIANT"
                ):

                    st.success(
                        "🟢 Policy status: COMPLIANT"
                    )

                elif policy_status == (
                    "PARTIALLY_COMPLIANT"
                ):

                    st.warning(
                        "🟡 Policy status: "
                        "PARTIALLY COMPLIANT"
                    )

                elif policy_status == (
                    "NON_COMPLIANT"
                ):

                    st.error(
                        "🔴 Policy status: "
                        "NON-COMPLIANT"
                    )

                elif policy_status == (
                    "POLICY_UNCLEAR"
                ):

                    st.warning(
                        "🟠 Policy status: "
                        "POLICY UNCLEAR"
                    )

                elif policy_status == (
                    "NO_POLICY_PROVIDED"
                ):

                    st.info(
                        "⚪ No company policy provided."
                    )

                else:

                    st.info(
                        f"Policy status: "
                        f"{policy_status}"
                    )

                if policy.get(
                    "rule_checks"
                ):

                    st.markdown(
                        "**Policy rule checks**"
                    )

                    for rule in policy[
                        "rule_checks"
                    ]:

                        rule_status = str(
                            rule.get(
                                "status",
                                "UNKNOWN",
                            )
                        ).upper()

                        if rule_status == (
                            "SATISFIED"
                        ):

                            st.success(
                                f"✓ {rule.get('rule', '')}"
                            )

                        elif rule_status == (
                            "NOT_SATISFIED"
                        ):

                            st.error(
                                f"✗ {rule.get('rule', '')}"
                            )

                        else:

                            st.warning(
                                f"⚠ {rule.get('rule', '')}"
                            )

                        if rule.get(
                            "reason"
                        ):

                            st.caption(
                                rule["reason"]
                            )

                if policy.get(
                    "violations"
                ):

                    st.markdown(
                        "**Policy violations**"
                    )

                    for item in policy[
                        "violations"
                    ]:

                        st.error(
                            item
                        )

                if policy.get(
                    "missing_policy_evidence"
                ):

                    st.markdown(
                        "**Missing policy evidence**"
                    )

                    for item in policy[
                        "missing_policy_evidence"
                    ]:

                        st.warning(
                            item
                        )

                if policy.get(
                    "reasoning"
                ):

                    st.markdown(
                        "**Policy reasoning**"
                    )

                    for item in policy[
                        "reasoning"
                    ]:

                        st.write(
                            f"- {item}"
                        )

                recommended_policy_action = (
                    policy.get(
                        "recommended_policy_action"
                    )
                )

                if recommended_policy_action:

                    st.write(
                        f"**Recommended policy action:** "
                        f"{recommended_policy_action}"
                    )
            # -------------------------
            # Resolution Analyst
            # -------------------------

            resolution = (
                agentic_result.get(
                    "resolution_analysis",
                    {},
                )
                or {}
            )

            with st.expander(
                "💡 Resolution Analyst",
                expanded=True,
            ):

                st.write(
                    f"**Recommended resolution:** "
                    f"{resolution.get('recommended_resolution', '')}"
                )

                confidence = resolution.get(
                    "confidence"
                )

                if confidence is not None:

                    st.metric(
                        "Resolution confidence",
                        f"{confidence}%",
                    )

                if resolution.get(
                    "reasoning"
                ):

                    st.markdown(
                        "**Reasoning**"
                    )

                    for item in resolution[
                        "reasoning"
                    ]:

                        st.write(
                            f"- {item}"
                        )

                if resolution.get(
                    "evidence_basis"
                ):

                    st.markdown(
                        "**Evidence basis**"
                    )

                    for item in resolution[
                        "evidence_basis"
                    ]:

                        st.write(
                            f"- {item}"
                        )

                if resolution.get(
                    "additional_evidence_needed"
                ):

                    st.markdown(
                        "**Additional evidence needed**"
                    )

                    for item in resolution[
                        "additional_evidence_needed"
                    ]:

                        st.warning(
                            item
                        )

                if resolution.get(
                    "next_actions"
                ):

                    st.markdown(
                        "**Next actions**"
                    )

                    for number, item in enumerate(
                        resolution[
                            "next_actions"
                        ],
                        start=1,
                    ):

                        st.write(
                            f"{number}. {item}"
                        )

                if resolution.get(
                    "escalation_strategy"
                ):

                    st.markdown(
                        "**Escalation strategy**"
                    )

                    for item in resolution[
                        "escalation_strategy"
                    ]:

                        st.write(
                            f"- {item}"
                        )

            # -------------------------
            # Reviewer Agent
            # -------------------------

            reviewer = (
                agentic_result.get(
                    "reviewer_analysis",
                    {},
                )
                or {}
            )

            with st.expander(
                "🛡️ Reviewer / Critic Agent",
                expanded=True,
            ):

                decision = reviewer.get(
                    "decision",
                    "UNKNOWN",
                )

                st.write(
                    f"**Decision:** {decision}"
                )

                if reviewer.get(
                    "approved_for_user_review",
                    False,
                ):

                    st.success(
                        "Reviewer accepts the "
                        "proposed resolution "
                        "for user review."
                    )

                else:

                    st.warning(
                        "Reviewer wants the "
                        "identified concerns "
                        "addressed first."
                    )

                if reviewer.get(
                    "supporting_reasons"
                ):

                    st.markdown(
                        "**Supporting reasons**"
                    )

                    for item in reviewer[
                        "supporting_reasons"
                    ]:

                        st.write(
                            f"- {item}"
                        )

                if reviewer.get(
                    "concerns"
                ):

                    st.markdown(
                        "**Reviewer concerns**"
                    )

                    for item in reviewer[
                        "concerns"
                    ]:

                        st.warning(
                            item
                        )

                if reviewer.get(
                    "required_changes"
                ):

                    st.markdown(
                        "**Required changes**"
                    )

                    for item in reviewer[
                        "required_changes"
                    ]:

                        st.write(
                            f"- {item}"
                        )

                reviewer_confidence = (
                    reviewer.get(
                        "reviewer_confidence"
                    )
                )

                if reviewer_confidence is not None:

                    st.metric(
                        "Reviewer confidence",
                        f"{reviewer_confidence}%",
                    )

                else:

                    st.info(
                "Run the Multi-Agent Workflow "
                "to analyse the query, evidence, "
                "resolution, and risks."
            )
                        # -------------------------
            # Company Decision Gate
            # -------------------------

            st.divider()

            st.markdown(
                "## 🏢 Company Decision"
            )

            st.write(
                "Review the AI assessment and "
                "make the final company decision "
                "for this case."
            )
                        # -------------------------
            # Case Strength
            # -------------------------

            case_strength = (
                calculate_case_strength(
                    case,
                    result,
                    agentic_result,
                )
            )

            strength_score = (
                case_strength["score"]
            )

            strength_label = (
                case_strength["strength"]
            )

            st.markdown(
                "### 📊 Case Strength"
            )

            strength_col1, strength_col2 = (
                st.columns(2)
            )

            with strength_col1:

                st.metric(
                    "Case Strength",
                    f"{strength_score}/100",
                )

            with strength_col2:

                st.metric(
                    "Assessment",
                    strength_label,
                )

            breakdown = (
                case_strength["breakdown"]
            )

            with st.expander(
                "View score breakdown"
            ):

                st.write(
                    f"**Evidence coverage:** "
                    f"{breakdown['evidence_coverage']}/25"
                )

                st.write(
                    f"**Evidence quality:** "
                    f"{breakdown['evidence_quality']}/20"
                )

                st.write(
                    f"**Claim support:** "
                    f"{breakdown['claim_support']}/20"
                )

                st.write(
                    f"**Consistency:** "
                    f"{breakdown['consistency']}/20"
                )

                st.write(
                    f"**Conflict penalty:** "
                    f"-{breakdown['conflict_penalty']}"
                )

                st.write(
                    f"**Missing evidence penalty:** "
                    f"-{breakdown['missing_evidence_penalty']}"
                )
                            # -------------------------
            # AI Recommended Action
            # -------------------------

            st.markdown(
                "### 🤖 Recommended Company Action"
            )

            resolution_data = (
                agentic_result.get(
                    "resolution_analysis",
                    {},
                )
                or {}
            )

            reviewer_data = (
                agentic_result.get(
                    "reviewer_analysis",
                    {},
                )
                or {}
            )

            final_agent_status = (
                agentic_result.get(
                    "final_status",
                    "UNKNOWN",
                )
            )

            policy_analysis = (
                agentic_result.get(
                    "policy_analysis",
                    {},
                )
                or {}
            )

            policy_status = policy_analysis.get(
                "compliance_status",
                "POLICY_UNCLEAR",
            )

            policy_action = policy_analysis.get(
                "recommended_policy_action",
                "HUMAN_REVIEW",
            )

            if (
                policy_status == "NON_COMPLIANT"
                or policy_action in (
                    "REJECT",
                    "ESCALATE",
                )
            ):

                recommended_action = "REJECT / ESCALATE"
                recommendation_reason = (
                    "The Policy Analyst identified a policy compliance problem. "
                    "Company review or escalation is required."
                )

            elif (
                policy_status == "POLICY_UNCLEAR"
                or policy_action == "HUMAN_REVIEW"
            ):

                recommended_action = "REVIEW POLICY / HUMAN REVIEW"
                recommendation_reason = (
                    "Policy compliance could not be established automatically."
                )

            elif policy_action == "REQUEST_MORE_EVIDENCE":

                recommended_action = "REQUEST MORE EVIDENCE"
                recommendation_reason = (
                    "The Policy Analyst identified missing evidence required "
                    "to apply the company policy."
                )

            elif final_agent_status == "CONFLICT_REQUIRES_REVIEW":

                recommended_action = "REJECT / ESCALATE"
                recommendation_reason = (
                    "Conflicting evidence requires company review."
                )

            elif final_agent_status == "MORE_EVIDENCE_REQUIRED":

                recommended_action = "REQUEST MORE EVIDENCE"
                recommendation_reason = (
                    "The evidence assessment indicates additional material is "
                    "needed before a company decision."
                )

            elif (
                strength_score >= 75
                and final_agent_status == "READY_FOR_COMPANY_REVIEW"
            ):

                recommended_action = "APPROVE / REFUND"
                recommendation_reason = (
                    "The case has strong evidence support and the reviewer "
                    "found no blocking issue."
                )

            elif strength_score >= 75:

                recommended_action = "APPROVE / REFUND"
                recommendation_reason = (
                    "The case strength is high and the available evidence "
                    "strongly supports the claim."
                )

            else:

                recommended_action = "REQUEST MORE EVIDENCE"
                recommendation_reason = (
                    "The case strength is below the threshold for confident "
                    "approval. Additional evidence should be obtained before "
                    "making a final decision."
                )

            st.warning(
                f"**Recommended action: "
                f"{recommended_action}**"
            )

            st.caption(
                recommendation_reason
            )

            proposed_resolution = (
                resolution_data.get(
                    "recommended_resolution"
                )
            )

            if proposed_resolution:

                st.write(
                    f"**Resolution Analyst:** "
                    f"{proposed_resolution}"
                )

            reviewer_decision = (
                reviewer_data.get(
                    "decision"
                )
            )

            if reviewer_decision:

                st.write(
                    f"**Reviewer assessment:** "
                    f"{reviewer_decision}"
                )

            current_decision = (
                st.session_state.get(
                    "company_decision"
                )
            )

            if current_decision:

                st.info(
                    f"Current company decision: "
                    f"{current_decision}"
                )

                if st.session_state.get(
                    "decision_reason"
                ):

                    st.caption(
                        "Reason: "
                        + st.session_state[
                            "decision_reason"
                        ]
                    )

            else:

                st.markdown(
                    "### Select an action"
                )

                decision_col1, decision_col2, decision_col3 = (
                    st.columns(3)
                )

                with decision_col1:

                    if st.button(
                        "✅ Approve / Refund",
                        type="primary",
                        use_container_width=True,
                        key="approve_case",
                    ):

                        decision = (
                            "APPROVED"
                        )

                        reason = (
                            "Company approved "
                            "the customer claim "
                            "based on the available "
                            "case assessment."
                        )

                        update_company_decision(
                            st.session_state.case_id,
                            decision,
                            reason,
                            "Company Reviewer",
                        )

                        st.session_state.company_decision = (
                            decision
                        )

                        st.session_state.case_status = (
                            decision
                        )

                        st.session_state.decision_reason = (
                            reason
                        )

                        st.success(
                            "Case approved."
                        )

                        st.rerun()

                with decision_col2:

                    if st.button(
                        "📄 Request More Evidence",
                        use_container_width=True,
                        key="request_evidence",
                    ):

                        decision = (
                            "MORE_EVIDENCE_REQUESTED"
                        )

                        reason = (
                            "Additional evidence "
                            "is required before "
                            "the company can make "
                            "a final decision."
                        )

                        update_company_decision(
                            st.session_state.case_id,
                            decision,
                            reason,
                            "Company Reviewer",
                        )

                        st.session_state.company_decision = (
                            decision
                        )

                        st.session_state.case_status = (
                            decision
                        )

                        st.session_state.decision_reason = (
                            reason
                        )

                        st.success(
                            "More evidence requested."
                        )

                        st.rerun()

                with decision_col3:

                    if st.button(
                        "⚠️ Reject / Escalate",
                        use_container_width=True,
                        key="reject_case",
                    ):

                        decision = (
                            "REJECTED_ESCALATED"
                        )

                        reason = (
                            "Company rejected "
                            "the claim or escalated "
                            "the case for further "
                            "human review."
                        )

                        update_company_decision(
                            st.session_state.case_id,
                            decision,
                            reason,
                            "Company Reviewer",
                        )

                        st.session_state.company_decision = (
                            decision
                        )

                        st.session_state.case_status = (
                            decision
                        )

                        st.session_state.decision_reason = (
                            reason
                        )

                        st.success(
                            "Case rejected / escalated."
                        )

                        st.rerun()
# =========================================================
# 4. RESOLUTION PACKAGE
# =========================================================

with package_tab:

    st.subheader(
        "Resolution Package"
    )

    if not st.session_state.active_case:

        st.info(
            "Create or load a case first."
        )

    else:

        case = (
            st.session_state.active_case
        )

        result = (
            st.session_state.analysis_result
        )

        case_id = (
            st.session_state.case_id
        )

        evidence_items = (
            st.session_state.evidence_items
        )

        ai_analysis = (
            st.session_state.ai_analysis
        )

        agentic_analysis = (
            st.session_state.agentic_analysis
        )

                # -------------------------
        # Final multi-agent status
        # -------------------------

        evidence_conflicts = (
            result
            .get(
                "evidence_review",
                {},
            )
            .get(
                "conflicts",
                0,
            )
        )

        agentic_data = (
            agentic_analysis
            or {}
        )

        final_agent_status = (
            agentic_data.get(
                "final_status",
                "NOT_RUN",
            )
        )

        reviewer_data = (
            agentic_data.get(
                "reviewer_analysis",
                {},
            )
            or {}
        )

        reviewer_decision = (
            reviewer_data.get(
                "decision",
                "NOT_RUN",
            )
        )

        if evidence_conflicts:

            st.error(
                "🔴 Status: BLOCKED — "
                "evidence conflicts require "
                "user review."
            )

        elif final_agent_status == (
            "CONFLICT_REQUIRES_REVIEW"
        ):

            st.error(
                "🔴 Status: BLOCKED — "
                "Reviewer identified conflicting "
                "evidence."
            )

        elif final_agent_status == (
            "POLICY_NON_COMPLIANT"
        ):

            st.error(
                "🔴 Status: POLICY NON-COMPLIANT — "
                "company escalation is required."
            )

        elif final_agent_status == (
            "POLICY_REQUIRES_REVIEW"
        ):

            st.warning(
                "🟡 Status: POLICY REVIEW REQUIRED"
            )

            st.caption(
                "The available policy could not be "
                "applied automatically."
            )

        elif final_agent_status == (
            "MORE_EVIDENCE_REQUIRED"
        ):

            st.warning(
                "🟡 Status: MORE EVIDENCE REQUIRED"
            )

            st.caption(
                f"Reviewer decision: "
                f"{reviewer_decision}"
            )

        elif final_agent_status == (
            "READY_FOR_COMPANY_REVIEW"
        ):

            st.success(
                "🟢 Status: READY FOR COMPANY REVIEW"
            )

            st.caption(
                f"Reviewer decision: "
                f"{reviewer_decision}"
            )

        else:

            st.info(
                "⚪ Status: Draft — "
                "multi-agent review has not "
                "been run yet."
            )

        st.markdown(
            "### Complaint draft"
        )

        st.code(
            result["complaint"],
            language=None,
        )

        package = (
            build_resolution_package(
                case,
                result,
                case_id,
                evidence_items,
                ai_analysis,
                agentic_analysis,
            )
        )

        st.download_button(
            label="Download resolution package",
            data=package,
            file_name=(
                f"{case_id}"
                "_resolution_package.md"
            ),
            mime="text/markdown",
            type="primary",
        )
