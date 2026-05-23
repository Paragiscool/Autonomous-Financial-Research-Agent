"""
evaluation/__init__.py

Public exports for the evaluation package.
"""

from evaluation.metrics import BenchmarkMetrics, QueryMetric
from evaluation.dashboard import render_console, generate_markdown_report, save_markdown_report, load_benchmark, find_latest_benchmark

__all__ = [
    "BenchmarkMetrics",
    "QueryMetric",
    "render_console",
    "generate_markdown_report",
    "save_markdown_report",
    "load_benchmark",
    "find_latest_benchmark",
]
