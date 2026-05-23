"""
synthesis/engine.py

ARA-1 Synthesis Engine — post-processing layer that sits between raw tool
findings and the final Markdown report.

Responsibilities:
  1. Rank and de-duplicate findings from multiple tools (e.g., yfinance vs SEC).
  2. Route each finding to the correct section of the report template.
  3. Apply a source-priority hierarchy: SEC > yfinance > web_search > earnings_mock.
  4. Pass the ordered, de-duplicated context to the LLM synthesizer prompt.

Design principle: This module is STATELESS — it takes a list of findings
and returns an ordered structure. No LLM calls happen here.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Source priority hierarchy (lower index = higher authority)
# ---------------------------------------------------------------------------
SOURCE_PRIORITY: List[str] = [
    "sec_filing_search",    # 1st — official regulatory filing
    "financial_data_api",   # 2nd — live market data (yfinance)
    "news_sentiment",       # 3rd — market sentiment
    "web_search",           # 4th — general web context
    "earnings_transcript",  # 5th — management commentary
    "company_profile",      # 6th — baseline static profile (lowest authority)
]

# ---------------------------------------------------------------------------
# Section routing: which tools contribute to which report sections
# ---------------------------------------------------------------------------
SECTION_ROUTING: Dict[str, List[str]] = {
    "## Company Overview":      ["company_profile"],
    "## Financial Performance": ["financial_data_api", "earnings_transcript"],
    "## Regulatory & Risk":     ["sec_filing_search"],
    "## Market Sentiment":      ["news_sentiment", "web_search"],
}


def _priority_rank(tool_name: str) -> int:
    """Returns the priority rank for a tool (lower = higher priority)."""
    try:
        return SOURCE_PRIORITY.index(tool_name)
    except ValueError:
        return len(SOURCE_PRIORITY)  # Unknown tools get lowest priority


def rank_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sorts findings by source authority (SOURCE_PRIORITY).
    Higher-authority sources appear first so the LLM synthesizer
    encounters them before lower-quality data.

    Args:
        findings: Raw list of executor observation dicts.

    Returns:
        Sorted list — highest authority first.
    """
    ranked = sorted(findings, key=lambda f: _priority_rank(f.get("tool", "")))
    logger.info(f"[Engine] Ranked {len(ranked)} findings by source priority.")
    return ranked


def deduplicate_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Removes lower-priority duplicates when multiple tools return data
    for the same subject matter.

    Strategy: keeps the FIRST (highest-priority) finding per tool name.
    Within the same tool, keeps only the first successful result.
    """
    seen_tools: set = set()
    deduped = []
    for f in findings:
        tool = f.get("tool", "unknown")
        status = f.get("status", "")
        if tool not in seen_tools and status == "success":
            seen_tools.add(tool)
            deduped.append(f)
        elif status != "success":
            # Always keep failed steps for transparency (verifier sees them)
            deduped.append(f)
    logger.info(f"[Engine] Deduplication: {len(findings)} → {len(deduped)} findings.")
    return deduped


def route_to_sections(
    findings: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Groups findings by their target report section based on SECTION_ROUTING.

    Args:
        findings: Ranked + de-duplicated finding list.

    Returns:
        Dict mapping section header → list of relevant findings.
    """
    sections: Dict[str, List[Dict[str, Any]]] = {k: [] for k in SECTION_ROUTING}
    unrouted: List[Dict[str, Any]] = []

    for finding in findings:
        tool = finding.get("tool", "")
        placed = False
        for section, tools in SECTION_ROUTING.items():
            if tool in tools:
                sections[section].append(finding)
                placed = True
                break
        if not placed:
            unrouted.append(finding)

    if unrouted:
        logger.warning(f"[Engine] {len(unrouted)} findings could not be routed to any section.")

    return sections


def prepare_synthesis_context(
    findings: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Full pipeline: rank → deduplicate → route.

    Returns:
        (ordered_findings, section_map)
        ordered_findings: flat list sorted by priority (for simple prompts)
        section_map:      dict grouped by report section (for structured prompts)
    """
    ranked    = rank_findings(findings)
    deduped   = deduplicate_findings(ranked)
    sections  = route_to_sections(deduped)

    logger.info(
        f"[Engine] Context ready — {len(deduped)} findings across "
        f"{sum(len(v) for v in sections.values())} routed entries."
    )
    return deduped, sections


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    mock_findings = [
        {"tool": "company_profile",   "status": "success", "summary": "AAPL: Apple Inc, Technology sector."},
        {"tool": "web_search",        "status": "success", "summary": "Apple hits $3T market cap in 2025."},
        {"tool": "financial_data_api","status": "success", "summary": "AAPL FY2024 revenue: $391B."},
        {"tool": "sec_filing_search", "status": "success", "summary": "10-K risk: supply chain concentration."},
        {"tool": "news_sentiment",    "status": "success", "summary": "Overall Bullish (avg score: +0.28)."},
        {"tool": "web_search",        "status": "success", "summary": "DUPLICATE — should be removed."},
    ]

    ordered, section_map = prepare_synthesis_context(mock_findings)

    print("\n=== Ordered Findings (by priority) ===")
    for f in ordered:
        print(f"  [{_priority_rank(f['tool'])}] {f['tool']:25s} → {f['summary'][:55]}")

    print("\n=== Section Routing ===")
    for section, items in section_map.items():
        print(f"\n  {section}")
        for item in items:
            print(f"    • {item['tool']}: {item['summary'][:50]}")
