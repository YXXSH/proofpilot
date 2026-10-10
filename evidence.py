import hashlib
import re
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

EVIDENCE_FOLDER = Path("data") / "evidence"

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

ISSUE_KEYWORDS = {
    "Defective product": [
        "defective",
        "damaged",
        "broken",
        "faulty",
        "damage",
        "screen",
        "display",
    ],
    "Refund not received": [
        "refund",
        "refunded",
        "refund pending",
        "refund not received",
    ],
    "Incorrect bill or charge": [
        "invoice",
        "bill",
        "charged",
        "charge",
        "amount",
        "payment",
    ],
    "Delivery problem": [
        "delivery",
        "delivered",
        "late",
        "tracking",
        "shipment",
        "courier",
    ],
    "Subscription problem": [
        "subscription",
        "renewal",
        "recurring",
        "cancelled",
        "canceled",
    ],
    "Service complaint": [
        "support",
        "service",
        "complaint",
        "ticket",
        "customer care",
    ],
    "Other": [],
}


def safe_filename(filename):
    return re.sub(r"[^a-zA-Z0-9._-]", "_", filename)


def normalize(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def extract_text_from_pdf(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))
    pages = []

    for page in reader.pages[:20]:
        pages.append(page.extract_text() or "")

    return "\n".join(pages).strip()


def extract_text_from_file(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    extension = Path(uploaded_file.name).suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_bytes)

    if extension == ".txt":
        return file_bytes.decode("utf-8", errors="ignore").strip()

    return ""


def find_evidence_signals(text):
    """
    Detect structured information from uploaded evidence.

    The whitespace is deliberately limited to spaces/tabs so the
    regex does not jump from a label to an unrelated word on
    another line.
    """

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

    references = re.findall(
        reference_pattern,
        text or "",
        flags=re.IGNORECASE,
    )

    dates = re.findall(
        date_pattern,
        text or "",
        flags=re.IGNORECASE,
    )

    amounts = re.findall(
        amount_pattern,
        text or "",
        flags=re.IGNORECASE,
    )

    lower_text = (text or "").lower()

    mentioned_companies = [
        company.title()
        for company in KNOWN_COMPANIES
        if company in lower_text
    ]

    support_terms = [
        "support",
        "customer care",
        "customer service",
        "complaint",
        "ticket",
        "email",
        "chat",
        "escalation",
    ]

    return {
        "references": list(dict.fromkeys(references)),
        "dates": list(dict.fromkeys(dates)),
        "amounts": list(dict.fromkeys(amounts)),
        "mentioned_companies": list(
            dict.fromkeys(mentioned_companies)
        ),
        "support_mentioned": any(
            term in lower_text for term in support_terms
        ),
    }


def _case_amounts(case):
    text = " ".join(
        [
            str(case.get("description", "")),
            str(case.get("desired_resolution", "")),
        ]
    )

    amount_pattern = (
        r"(?:"
        r"₹\s?\d[\d,]*(?:\.\d{1,2})?"
        r"|"
        r"\b(?:rs\.?|inr)\s?\d[\d,]*(?:\.\d{1,2})?"
        r")"
    )

    return re.findall(
        amount_pattern,
        text,
        flags=re.IGNORECASE,
    )


def verify_evidence_against_case(case, evidence_item):
    """
    Compare one uploaded document against the active case.

    Maximum score = 10:
    company  = 2
    reference = 3
    date = 2
    issue = 2
    amount = 1
    """

    text = str(
        evidence_item.get("text_preview", "")
    )

    lower_text = text.lower()

    signals = evidence_item.get(
        "signals",
        {},
    )

    score = 0
    matched = []
    conflicts = []

    # -------------------------
    # Company
    # -------------------------

    company = str(
        case.get("company", "")
    ).strip()

    if company:
        company_key = company.lower().split()[0]

        mentioned = [
            c.lower()
            for c in signals.get(
                "mentioned_companies",
                [],
            )
        ]

        if (
            company_key in lower_text
            or any(
                company_key in item
                for item in mentioned
            )
        ):
            score += 2
            matched.append(
                f"Company: {company}"
            )

        elif mentioned:
            conflicts.append(
                f"Case company is {company}, "
                f"but evidence mentions "
                f"{', '.join(signals['mentioned_companies'])}."
            )

    # -------------------------
    # Order/reference
    # -------------------------

    order_id = str(
        case.get("order_id", "")
    ).strip()

    if order_id:
        if normalize(order_id) in normalize(text):
            score += 3
            matched.append(
                f"Order/reference: {order_id}"
            )

    # -------------------------
    # Date
    # -------------------------

    event_date = str(
        case.get("event_date", "")
    ).strip()

    if event_date:
        if normalize(event_date) in normalize(text):
            score += 2
            matched.append(
                f"Date: {event_date}"
            )

    # -------------------------
    # Issue
    # -------------------------

    issue_type = str(
        case.get(
            "issue_type",
            "Other",
        )
    )

    issue_terms = ISSUE_KEYWORDS.get(
        issue_type,
        [],
    )

    issue_matches = [
        term
        for term in issue_terms
        if term in lower_text
    ]

    if issue_matches:
        score += 2

        matched.append(
            "Issue terms: "
            + ", ".join(
                issue_matches[:5]
            )
        )

    # -------------------------
    # Amount
    # -------------------------

    case_amounts = _case_amounts(case)

    evidence_amounts = signals.get(
        "amounts",
        [],
    )

    normalized_evidence_amounts = {
        normalize(x)
        for x in evidence_amounts
    }

    amount_matches = [
        x
        for x in case_amounts
        if normalize(x)
        in normalized_evidence_amounts
    ]

    if amount_matches:
        score += 1

        matched.append(
            "Amount: "
            + amount_matches[0]
        )

    # -------------------------
    # Classification
    # -------------------------

    if conflicts:
        status = "CONFLICTS_FOUND"

    elif score >= 7:
        status = "STRONG_MATCH"

    elif score >= 4:
        status = "PARTIAL_MATCH"

    else:
        status = "NO_MATCHING_SIGNAL"

    return {
        "status": status,
        "score": score,
        "max_score": 10,
        "confidence": round(
            score / 10,
            2,
        ),
        "matched_signals": matched,
        "conflicts": conflicts,
    }


def process_uploaded_file(
    uploaded_file,
    case_id,
):
    case_folder = (
        EVIDENCE_FOLDER / case_id
    )

    case_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_name = safe_filename(
        uploaded_file.name
    )

    file_bytes = uploaded_file.getvalue()

    file_hash = hashlib.sha256(
        file_bytes
    ).hexdigest()

    saved_path = (
        case_folder / original_name
    )

    # Prevent silent overwrite.
    if saved_path.exists():
        stem = saved_path.stem
        suffix = saved_path.suffix

        saved_path = (
            case_folder
            / f"{stem}_{file_hash[:8]}{suffix}"
        )

    clean_name = saved_path.name

    with open(
        saved_path,
        "wb",
    ) as file:
        file.write(file_bytes)

    extracted_text = (
        extract_text_from_file(
            uploaded_file
        )
    )

    signals = find_evidence_signals(
        extracted_text
    )

    return {
        "evidence_id": file_hash[:12].upper(),
        "filename": clean_name,
        "file_type": saved_path.suffix.lower(),
        "size_bytes": len(file_bytes),
        "sha256": file_hash,
        "saved_path": str(saved_path),
        "characters_extracted": len(
            extracted_text
        ),
        "text_preview": extracted_text[:3000],
        "signals": signals,
        "verification": None,
    }


def build_evidence_review(
    case,
    evidence_items,
):
    reviewed_items = []

    for item in evidence_items or []:
        reviewed = dict(item)

        reviewed[
            "verification"
        ] = verify_evidence_against_case(
            case,
            item,
        )

        reviewed_items.append(
            reviewed
        )

    strong = [
        x
        for x in reviewed_items
        if x["verification"]["status"]
        == "STRONG_MATCH"
    ]

    partial = [
        x
        for x in reviewed_items
        if x["verification"]["status"]
        == "PARTIAL_MATCH"
    ]

    conflicts = [
        x
        for x in reviewed_items
        if x["verification"]["status"]
        == "CONFLICTS_FOUND"
    ]

    if conflicts:
        overall = "CONFLICTS_FOUND"

    elif strong:
        overall = "STRONGLY_SUPPORTED"

    elif partial:
        overall = "PARTIALLY_SUPPORTED"

    else:
        overall = "NO_EVIDENCE_YET"

    return {
        "documents_checked": len(
            reviewed_items
        ),
        "strong_matches": len(strong),
        "partial_matches": len(partial),
        "conflicts": len(conflicts),
        "items": reviewed_items,
        "overall_status": overall,
    }