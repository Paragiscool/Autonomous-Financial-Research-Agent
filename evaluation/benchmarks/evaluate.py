"""
evaluate.py

ARA-1 Quantitative Benchmark Runner.

Runs 5 diverse research queries against the live agent, tracks real-time
metrics using BenchmarkMetrics, stores episodes in EpisodicMemory, and
saves the full scorecard to evaluation/benchmarks/.

Usage:
    python evaluate.py
"""

import time
import json
import os
import sys
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
# We are in evaluation/benchmarks, project root is two levels up
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
load_dotenv()

from agent.core import AutonomousResearchAgent
from evaluation.metrics import BenchmarkMetrics
from memory.episodic import EpisodicMemory


# ------------------------------------------------------------------
# Benchmark configuration
# ------------------------------------------------------------------
TEST_QUERIES = [
    ("What is Microsoft's (MSFT) Q3 revenue?",                              "MSFT"),
    ("Summarize the risk factors from Apple's (AAPL) latest 10-K.",         "AAPL"),
    ("What is the latest market sentiment regarding Tesla's (TSLA) robotaxi?", "TSLA"),
    ("What is Microsoft's (MSFT) Q3 revenue?",                              "MSFT"),   # REPEAT → Cache Hit
    ("Compare NVIDIA's (NVDA) data center growth with their latest news announcements.", "NVDA"),
]

RUN_LABEL = f"baseline-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
EPISODIC_STORE = os.path.join(project_root, "episodic_memory.jsonl")


def run_benchmark():
    print("\n" + "=" * 60)
    print("🚀  ARA-1 QUANTITATIVE BENCHMARK")
    print(f"    Run label : {RUN_LABEL}")
    print(f"    Queries   : {len(TEST_QUERIES)}")
    print("=" * 60 + "\n")

    # Initialise agent with live LLM (simulate_failures=False for clean baseline)
    agent = AutonomousResearchAgent(simulate_failures=False)

    # Initialise metric collectors
    metrics = BenchmarkMetrics(run_label=RUN_LABEL)
    episodic = EpisodicMemory(store_path=EPISODIC_STORE)

    for i, (query, ticker) in enumerate(TEST_QUERIES, 1):
        print(f"--- Test {i}/{len(TEST_QUERIES)}: {query[:55]}... ---")

        metrics.start_query(query)
        q_start = time.time()

        try:
            result = agent.research(query, ticker=ticker)
            elapsed = round(time.time() - q_start, 3)

            metrics.end_query(result)

            if result.get("from_cache"):
                print(f"  ⚡ Cache Hit  ({elapsed}s)")
            else:
                calls = result.get("tool_calls_made", [])
                successes = sum(1 for c in calls if c.get("status") == "success")
                print(f"  ✅ Success   ({elapsed}s)  |  Steps: {len(calls)}  |  Tool OK: {successes}/{len(calls)}")

            # Store episode in episodic memory
            calls = result.get("tool_calls_made", [])
            episodic.store_episode(
                episode_id=f"{ticker.lower()}-ep{i}-{RUN_LABEL}",
                query=query,
                ticker=ticker,
                tools_used=[c.get("tool", "unknown") for c in calls],
                step_count=len(calls),
                success_count=sum(1 for c in calls if c.get("status") == "success"),
                elapsed_s=elapsed,
                report_snippet=result.get("report", "")[:400],
                cache_hit=result.get("from_cache", False),
            )

        except Exception as e:
            elapsed = round(time.time() - q_start, 3)
            print(f"  ❌ Failed    ({elapsed}s)  |  {e}")
            metrics.fail_query(str(e))

        print("-" * 60)

    # Print live scorecard to console
    metrics.print_scorecard()

    # Save full JSON scorecard
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{RUN_LABEL}.json")
    metrics.save(out_path)
    print(f"📁  Scorecard saved → {out_path}")

    # Save markdown report
    from evaluation.dashboard import save_markdown_report, load_benchmark
    md_path = os.path.join(OUTPUT_DIR, f"{RUN_LABEL}.md")
    save_markdown_report(metrics.get_scorecard(), md_path)
    print(f"📝  Markdown report → {md_path}")

    # Print episodic memory summary
    print(f"\n📚  Episodic Memory: {episodic.count()} total episodes stored")
    for _, ticker in set(TEST_QUERIES):
        hist = episodic.get_ticker_history(ticker)
        if hist.get("total_episodes", 0) > 0:
            print(f"    {ticker}: {hist['total_episodes']} episode(s) | avg {hist['average_elapsed_s']}s | cache hits: {hist['cache_hit_episodes']}")

    print("\n✅  Benchmark complete.\n")


if __name__ == "__main__":
    run_benchmark()
