import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


DATA_FOLDER = Path("data")
CASES_FILE = DATA_FOLDER / "cases.json"


def load_cases():
    if not CASES_FILE.exists():
        return []

    try:
        with open(
            CASES_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return []


def write_cases(cases):
    DATA_FOLDER.mkdir(
        exist_ok=True
    )

    with open(
        CASES_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            cases,
            file,
            indent=2,
            ensure_ascii=False,
        )


def save_case(
    case,
    analysis,
):
    case_id = (
        f"PP-{uuid4().hex[:8].upper()}"
    )

    record = {
        "case_id": case_id,
        "created_at": (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        ),

        # Company-side decision state
        "status": "DRAFT",

        # Original case and rule-based analysis
        "case": case,
        "analysis": analysis,

        # Evidence and AI analysis
        "evidence": [],
        "ai_analysis": None,
        "agentic_analysis": None,

        # Company decision record
        "company_decision": None,
        "decision_reason": None,
        "decision_at": None,
        "decision_by": None,
    }

    cases = load_cases()

    cases.insert(
        0,
        record,
    )

    write_cases(cases)

    return case_id


def get_case(case_id):
    for record in load_cases():

        if record.get(
            "case_id"
        ) == case_id:

            return record

    return None


def add_evidence_to_case(
    case_id,
    evidence_items,
):
    cases = load_cases()

    for record in cases:

        if (
            record["case_id"]
            == case_id
        ):

            record.setdefault(
                "evidence",
                [],
            ).extend(
                evidence_items
            )

            write_cases(cases)

            return True

    return False


def update_case_analysis(
    case_id,
    analysis,
):
    cases = load_cases()

    for record in cases:

        if (
            record.get("case_id")
            == case_id
        ):

            record["analysis"] = (
                analysis
            )

            write_cases(cases)

            return True

    return False


def update_ai_analysis(
    case_id,
    ai_analysis,
):
    cases = load_cases()

    for record in cases:

        if (
            record.get("case_id")
            == case_id
        ):

            record["ai_analysis"] = (
                ai_analysis
            )

            write_cases(cases)

            return True

    return False


def update_agentic_analysis(
    case_id,
    agentic_analysis,
):
    cases = load_cases()

    for record in cases:

        if (
            record.get("case_id")
            == case_id
        ):

            record[
                "agentic_analysis"
            ] = agentic_analysis

            write_cases(cases)

            return True

    return False


def update_case_status(
    case_id,
    status,
):
    cases = load_cases()

    for record in cases:

        if (
            record.get("case_id")
            == case_id
        ):

            record["status"] = status

            write_cases(cases)

            return True

    return False


def update_company_decision(
    case_id,
    decision,
    reason="",
    decided_by="Company Reviewer",
):
    cases = load_cases()

    for record in cases:

        if (
            record.get("case_id")
            == case_id
        ):

            record[
                "company_decision"
            ] = decision

            record[
                "decision_reason"
            ] = reason

            record[
                "decision_at"
            ] = (
                datetime.now()
                .isoformat(
                    timespec="seconds"
                )
            )

            record[
                "decision_by"
            ] = decided_by

            # The decision itself becomes
            # the persistent case status.
            record["status"] = decision

            write_cases(cases)

            return True

    return False