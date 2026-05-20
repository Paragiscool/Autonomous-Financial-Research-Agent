"""
agent/parser.py
Parses raw LLM text responses into structured Python objects.
Handles JSON extraction with graceful fallback for malformed outputs.
"""

import json
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _find_outermost_json(text: str) -> str | None:
    """
    Finds the outermost JSON object by tracking brace depth.
    This is more robust than a greedy regex when the LLM produces
    text with multiple JSON objects or surrounding prose.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def extract_json_from_text(text: str) -> Optional[dict]:
    """
    Extracts a JSON object from an LLM response string.
    Handles cases where the LLM wraps JSON in markdown code fences.
    Uses balanced-brace extraction to avoid greedy regex mis-matches.
    """
    # Strip markdown code fences first (```json ... ``` or ``` ... ```)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        raw = fenced.group(1)
    else:
        # Use balanced-brace extraction — safer than greedy regex
        raw = _find_outermost_json(text)

    if not raw:
        logger.error("Parser: No JSON object found in LLM response.")
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Parser: JSON decode error — {e}. Raw: {raw[:200]}")
        return None


def parse_plan(llm_response: str) -> Optional[dict]:
    """
    Parses the Planner LLM's response into a structured research plan.
    Returns None if parsing fails.
    
    Expected structure:
    {
      "query_summary": str,
      "steps": [ {"step_id": int, "tool": str, "arguments": dict, "purpose": str, "depends_on": list} ],
      "synthesis_goal": str
    }
    """
    data = extract_json_from_text(llm_response)
    if not data:
        return None

    required_keys = {"query_summary", "steps", "synthesis_goal"}
    if not required_keys.issubset(data.keys()):
        logger.error(f"Parser: Plan missing required keys. Got: {list(data.keys())}")
        return None

    # Validate each step
    for i, step in enumerate(data.get("steps", [])):
        if "tool" not in step or "arguments" not in step:
            logger.error(f"Parser: Step {i} is malformed. Missing 'tool' or 'arguments'.")
            return None

    logger.info(f"Parser: Successfully parsed plan with {len(data['steps'])} steps.")
    return data


def parse_executor_response(llm_response: str) -> Optional[dict]:
    """
    Parses the Executor LLM's response after a tool call.
    Returns None if parsing fails.

    Expected structure:
    {
      "step_id": int,
      "status": "success" | "fallback_needed" | "conflict_detected" | "skip",
      "summary": str,
      "revise_plan": bool,
      "revision_note": str
    }
    """
    data = extract_json_from_text(llm_response)
    if not data:
        return None

    valid_statuses = {"success", "fallback_needed", "conflict_detected", "skip"}
    if data.get("status") not in valid_statuses:
        logger.warning(f"Parser: Unknown executor status '{data.get('status')}'. Defaulting to 'success'.")
        data["status"] = "success"

    return data
