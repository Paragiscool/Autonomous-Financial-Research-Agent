"""
evaluation/dashboard.py

Console and file-based dashboard for ARA-1 benchmark results.

Features:
  - Loads a saved benchmark JSON file and renders a rich console report.
  - Compares the latest run against the previous run (if available).
  - Generates a markdown summary report.
  - Highlights pass/fail against the defined targets.

Usage:
    python evaluation/dashboard.py evaluation/benchmarks/run_latest.json
    python evaluation/dashboard.py  # auto-loads most recent benchmark in the folder
"""

import json
import os
import sys
import glob
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

BENCHMARK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmarks")


# ------------------------------------------------------------------
# Loader helpers
# ------------------------------------------------------------------

def load_benchmark(filepath: str) -> Dict[str, Any]:
    """Loads a benchmark JSON file and returns the scorecard dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def find_latest_benchmark(directory: str = BENCHMARK_DIR) -> Optional[str]:
    """Returns the path to the most recently modified benchmark JSON file."""
    pattern = os.path.join(directory, "*.json")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def find_all_benchmarks(directory: str = BENCHMARK_DIR) -> List[str]:
    """Returns all benchmark JSON files sorted newest-first."""
    pattern = os.path.join(directory, "*.json")
    files = glob.glob(pattern)
    return sorted(files, key=os.path.getmtime, reverse=True)


# ------------------------------------------------------------------
# Console renderer
# ------------------------------------------------------------------

def _pass_fail(met: bool) -> str:
    return "✅  PASS" if met else "❌  FAIL"


def _bar(ratio: float, width: int = 30) -> str:
    filled = int(ratio * width)
    return "█" * filled + "░" * (width - filled)


def render_console(scorecard: Dict[str, Any], compare_to: Optional[Dict[str, Any]] = None):
    """
    Renders a detailed console dashboard from a scorecard dict.

    Args:
        scorecard:  The primary benchmark run to display.
        compare_to: An optional previous run to compare against.
    """
    sep = "=" * 70
    thin = "-" * 70

    print("\n" + sep)
    print(f"  🚀  ARA-1 EVALUATION DASHBOARD")
    print(f"  Run Label   : {scorecard.get('run_label', 'N/A')}")
    print(f"  Timestamp   : {scorecard.get('run_timestamp', 'N/A')}")
    print(f"  Run Time    : {scorecard.get('total_run_time_s', 0):.1f}s")
    print(sep)

    # Core KPIs
    sr = scorecard.get("success_rate", 0)
    cr = scorecard.get("cache_utilisation_ratio", 0)
    tr = scorecard.get("tool_success_rate", 0)
    targets = scorecard.get("targets", {})

    print(f"\n  📈 KEY PERFORMANCE INDICATORS\n")

    def _delta(key: str) -> str:
        if compare_to is None:
            return ""
        prev = compare_to.get(key, None)
        cur = scorecard.get(key, None)
        if prev is None or cur is None:
            return ""
        diff = cur - prev
        arrow = "▲" if diff > 0 else ("▼" if diff < 0 else "→")
        return f"  {arrow} {abs(diff)*100:.1f}pp vs prev"

    print(f"  Success Rate      : {sr*100:5.1f}%  {_bar(sr)}  {_pass_fail(targets.get('success_rate_met', False))}{_delta('success_rate')}")
    print(f"  Cache Utilisation : {cr*100:5.1f}%  {_bar(cr)}  {_pass_fail(targets.get('cache_ratio_met', False))}{_delta('cache_utilisation_ratio')}")
    print(f"  Tool Success Rate : {tr*100:5.1f}%  {_bar(tr)}  {_pass_fail(targets.get('tool_success_rate_met', False))}{_delta('tool_success_rate')}")

    # Latency
    print(f"\n  ⏱  LATENCY")
    print(f"  Avg: {scorecard.get('avg_latency_s', 0):.3f}s  |  Min: {scorecard.get('min_latency_s', 0):.3f}s  |  Max: {scorecard.get('max_latency_s', 0):.3f}s")

    # Tool usage
    print(f"\n  🛠  TOOL USAGE")
    print(f"  Total Calls   : {scorecard.get('total_tool_calls', 0)}")
    print(f"  Successes     : {scorecard.get('total_tool_successes', 0)}")
    print(f"  Failures      : {scorecard.get('total_tool_failures', 0)}")

    # Per-query breakdown
    print(f"\n  📋 PER-QUERY BREAKDOWN")
    print(f"  {'#':<4} {'STATUS':<12} {'LATENCY':>8}  {'STEPS':>5}  QUERY")
    print("  " + thin)

    status_icons = {"success": "✅", "cache_hit": "⚡", "failed": "❌", "pending": "⏳"}
    for q in scorecard.get("per_query", []):
        icon = status_icons.get(q["status"], "?")
        label = f"{icon} {q['status']:<10}"
        print(f"  {q['index']:<4} {label} {q['elapsed_s']:>7.2f}s  {q['step_count']:>5}  {q['query'][:45]}")

    # Summary verdict
    all_pass = (
        targets.get("success_rate_met", False)
        and targets.get("cache_ratio_met", False)
        and targets.get("tool_success_rate_met", False)
    )
    print("\n" + sep)
    if all_pass:
        print("  🏆  ALL TARGETS MET — ARA-1 BENCHMARK PASSED")
    else:
        failed_targets = [
            k.replace("_met", "").replace("_", " ").title()
            for k, v in targets.items()
            if k.endswith("_met") and not v
        ]
        print(f"  ⚠️  BENCHMARK INCOMPLETE — Targets not met: {', '.join(failed_targets)}")
    print(sep + "\n")


# ------------------------------------------------------------------
# Markdown report generator
# ------------------------------------------------------------------

def generate_markdown_report(scorecard: Dict[str, Any]) -> str:
    """Generates a Markdown benchmark summary from a scorecard dict."""
    targets = scorecard.get("targets", {})
    lines = [
        f"# ARA-1 Benchmark Report",
        f"",
        f"**Run Label:** `{scorecard.get('run_label', 'N/A')}`  ",
        f"**Timestamp:** {scorecard.get('run_timestamp', 'N/A')}  ",
        f"**Total Run Time:** {scorecard.get('total_run_time_s', 0):.1f}s",
        f"",
        f"## KPI Summary",
        f"",
        f"| Metric | Value | Target | Status |",
        f"|--------|-------|--------|--------|",
        f"| Success Rate | {scorecard.get('success_rate', 0)*100:.1f}% | ≥80% | {'✅' if targets.get('success_rate_met') else '❌'} |",
        f"| Cache Utilisation | {scorecard.get('cache_utilisation_ratio', 0)*100:.1f}% | ≥20% | {'✅' if targets.get('cache_ratio_met') else '❌'} |",
        f"| Tool Success Rate | {scorecard.get('tool_success_rate', 0)*100:.1f}% | ≥70% | {'✅' if targets.get('tool_success_rate_met') else '❌'} |",
        f"",
        f"## Latency",
        f"",
        f"| Avg | Min | Max |",
        f"|-----|-----|-----|",
        f"| {scorecard.get('avg_latency_s', 0):.3f}s | {scorecard.get('min_latency_s', 0):.3f}s | {scorecard.get('max_latency_s', 0):.3f}s |",
        f"",
        f"## Tool Usage",
        f"",
        f"- Total Calls: **{scorecard.get('total_tool_calls', 0)}**",
        f"- Successes: **{scorecard.get('total_tool_successes', 0)}**",
        f"- Failures: **{scorecard.get('total_tool_failures', 0)}**",
        f"",
        f"## Per-Query Results",
        f"",
        f"| # | Query | Status | Latency | Steps |",
        f"|---|-------|--------|---------|-------|",
    ]
    status_icons = {"success": "✅", "cache_hit": "⚡", "failed": "❌", "pending": "⏳"}
    for q in scorecard.get("per_query", []):
        icon = status_icons.get(q["status"], "?")
        lines.append(
            f"| {q['index']} | {q['query'][:50]} | {icon} {q['status']} | {q['elapsed_s']:.2f}s | {q['step_count']} |"
        )

    all_pass = all(v for k, v in targets.items() if k.endswith("_met"))
    lines += [
        "",
        "## Verdict",
        "",
        "🏆 **ALL TARGETS MET**" if all_pass else "⚠️ **Some targets not met — review failures above.**",
    ]
    return "\n".join(lines)


def save_markdown_report(scorecard: Dict[str, Any], filepath: str):
    """Saves a Markdown benchmark report to a file."""
    md = generate_markdown_report(scorecard)
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Markdown report saved: {filepath}")
    return filepath


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ARA-1 Benchmark Dashboard")
    parser.add_argument("benchmark_file", nargs="?", help="Path to benchmark JSON. Defaults to most recent.")
    parser.add_argument("--markdown", "-m", help="Optional path to save a Markdown report.", default=None)
    args = parser.parse_args()

    filepath = args.benchmark_file or find_latest_benchmark()
    if not filepath or not os.path.exists(filepath):
        print("No benchmark file found. Run evaluate.py first.")
        sys.exit(1)

    print(f"Loading benchmark: {filepath}")
    scorecard = load_benchmark(filepath)

    # Try to load the previous benchmark for comparison
    all_files = find_all_benchmarks()
    prev_scorecard = None
    if len(all_files) >= 2:
        try:
            prev_path = next(f for f in all_files if f != filepath)
            prev_scorecard = load_benchmark(prev_path)
            print(f"Comparing against: {prev_path}")
        except StopIteration:
            pass

    render_console(scorecard, compare_to=prev_scorecard)

    if args.markdown:
        save_markdown_report(scorecard, args.markdown)


if __name__ == "__main__":
    main()
