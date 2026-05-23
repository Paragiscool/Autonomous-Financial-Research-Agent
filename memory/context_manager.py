"""
memory/context_manager.py

Manages the agent's active context window for a single research session.
Tracks:
  - The running conversation / message history
  - Token budget estimation (rough character-based)
  - Step-level observations for the current plan execution
"""

import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Rough token budget: ~4 chars per token, max context ~16k tokens for safety
MAX_CONTEXT_CHARS = 64_000


class ContextManager:
    """
    Short-term, in-session context manager.

    Responsibilities:
      - Maintains an ordered list of messages (planner / executor / synthesizer turns).
      - Provides a trimmed view of the context that fits within the token budget.
      - Tracks per-session metadata: session_id, query, start time, elapsed time.
    """

    def __init__(self, session_id: str, query: str):
        self.session_id = session_id
        self.query = query
        self.start_time: float = time.time()
        self.messages: List[Dict[str, Any]] = []
        self.step_observations: List[Dict[str, Any]] = []
        self._total_chars: int = 0

        logger.info(f"ContextManager initialised for session '{session_id}' | Query: {query[:60]}")

    # ------------------------------------------------------------------
    # Message tracking
    # ------------------------------------------------------------------
    def add_message(self, role: str, content: str, step_id: Optional[int] = None):
        """
        Appends a message to the context window.

        Args:
            role:    'planner' | 'executor' | 'synthesizer' | 'verifier' | 'user' | 'system'
            content: Raw text content of the message.
            step_id: Optional step number for executor messages.
        """
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "chars": len(content),
        }
        if step_id is not None:
            entry["step_id"] = step_id

        self.messages.append(entry)
        self._total_chars += len(content)

        # Auto-trim if we exceed budget
        if self._total_chars > MAX_CONTEXT_CHARS:
            self._trim_context()

        logger.debug(f"[Context] +{len(content)} chars ({role}) | Total: {self._total_chars} chars")

    def add_observation(self, step_id: int, tool: str, status: str, summary: str, elapsed_s: float = 0.0):
        """
        Stores a structured executor observation alongside the message log.

        Args:
            step_id:   The plan step number.
            tool:      Tool that was executed.
            status:    'success' | 'fallback_needed' | 'conflict_detected'
            summary:   Short textual summary of the result.
            elapsed_s: Wall-clock seconds the step took.
        """
        obs = {
            "step_id": step_id,
            "tool": tool,
            "status": status,
            "summary": summary,
            "elapsed_s": round(elapsed_s, 3),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.step_observations.append(obs)
        logger.info(f"[Observation] Step {step_id} | {tool} → {status} ({elapsed_s:.2f}s)")

    # ------------------------------------------------------------------
    # Context trimming / retrieval
    # ------------------------------------------------------------------
    def _trim_context(self):
        """
        Removes oldest messages (except the first system/user seed) until
        total chars fall back below the budget.
        """
        logger.warning(f"Context budget exceeded ({self._total_chars} chars). Trimming oldest messages…")
        # Always keep index 0 (system prompt / query)
        while len(self.messages) > 1 and self._total_chars > MAX_CONTEXT_CHARS:
            removed = self.messages.pop(1)
            self._total_chars -= removed["chars"]
        logger.info(f"Context trimmed to {self._total_chars} chars ({len(self.messages)} messages remaining).")

    def get_context_window(self, max_chars: int = MAX_CONTEXT_CHARS) -> str:
        """
        Returns a concatenated string of all messages in the context window,
        truncated to max_chars if necessary.
        """
        parts = []
        running = 0
        for msg in reversed(self.messages):  # Most recent first
            chunk = f"[{msg['role'].upper()}]: {msg['content']}\n"
            if running + len(chunk) > max_chars:
                break
            parts.insert(0, chunk)
            running += len(chunk)
        return "".join(parts)

    # ------------------------------------------------------------------
    # Session summary
    # ------------------------------------------------------------------
    def get_summary(self) -> Dict[str, Any]:
        """Returns a serialisable summary of the current session context."""
        elapsed = round(time.time() - self.start_time, 2)
        return {
            "session_id": self.session_id,
            "query": self.query,
            "elapsed_seconds": elapsed,
            "total_messages": len(self.messages),
            "total_chars_in_context": self._total_chars,
            "total_steps_observed": len(self.step_observations),
            "step_statuses": {
                "success": sum(1 for o in self.step_observations if o["status"] == "success"),
                "fallback_needed": sum(1 for o in self.step_observations if o["status"] == "fallback_needed"),
                "conflict_detected": sum(1 for o in self.step_observations if o["status"] == "conflict_detected"),
            },
        }

    def __repr__(self) -> str:
        return (
            f"ContextManager(session='{self.session_id}', "
            f"messages={len(self.messages)}, "
            f"chars={self._total_chars})"
        )


# ------------------------------------------------------------------
# Quick self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import json

    ctx = ContextManager(session_id="test-session-001", query="What is MSFT's Q3 revenue?")

    ctx.add_message("user", "What is MSFT's Q3 revenue?")
    ctx.add_message("planner", "Step 1: Call financial_data_api for MSFT income statement.")
    ctx.add_observation(step_id=1, tool="financial_data_api", status="success", summary="Fetched MSFT income statement.", elapsed_s=1.23)
    ctx.add_message("executor", "[Step 1] Tool returned quarterly income data for MSFT.", step_id=1)
    ctx.add_observation(step_id=2, tool="sec_filing_search", status="success", summary="Fetched 10-Q filing.", elapsed_s=2.11)

    print("\n=== Context Window (last 500 chars) ===")
    print(ctx.get_context_window(max_chars=500))

    print("\n=== Session Summary ===")
    print(json.dumps(ctx.get_summary(), indent=2))
