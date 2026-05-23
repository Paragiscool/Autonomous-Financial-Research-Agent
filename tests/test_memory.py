import os
import sys
import time
import logging
from dotenv import load_dotenv

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from agent.core import AutonomousResearchAgent
from agent.llm_wrapper import RobustLLM

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Test-Caching")

def run_cache_test():
    logger.info("Initializing Agent for caching test...")
    agent = AutonomousResearchAgent(dry_run=True, simulate_failures=False)
    query = "What is Microsoft's Q3 revenue?"
    ticker = "MSFT"
    
    # Clean up any existing cache for this test query to ensure a clean slate
    collection = agent.memory.collection
    try:
        # We find existing items with this ticker and delete them just for this test
        docs = collection.get(where={"ticker": ticker})
        if docs and docs["ids"]:
            collection.delete(ids=docs["ids"])
            logger.info(f"Cleaned up {len(docs['ids'])} existing MSFT records.")
    except Exception as e:
        logger.warning(f"Cleanup failed or skipped: {e}")

    logger.info("--- RUN 1: First Query (Cache Miss) ---")
    start_time = time.time()
    result1 = agent.research(query=query, ticker=ticker)
    report1 = result1["report"]
    duration1 = time.time() - start_time
    logger.info(f"Run 1 completed in {duration1:.2f} seconds.")
    
    logger.info("--- RUN 2: Same Query (Cache Hit) ---")
    start_time = time.time()
    result2 = agent.research(query=query, ticker=ticker)
    report2 = result2["report"]
    duration2 = time.time() - start_time
    logger.info(f"Run 2 completed in {duration2:.2f} seconds.")
    
    assert duration2 < 1.0, f"Expected cache hit to be < 1s, got {duration2:.2f}s"
    assert report1 == report2, "Reports from Run 1 and Run 2 should match exactly."
    logger.info("CACHE HIT SUCCESS: Instantly returned report!")

    logger.info("--- RUN 3: Expired Timestamp (Cache Bypass) ---")
    # Manually update the timestamp in ChromaDB to simulate a 3-day old report
    results = collection.get(where={"ticker": ticker})
    if results and results["ids"]:
        doc_id = results["ids"][0]
        old_metadata = results["metadatas"][0]
        # Set timestamp to 3 days ago
        old_metadata["timestamp"] = int(time.time()) - (3 * 86400)
        collection.update(
            ids=[doc_id],
            metadatas=[old_metadata]
        )
        logger.info(f"Manually expired the cache timestamp for document {doc_id}.")
        
    start_time = time.time()
    result3 = agent.research(query=query, ticker=ticker)
    report3 = result3["report"]
    duration3 = time.time() - start_time
    logger.info(f"Run 3 completed in {duration3:.2f} seconds.")
    
    assert duration3 > 1.0, f"Expected cache bypass to take > 1s, got {duration3:.2f}s"
    logger.info("CACHE BYPASS SUCCESS: Expired timestamp forced a fresh generation.")
    
    logger.info("All caching tests passed successfully!")

if __name__ == "__main__":
    run_cache_test()
