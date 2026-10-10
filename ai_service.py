import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai


load_dotenv()


MODEL_NAMES = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
]


def get_gemini_api_key():
    """Read the API key locally or from Streamlit's hosted secret store."""
    api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        return api_key

    try:
        import streamlit as st

        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


def _extract_json(text):
    """
    Try to extract a JSON object from Gemini output.
    Handles normal JSON and ```json fenced responses.
    """

    if not text:
        return None

    text = text.strip()

    # Remove markdown fences.
    fenced_match = re.search(
        r"```(?:json)?\s*(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if fenced_match:
        text = fenced_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fall back to locating the first object.
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end > start:
        candidate = text[start:end + 1]

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None

    return None


def generate_agent_json(
    agent_name,
    instructions,
    payload,
):
    """
    Run one specialist ProofPilot agent and request
    machine-readable JSON.
    """

    api_key = get_gemini_api_key()

    if not api_key:
        return {
            "available": False,
            "agent": agent_name,
            "error": "Gemini key was not found.",
            "data": None,
        }

    prompt = f"""
You are the {agent_name} inside ProofPilot,
an AI consumer-resolution system.

You are one specialist in a multi-agent pipeline.

IMPORTANT RULES:

1. Use only the information provided.
2. Do not invent facts.
3. Do not invent company policies.
4. Do not invent legal rights or legal conclusions.
5. Clearly distinguish evidence from user claims.
6. Identify uncertainty.
7. Return ONLY valid JSON.
8. Do not wrap the JSON in commentary.

YOUR SPECIAL INSTRUCTIONS:

{instructions}

INPUT DATA:

{json.dumps(
    payload,
    indent=2,
    ensure_ascii=False,
)}
"""

    errors = []

    for model_name in MODEL_NAMES:

        try:
            client = genai.Client(
                api_key=api_key,
                http_options={
                    "api_version": "v1",
                    "timeout": 15000,
                },
            )

            response = (
                client
                .models
                .generate_content(
                    model=model_name,
                    contents=prompt,
                )
            )

            raw_text = (
                response.text
                or ""
            )

            parsed = _extract_json(
                raw_text
            )

            if parsed is None:
                raise ValueError(
                    "Gemini returned invalid JSON."
                )

            return {
                "available": True,
                "agent": agent_name,
                "model": model_name,
                "data": parsed,
                "raw_text": raw_text,
            }

        except Exception as error:
            errors.append(
                f"{model_name}: {error}"
            )
            time.sleep(1)

    return {
        "available": False,
        "agent": agent_name,
        "data": None,
        "errors": errors,
        "error": (
            "Agent temporarily unavailable."
        ),
    }


def generate_ai_analysis(
    case,
    rule_based_result,
    evidence_items=None,
):
    """
    Your original general AI review.
    Kept so the existing Agent Workspace
    continues to work.
    """

    evidence_items = (
        evidence_items or []
    )

    evidence_context = []

    for item in evidence_items:

        evidence_context.append(
            {
                "filename": item.get(
                    "filename"
                ),
                "signals": item.get(
                    "signals",
                    {},
                ),
                "verification": (
                    item.get(
                        "verification"
                    )
                    or {}
                ),
                "text_excerpt": item.get(
                    "text_preview",
                    "",
                )[:4000],
            }
        )

    instructions = """
Analyse the consumer case and provide:

1. A clear assessment.
2. Important facts or ambiguities.
3. Evidence that should be preserved.
4. A stronger next action.
5. A polite escalation strategy.

Use plain language.
Do not claim to be a lawyer.
"""

    result = generate_agent_json(
        "General AI Review Agent",
        instructions,
        {
            "case": case,
            "rule_based_analysis": rule_based_result,
            "evidence": evidence_context,
        },
    )

    if result.get("available"):
        return {
            "available": True,
            "model": result.get(
                "model"
            ),
            "text": json.dumps(
                result["data"],
                indent=2,
                ensure_ascii=False,
            ),
        }

    return {
        "available": False,
        "text": (
            "AI analysis is temporarily unavailable. "
            "ProofPilot completed the rule-based "
            "and evidence-based analysis safely."
        ),
        "errors": result.get(
            "errors",
            [],
        ),
    }
