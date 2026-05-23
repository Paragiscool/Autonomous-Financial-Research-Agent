"""
memory/episodic.py

Episodic memory for ARA-1.

Stores discrete research "episodes" — each episode represents one complete
agent research session (query → findings → report). Episodes are persisted
as JSON lines in a local file so they survive across process restarts.

Key capabilities:
  - Append a new episode (store_episode)
  - Retrieve recent episodes filtered by ticker or query keyword (recall_episodes)
  - Summarise all past episodes for a given ticker (get_ticker_history)
  - Prune old episodes beyond a retention window (prune_old_episodes)
"""

import json
import os
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Default storage path — relative to project root
DEFAULT_STORE_PATH = "./episodic_memory.jsonl"

# Keep episodes for up to 30 days by default
DEFAULT_RETENTION_DAYS = 30


class EpisodicMemory:
    """
    File-backed episodic memory store.

    Each episode is a JSON object on a single line in the backing file.
    Schema:
        {
            "episode_id":    str,      # Unique ID (session ID typically)
            "query":         str,      # The original research query
            "ticker":        str,      # Primary ticker, or 'unknown'
            "timestamp_utc": str,      # ISO-8601 UTC timestamp
            "timestamp_unix":int,      # Unix epoch for fast range queries
            "tools_used":    [str],    # List of tool names called
            "step_count":    int,      # Total number of plan steps executed
            "success_count": int,      # Steps that completed with status=success
            "cache_hit":     bool,     # Was this served from the semantic cache?
            "elapsed_s":     float,    # Total wall-clock time in seconds
            "report_snippet":str,      # First 400 chars of the synthesised report
        }
    """

    def __init__(self, store_path: str = DEFAULT_STORE_PATH, retention_days: int = DEFAULT_RETENTION_DAYS):
        self.store_path = store_path
        self.retention_days = retention_days
        self._ensure_file()
        logger.info(f"EpisodicMemory initialised | Store: {self.store_path} | Retention: {retention_days} days")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_file(self):
        """Creates the backing file if it does not exist."""
        if not os.path.exists(self.store_path):
            open(self.store_path, "w", encoding="utf-8").close()
            logger.info(f"Created episodic memory store: {self.store_path}")

    def _read_all(self) -> List[Dict[str, Any]]:
        """Returns all episodes as a list of dicts."""
        episodes = []
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            episodes.append(json.loads(line))
                        except json.JSONDecodeError:
                            logger.warning(f"Skipping malformed episode line: {line[:60]}")
        except FileNotFoundError:
            pass
        return episodes

    def _write_all(self, episodes: List[Dict[str, Any]]):
        """Overwrites the backing file with the provided list of episodes."""
        with open(self.store_path, "w", encoding="utf-8") as f:
            for ep in episodes:
                f.write(json.dumps(ep) + "\n")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def store_episode(
        self,
        episode_id: str,
        query: str,
        ticker: str,
        tools_used: List[str],
        step_count: int,
        success_count: int,
        elapsed_s: float,
        report_snippet: str,
        cache_hit: bool = False,
    ) -> Dict[str, Any]:
        """
        Persists a new research episode to the backing store.

        Returns the episode dict that was stored.
        """
        now = datetime.utcnow()
        episode = {
            "episode_id": episode_id,
            "query": query,
            "ticker": ticker,
            "timestamp_utc": now.isoformat() + "Z",
            "timestamp_unix": int(time.time()),
            "tools_used": tools_used,
            "step_count": step_count,
            "success_count": success_count,
            "cache_hit": cache_hit,
            "elapsed_s": round(elapsed_s, 3),
            "report_snippet": report_snippet[:400],
        }
        with open(self.store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(episode) + "\n")
        logger.info(f"Episode stored: {episode_id} | Ticker: {ticker} | {step_count} steps | {elapsed_s:.2f}s")
        return episode

    def recall_episodes(
        self,
        ticker: Optional[str] = None,
        keyword: Optional[str] = None,
        last_n: int = 10,
        since_days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recent episodes matching optional filters.

        Args:
            ticker:    If set, only return episodes for this ticker symbol.
            keyword:   If set, only return episodes whose query contains this keyword (case-insensitive).
            last_n:    Maximum number of episodes to return (most recent first).
            since_days: Only return episodes from the last N days.

        Returns:
            List of matching episode dicts, sorted newest-first.
        """
        cutoff_unix = int(time.time()) - (since_days * 86400)
        all_eps = self._read_all()

        # Filter
        filtered = []
        for ep in all_eps:
            if ep.get("timestamp_unix", 0) < cutoff_unix:
                continue
            if ticker and ep.get("ticker", "").upper() != ticker.upper():
                continue
            if keyword and keyword.lower() not in ep.get("query", "").lower():
                continue
            filtered.append(ep)

        # Sort newest first and cap
        filtered.sort(key=lambda e: e.get("timestamp_unix", 0), reverse=True)
        return filtered[:last_n]

    def get_ticker_history(self, ticker: str) -> Dict[str, Any]:
        """
        Summarises all past episodes for a given ticker.

        Returns a dict with aggregate stats useful for the agent's context.
        """
        episodes = self.recall_episodes(ticker=ticker, last_n=100, since_days=self.retention_days)
        if not episodes:
            return {"ticker": ticker, "total_episodes": 0, "message": "No prior research found."}

        total_steps = sum(e.get("step_count", 0) for e in episodes)
        total_success = sum(e.get("success_count", 0) for e in episodes)
        avg_elapsed = round(sum(e.get("elapsed_s", 0) for e in episodes) / len(episodes), 2)
        cache_hits = sum(1 for e in episodes if e.get("cache_hit", False))

        return {
            "ticker": ticker,
            "total_episodes": len(episodes),
            "total_steps": total_steps,
            "total_successful_steps": total_success,
            "cache_hit_episodes": cache_hits,
            "average_elapsed_s": avg_elapsed,
            "most_recent_query": episodes[0].get("query", ""),
            "most_recent_timestamp": episodes[0].get("timestamp_utc", ""),
            "tools_ever_used": list({t for ep in episodes for t in ep.get("tools_used", [])}),
        }

    def prune_old_episodes(self) -> int:
        """
        Removes episodes older than the configured retention window.

        Returns the number of episodes pruned.
        """
        cutoff_unix = int(time.time()) - (self.retention_days * 86400)
        all_eps = self._read_all()
        kept = [ep for ep in all_eps if ep.get("timestamp_unix", 0) >= cutoff_unix]
        pruned = len(all_eps) - len(kept)
        if pruned:
            self._write_all(kept)
            logger.info(f"Pruned {pruned} old episode(s) older than {self.retention_days} days.")
        else:
            logger.info("No episodes needed pruning.")
        return pruned

    def count(self) -> int:
        """Returns the total number of stored episodes."""
        return len(self._read_all())

    def __repr__(self) -> str:
        return f"EpisodicMemory(store='{self.store_path}', episodes={self.count()})"


# ------------------------------------------------------------------
# Quick self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uuid
    import tempfile

    # Use a temp file so the test doesn't pollute the real store
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp:
        tmp_path = tmp.name

    em = EpisodicMemory(store_path=tmp_path, retention_days=30)

    # Store 3 fake episodes
    for i, ticker in enumerate(["MSFT", "AAPL", "MSFT"], start=1):
        em.store_episode(
            episode_id=f"ep-{uuid.uuid4().hex[:6]}",
            query=f"Test query #{i} for {ticker}",
            ticker=ticker,
            tools_used=["financial_data_api", "sec_filing_search"],
            step_count=3,
            success_count=3,
            elapsed_s=4.5 + i,
            report_snippet=f"Mock report snippet for {ticker} research #{i}.",
            cache_hit=(i == 3),
        )

    print(f"\nTotal stored: {em.count()}")
    print("\n=== MSFT History ===")
    print(json.dumps(em.get_ticker_history("MSFT"), indent=2))
    print("\n=== Recalled Episodes (MSFT) ===")
    for ep in em.recall_episodes(ticker="MSFT"):
        print(f"  [{ep['timestamp_utc']}] {ep['query']} | {ep['elapsed_s']}s | cache={ep['cache_hit']}")

    # Cleanup
    os.remove(tmp_path)
    print("\nSelf-test complete.")
