"""
evaluation/metrics.py

Real-time metrics collection and aggregation for ARA-1 benchmark runs.

Tracks per-query and aggregate metrics:
  - Latency (wall-clock time per query)
  - Tool call counts and success/failure rates
  - Cache utilisation
  - Plan efficiency (steps completed vs planned)
  - Overall success rate

Usage:
    from evaluation.metrics import BenchmarkMetrics

    m = BenchmarkMetrics()
    m.start_query("What is MSFT Q3 revenue?")
    # ... run agent ...
    m.end_query(result_dict)
    m.print_scorecard()
    m.save("evaluation/benchmarks/run_YYYYMMDD.json")
"""

import json
import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryMetric:
    """
    Captures metrics for a single benchmark query.
    """
    def __init__(self, index: int, query: str):
        self.index = index
        self.query = query
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.elapsed_s: float = 0.0
        self.status: str = "pending"   # 'success' | 'failed' | 'cache_hit'
        self.from_cache: bool = False
        self.tool_calls: List[str] = []
        self.tool_success_count: int = 0
        self.tool_failure_count: int = 0
        self.step_count: int = 0
        self.error_message: str = ""
        self.report_length: int = 0

    def complete(self, result: Dict[str, Any]):
        """Finalises the query metric from the agent result dict."""
        self.end_time = time.time()
        self.elapsed_s = round(self.end_time - self.start_time, 3)
        self.from_cache = result.get("from_cache", False)

        if self.from_cache:
            self.status = "cache_hit"
        else:
            self.status = "success"

        calls = result.get("tool_calls_made", [])
        self.step_count = len(calls)
        self.tool_calls = [c.get("tool", "unknown") for c in calls]
        self.tool_success_count = sum(1 for c in calls if c.get("status") == "success")
        self.tool_failure_count = self.step_count - self.tool_success_count
        self.report_length = len(result.get("report", ""))

    def fail(self, error: str):
        """Marks the query as failed with an error message."""
        self.end_time = time.time()
        self.elapsed_s = round(self.end_time - self.start_time, 3)
        self.status = "failed"
        self.error_message = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "query": self.query,
            "status": self.status,
            "elapsed_s": self.elapsed_s,
            "from_cache": self.from_cache,
            "step_count": self.step_count,
            "tools_used": self.tool_calls,
            "tool_success_count": self.tool_success_count,
            "tool_failure_count": self.tool_failure_count,
            "report_length_chars": self.report_length,
            "error_message": self.error_message,
        }


class BenchmarkMetrics:
    """
    Aggregates per-query metrics over a full benchmark run.

    Example:
        metrics = BenchmarkMetrics(run_label="baseline-v1")
        for q in test_queries:
            metrics.start_query(q)
            try:
                result = agent.research(q)
                metrics.end_query(result)
            except Exception as e:
                metrics.fail_query(str(e))
        report = metrics.get_scorecard()
        metrics.save("evaluation/benchmarks/run.json")
    """

    def __init__(self, run_label: str = "benchmark"):
        self.run_label = run_label
        self.run_start: float = time.time()
        self.run_timestamp: str = datetime.utcnow().isoformat() + "Z"
        self.query_metrics: List[QueryMetric] = []
        self._active: Optional[QueryMetric] = None
        logger.info(f"BenchmarkMetrics started | Run: '{run_label}' | {self.run_timestamp}")

    # ------------------------------------------------------------------
    # Per-query lifecycle
    # ------------------------------------------------------------------
    def start_query(self, query: str) -> QueryMetric:
        """Opens a new per-query metric tracker. Call before running the agent."""
        idx = len(self.query_metrics) + 1
        qm = QueryMetric(index=idx, query=query)
        self.query_metrics.append(qm)
        self._active = qm
        logger.info(f"[Metrics] Query {idx} started: {query[:60]}")
        return qm

    def end_query(self, result: Dict[str, Any]):
        """Finalises the current query metric from the agent result dict."""
        if self._active is None:
            raise RuntimeError("end_query called without a matching start_query.")
        self._active.complete(result)
        logger.info(
            f"[Metrics] Query {self._active.index} complete | "
            f"Status: {self._active.status} | "
            f"Elapsed: {self._active.elapsed_s}s | "
            f"Steps: {self._active.step_count}"
        )
        self._active = None

    def fail_query(self, error: str):
        """Records the current query as failed."""
        if self._active is None:
            raise RuntimeError("fail_query called without a matching start_query.")
        self._active.fail(error)
        logger.error(f"[Metrics] Query {self._active.index} FAILED: {error}")
        self._active = None

    # ------------------------------------------------------------------
    # Aggregate scorecard
    # ------------------------------------------------------------------
    def get_scorecard(self) -> Dict[str, Any]:
        """Computes and returns the aggregate benchmark scorecard."""
        total = len(self.query_metrics)
        if total == 0:
            return {"run_label": self.run_label, "total_queries": 0, "message": "No queries recorded."}

        successes = sum(1 for q in self.query_metrics if q.status in ("success", "cache_hit"))
        failures = sum(1 for q in self.query_metrics if q.status == "failed")
        cache_hits = sum(1 for q in self.query_metrics if q.status == "cache_hit")

        latencies = [q.elapsed_s for q in self.query_metrics]
        total_tool_calls = sum(q.step_count for q in self.query_metrics)
        total_tool_success = sum(q.tool_success_count for q in self.query_metrics)
        total_tool_failure = sum(q.tool_failure_count for q in self.query_metrics)

        tool_success_rate = (
            round(total_tool_success / total_tool_calls, 4) if total_tool_calls > 0 else 0.0
        )
        avg_latency = round(sum(latencies) / len(latencies), 3) if latencies else 0.0
        max_latency = round(max(latencies), 3) if latencies else 0.0
        min_latency = round(min(latencies), 3) if latencies else 0.0

        cache_ratio = round(cache_hits / total, 4)
        success_rate = round(successes / total, 4)

        total_run_time = round(time.time() - self.run_start, 2)

        return {
            "run_label": self.run_label,
            "run_timestamp": self.run_timestamp,
            "total_run_time_s": total_run_time,
            "total_queries": total,
            "successful_queries": successes,
            "failed_queries": failures,
            "cache_hit_queries": cache_hits,
            "success_rate": success_rate,
            "cache_utilisation_ratio": cache_ratio,
            "avg_latency_s": avg_latency,
            "min_latency_s": min_latency,
            "max_latency_s": max_latency,
            "total_tool_calls": total_tool_calls,
            "total_tool_successes": total_tool_success,
            "total_tool_failures": total_tool_failure,
            "tool_success_rate": tool_success_rate,
            "targets": {
                "success_rate_target": 0.80,
                "success_rate_met": success_rate >= 0.80,
                "cache_ratio_target": 0.20,
                "cache_ratio_met": cache_ratio >= 0.20,
                "tool_success_rate_target": 0.70,
                "tool_success_rate_met": tool_success_rate >= 0.70,
            },
            "per_query": [q.to_dict() for q in self.query_metrics],
        }

    def print_scorecard(self):
        """Pretty-prints the scorecard to stdout."""
        sc = self.get_scorecard()
        print("\n" + "=" * 60)
        print(f"📊  ARA-1 BENCHMARK SCORECARD  |  Run: {sc['run_label']}")
        print("=" * 60)
        print(f"  Timestamp       : {sc.get('run_timestamp', 'N/A')}")
        print(f"  Total Run Time  : {sc.get('total_run_time_s', 0)}s")
        print(f"  Total Queries   : {sc['total_queries']}")
        print(f"  Successes       : {sc.get('successful_queries', 0)}")
        print(f"  Failures        : {sc.get('failed_queries', 0)}")
        print(f"  Cache Hits      : {sc.get('cache_hit_queries', 0)}")
        print("-" * 60)
        print(f"  Success Rate    : {sc.get('success_rate', 0)*100:.1f}%  "
              f"(target ≥80%  {'✅' if sc['targets']['success_rate_met'] else '❌'})")
        print(f"  Cache Ratio     : {sc.get('cache_utilisation_ratio', 0)*100:.1f}%  "
              f"(target ≥20%  {'✅' if sc['targets']['cache_ratio_met'] else '❌'})")
        print(f"  Tool Success    : {sc.get('tool_success_rate', 0)*100:.1f}%  "
              f"(target ≥70%  {'✅' if sc['targets']['tool_success_rate_met'] else '❌'})")
        print("-" * 60)
        print(f"  Avg Latency     : {sc.get('avg_latency_s', 0)}s")
        print(f"  Min/Max Latency : {sc.get('min_latency_s', 0)}s / {sc.get('max_latency_s', 0)}s")
        print(f"  Total Tool Calls: {sc.get('total_tool_calls', 0)}")
        print("=" * 60)

        print("\n  Per-Query Results:")
        for q in sc.get("per_query", []):
            status_icon = {"success": "✅", "cache_hit": "⚡", "failed": "❌", "pending": "⏳"}.get(q["status"], "?")
            print(f"    [{q['index']}] {status_icon} {q['query'][:50]:<50} | {q['elapsed_s']}s | steps={q['step_count']}")
        print()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self, filepath: str):
        """Saves the full scorecard JSON to a file."""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        sc = self.get_scorecard()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sc, f, indent=2)
        logger.info(f"Benchmark results saved to: {filepath}")
        return filepath


# ------------------------------------------------------------------
# Quick self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import random

    m = BenchmarkMetrics(run_label="self-test")
    queries = ["MSFT Q3 revenue?", "AAPL 10-K risk factors", "TSLA robotaxi news", "MSFT Q3 revenue?", "NVDA data center"]

    for q in queries:
        m.start_query(q)
        time.sleep(random.uniform(0.05, 0.2))  # Simulate latency
        fake_result = {
            "from_cache": "MSFT" in q and queries.index(q) > 0,
            "tool_calls_made": [
                {"tool": "financial_data_api", "status": "success"},
                {"tool": "sec_filing_search", "status": "success"},
            ],
            "report": "# Mock Report\n\nSome content here.",
        }
        m.end_query(fake_result)

    m.print_scorecard()
    m.save("evaluation/benchmarks/self_test_run.json")
    print("Self-test metrics saved.")
