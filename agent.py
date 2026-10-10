import re

from evidence import build_evidence_review


KNOWN_COMPANIES = [
    "flipkart",
    "amazon",
    "myntra",
    "apple",
    "samsung",
    "dell",
    "croma",
    "reliance",
    "zomato",
    "swiggy",
    "ola",
    "uber",
    "airtel",
    "jio",
]


def unique_items(items):
    return list(
        dict.fromkeys(
            item
            for item in items
            if item
        )
    )


def extract_case_facts(case):
    description = case[
        "description"
    ].strip()

    lower_description = (
        description.lower()
    )

    reference_pattern = (
        r"(?:order|booking|transaction|reference|ticket|complaint|invoice|tracking)"
        r"(?:[ \t]+(?:id|number|no\.?))?"
        r"[ \t]*(?::|#|-)[ \t]*([a-zA-Z0-9-]{5,})"
    )

    date_pattern = (
        r"\b(?:"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        r"|"
        r"\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*\s+\d{2,4}"
        r")\b"
    )

    amount_pattern = (
        r"(?:"
        r"₹\s?\d[\d,]*(?:\.\d{1,2})?"
        r"|"
        r"\b(?:rs\.?|inr)\s?\d[\d,]*(?:\.\d{1,2})?"
        r")"
    )

    extracted_references = re.findall(
        reference_pattern,
        description,
        flags=re.IGNORECASE,
    )

    extracted_dates = re.findall(
        date_pattern,
        description,
        flags=re.IGNORECASE,
    )

    extracted_amounts = re.findall(
        amount_pattern,
        description,
        flags=re.IGNORECASE,
    )

    mentioned_companies = [
        company.title()
        for company in KNOWN_COMPANIES
        if company in lower_description
    ]

    support_words = [
        "support",
        "customer care",
        "customer service",
        "complaint",
        "called",
        "email",
        "chat",
        "ticket",
    ]

    support_mentioned = any(
        word in lower_description
        for word in support_words
    )

    references = unique_items(
        [
            case["order_id"].strip()
        ]
        + extracted_references
    )

    dates = unique_items(
        [
            case["event_date"].strip()
        ]
        + extracted_dates
    )

    return {
        "references": references,
        "dates": dates,
        "amounts": unique_items(
            extracted_amounts
        ),
        "mentioned_companies": unique_items(
            mentioned_companies
        ),
        "prior_support_mentioned": support_mentioned,
    }


def find_consistency_warnings(
    case,
    facts,
    evidence_review=None,
):
    warnings = []

    entered_company = (
        case["company"]
        .strip()
        .lower()
    )

    mentioned_companies = [
        company.lower()
        for company in facts[
            "mentioned_companies"
        ]
    ]

    if (
        mentioned_companies
        and not any(
            entered_company == company
            or entered_company.split()[0]
            == company.split()[0]
            for company
            in mentioned_companies
        )
    ):
        warnings.append(
            "The company entered in the form "
            "does not match the company "
            "mentioned in the description: "
            + ", ".join(
                facts[
                    "mentioned_companies"
                ]
            )
            + "."
        )

    if (
        not case["event_date"].strip()
        and facts["dates"]
    ):
        warnings.append(
            "A date appears in the description "
            "but was not added to the date field."
        )

    if (
        not case["order_id"].strip()
        and facts["references"]
    ):
        warnings.append(
            "A possible reference number appears "
            "in the description but was not added "
            "to the reference field."
        )

    if (
        evidence_review
        and evidence_review.get(
            "conflicts",
            0,
        )
    ):
        warnings.append(
            f"Evidence review found "
            f"{evidence_review['conflicts']} "
            "document(s) with possible conflicts."
        )

    return warnings


def build_timeline(
    case,
    facts,
    evidence_review=None,
):
    event_date = (
        case["event_date"].strip()
        or (
            facts["dates"][0]
            if facts["dates"]
            else "Date not provided"
        )
    )

    timeline = [
        {
            "date": event_date,
            "event": (
                "Customer reports: "
                + case["description"].strip()
            ),
        }
    ]

    if (
        case["contacted_support"]
        or facts["prior_support_mentioned"]
    ):
        timeline.append(
            {
                "date": "Date not provided",
                "event": (
                    "Customer has already contacted "
                    "support or mentioned an earlier "
                    "support interaction."
                ),
            }
        )

    for item in (
        evidence_review or {}
    ).get("items", []):

        verification = (
            item.get(
                "verification"
            )
            or {}
        )

        if verification.get(
            "status"
        ) in {
            "STRONG_MATCH",
            "PARTIAL_MATCH",
        }:
            timeline.append(
                {
                    "date": "Evidence",
                    "event": (
                        f"{item['filename']} "
                        f"supports the case "
                        f"({verification['status']})."
                    ),
                }
            )

    return timeline


def find_evidence_gaps(
    case,
    facts,
    evidence_review=None,
):
    gaps = []

    review = (
        evidence_review
        or {}
    )

    has_reference_evidence = any(
        item.get(
            "signals",
            {},
        ).get("references")
        for item
        in review.get(
            "items",
            [],
        )
    )

    has_date_evidence = any(
        item.get(
            "signals",
            {},
        ).get("dates")
        for item
        in review.get(
            "items",
            [],
        )
    )

    if (
        not facts["references"]
        and not has_reference_evidence
    ):
        gaps.append(
            "Order, booking, account, invoice, "
            "or transaction reference number"
        )

    if (
        not facts["dates"]
        and not has_date_evidence
    ):
        gaps.append(
            "Date of purchase, delivery, "
            "charge, or incident"
        )

    if (
        not case["contacted_support"]
        and not facts[
            "prior_support_mentioned"
        ]
    ):
        gaps.append(
            "Record of any earlier conversation "
            "with customer support"
        )

    if not review.get(
        "documents_checked"
    ):
        gaps.append(
            "At least one supporting document "
            "such as an invoice, receipt, "
            "order confirmation, or support record"
        )

    if (
        review.get("documents_checked")
        and review.get(
            "overall_status"
        ) == "NO_EVIDENCE_YET"
    ):
        gaps.append(
            "Evidence that directly supports "
            "the central claim"
        )

    if len(
        case["description"].strip()
    ) < 60:
        gaps.append(
            "A fuller description of what happened, "
            "the impact, and the company's response"
        )

    return unique_items(gaps)


def build_action_plan(
    case,
    evidence_gaps,
):
    steps = []

    if evidence_gaps:
        steps.append(
            "Collect the missing evidence identified "
            "by ProofPilot."
        )

    steps.extend(
        [
            "Save receipts, invoices, emails, chats, "
            "delivery records, and screenshots in one folder.",
            "Review the company's official refund, "
            "warranty, delivery, or billing policy.",
            "Send the prepared complaint through "
            "the official support channel.",
            "Save the support ticket number and "
            "set a follow-up reminder.",
        ]
    )

    if (
        case["issue_type"]
        == "Defective product"
    ):
        steps.append(
            "Attach clear photos or videos showing "
            "the defect or incorrect item."
        )

    if (
        case["issue_type"]
        == "Incorrect bill or charge"
    ):
        steps.append(
            "Attach the invoice or bank statement "
            "showing the disputed charge."
        )

    if (
        case["issue_type"]
        == "Refund not received"
    ):
        steps.append(
            "Ask for written confirmation of the "
            "refund amount and processing date."
        )

    if (
        case["issue_type"]
        == "Delivery problem"
    ):
        steps.append(
            "Attach delivery tracking details and "
            "any proof of the delivery issue."
        )

    return steps


def draft_complaint(
    case,
    facts,
):
    reference = (
        case["order_id"].strip()
        or (
            facts["references"][0]
            if facts["references"]
            else "[reference number not available]"
        )
    )

    event_date = (
        case["event_date"].strip()
        or (
            facts["dates"][0]
            if facts["dates"]
            else "[date not available]"
        )
    )

    return f"""Subject: Request for resolution — {case["issue_type"]}

Dear {case["company"]} Support Team,

I am writing about a {case["issue_type"].lower()}.

Reference number: {reference}
Relevant date: {event_date}

Issue summary:
{case["description"].strip()}

I request the following resolution:
{case["desired_resolution"].strip()}

Please confirm receipt of this complaint and let me know the next steps and expected resolution timeline.

Sincerely,
[Your name]
"""


def verify_resolution_package(
    case,
    action_plan,
    complaint,
    warnings,
    evidence_review,
):
    checks = {
        "Company is identified": bool(
            case["company"].strip()
        ),

        "Issue type is identified": bool(
            case["issue_type"].strip()
        ),

        "Problem description is included":
            case["description"].strip()
            in complaint,

        "Requested resolution is included":
            case["desired_resolution"].strip()
            in complaint,

        "Action plan was created":
            len(action_plan) >= 4,

        "No company mismatch detected":
            not any(
                "company entered"
                in warning.lower()
                for warning
                in warnings
            ),

        "Evidence is free of known conflicts":
            evidence_review.get(
                "conflicts",
                0,
            ) == 0,
    }

    return checks


def analyse_case(
    case,
    evidence_items=None,
):
    evidence_items = (
        evidence_items
        or []
    )

    facts = extract_case_facts(
        case
    )

    evidence_review = (
        build_evidence_review(
            case,
            evidence_items,
        )
    )

    warnings = (
        find_consistency_warnings(
            case,
            facts,
            evidence_review,
        )
    )

    timeline = build_timeline(
        case,
        facts,
        evidence_review,
    )

    evidence_gaps = (
        find_evidence_gaps(
            case,
            facts,
            evidence_review,
        )
    )

    action_plan = (
        build_action_plan(
            case,
            evidence_gaps,
        )
    )

    complaint = draft_complaint(
        case,
        facts,
    )

    verification = (
        verify_resolution_package(
            case,
            action_plan,
            complaint,
            warnings,
            evidence_review,
        )
    )

    return {
        "extracted_facts": facts,
        "consistency_warnings": warnings,
        "timeline": timeline,
        "evidence_gaps": evidence_gaps,
        "evidence_review": evidence_review,
        "action_plan": action_plan,
        "complaint": complaint,
        "verification": verification,
    }