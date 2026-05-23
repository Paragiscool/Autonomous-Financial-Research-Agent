import time
import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from agent.core import AutonomousResearchAgent

def run_benchmark():
    agent = AutonomousResearchAgent(simulate_failures=False) # Keep chaos off for baseline metrics
    
    # 5 Diverse Queries targeting different tools (SEC, Web, yfinance)
    test_queries = [
        "What is Microsoft's (MSFT) Q3 revenue?", # Should hit yfinance
        "Summarize the risk factors from Apple's (AAPL) latest 10-K.", # Should hit SEC
        "What is the latest market sentiment regarding Tesla's (TSLA) robotaxi?", # Should hit News/Sentiment
        "What is Microsoft's (MSFT) Q3 revenue?", # REPEAT: Should trigger a 100% Cache Hit
        "Compare NVIDIA's (NVDA) data center growth with their latest news announcements." # Complex: Multi-tool
    ]
    
    metrics = {
        "total_queries": len(test_queries),
        "successful_runs": 0,
        "total_tool_calls": 0,
        "cache_hits": 0,
        "total_time_seconds": 0
    }

    print("\n" + "="*50)
    print("🚀 INITIATING ARA-1 QUANTITATIVE BENCHMARK")
    print("="*50 + "\n")

    start_benchmark = time.time()

    for i, query in enumerate(test_queries, 1):
        print(f"--- Test {i}/{len(test_queries)}: {query[:40]}... ---")
        
        start_q = time.time()
        
        try:
            # We now parse the dictionary output that we just upgraded core.py to return!
            result = agent.research(query) 
            
            elapsed = round(time.time() - start_q, 2)
            print(f"✅ Success ({elapsed}s)")
            
            metrics["successful_runs"] += 1
            
            if result.get("from_cache"):
                metrics["cache_hits"] += 1
                print("   -> ⚡ Cache Hit")
            else:
                tool_calls = result.get("tool_calls_made", [])
                metrics["total_tool_calls"] += len(tool_calls)
                print(f"   -> 🛠️ Tool Calls: {len(tool_calls)}")
                
        except Exception as e:
            print(f"❌ Failed: {e}")
            
        print("-" * 50)

    metrics["total_time_seconds"] = round(time.time() - start_benchmark, 2)
    
    # Calculate the final ratios
    tool_efficiency = "N/A" if metrics["total_tool_calls"] == 0 else f">70% target pending manual tool review" 
    cache_ratio = round(metrics["cache_hits"] / metrics["total_queries"], 2)

    print("\n" + "="*50)
    print("📊 ARA-1 FINAL SCORECARD")
    print("="*50)
    print(json.dumps(metrics, indent=2))
    print(f"Memory Utilization (Cache Ratio): {cache_ratio} (Target: >= 0.20)")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_benchmark()
