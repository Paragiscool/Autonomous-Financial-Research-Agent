"""
agent/core.py
The main ARA-1 agent class implementing the Plan-and-Execute cognitive loop.

Flow:
  Query → [Memory Check] → Planner → Plan
       → Executor (step-by-step) → Findings
       → Synthesizer → Final Report
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Optional

# Ensure project root is on path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.prompts import PLANNER_SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT, SYNTHESIZER_PROMPT
from agent.parser import parse_plan, parse_executor_response
from tool_registry import ToolRegistry
from memory.vector_store import LongTermMemory

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ARA-1")

# Max iterations to prevent infinite loops
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 15))


class AutonomousResearchAgent:
    """
    ARA-1: The core Plan-and-Execute research agent.
    
    Architecture:
    - Planner:     Generates a structured multi-step research plan from the query.
    - Executor:    Executes each plan step using the tool registry; handles fallbacks.
    - Synthesizer: Aggregates all findings into a final research report.
    """

    def __init__(self, llm=None, dry_run: bool = True):
        """
        Args:
            llm:     A RobustLLM instance. If None, the agent runs in dry_run mode.
            dry_run: If True, skips real LLM calls and uses mock responses (for offline testing).
        """
        self.llm = llm
        self.dry_run = dry_run
        self.session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:6]}"
        self.registry = ToolRegistry(schemas_dir="tools/schemas")
        self.memory = LongTermMemory(db_path="./chroma_db")

        logger.info(f"ARA-1 initialized. Session: {self.session_id} | Dry Run: {self.dry_run}")

    # ------------------------------------------------------------------
    # PHASE 0: Pre-flight memory check
    # ------------------------------------------------------------------
    def _check_long_term_memory(self, query: str, ticker: Optional[str] = None) -> Optional[str]:
        """
        Checks if the agent has already researched this topic recently.
        Returns a summary of past findings if relevant data exists.
        """
        results = self.memory.search_memory(query, ticker_filter=ticker, n_results=2)
        docs = results.get("documents", [[]])[0]
        if docs:
            logger.info(f"Long-term memory hit: {len(docs)} relevant past finding(s) found.")
            return "\n\n".join(docs)
        logger.info("Long-term memory: No prior research found for this query.")
        return None

    # ------------------------------------------------------------------
    # PHASE 1: Planner
    # ------------------------------------------------------------------
    def _run_planner(self, query: str) -> Optional[dict]:
        """
        Calls the Planner LLM to generate a structured research plan.
        In dry_run mode, returns a hardcoded mock plan.
        """
        if self.dry_run:
            # Dynamically build mock plan from the stored ticker context
            t = (getattr(self, '_current_ticker', None) or "MSFT").upper()
            logger.info(f"[DRY RUN] Using mock plan for: {query}")
            return {
                "query_summary": f"Research query: {query}",
                "steps": [
                    {
                        "step_id": 1,
                        "tool": "company_profile",
                        "arguments": {"ticker": t},
                        "purpose": "Retrieve basic company information.",
                        "depends_on": []
                    },
                    {
                        "step_id": 2,
                        "tool": "financial_data_api",
                        "arguments": {"ticker": t, "statement_type": "income_statement", "period": "annual"},
                        "purpose": "Get revenue and profitability data.",
                        "depends_on": [1]
                    },
                    {
                        "step_id": 3,
                        "tool": "sec_filing_search",
                        "arguments": {"ticker": t, "filing_type": "10-K"},
                        "purpose": "Retrieve risk factors from the most recent 10-K.",
                        "depends_on": [1]
                    }
                ],
                "synthesis_goal": "A structured research report covering business overview, financials, and key risks."
            }

        # Real LLM call
        tool_registry_str = json.dumps(list(self.registry.schemas.values()), indent=2)
        prompt = PLANNER_SYSTEM_PROMPT.format(tool_registry=tool_registry_str)
        prompt += f"\n\nResearch Query: {query}\n\nGenerate the research plan as JSON:"

        logger.info("Calling Planner LLM...")
        raw_response = self.llm.generate(prompt)
        plan = parse_plan(raw_response)

        if not plan:
            logger.error("Planner failed to produce a valid plan.")
        return plan

    # ------------------------------------------------------------------
    # PHASE 2: Executor
    # ------------------------------------------------------------------
    def _execute_step(self, step: dict, findings: list) -> dict:
        """
        Executes a single plan step using the tool registry.
        Returns a structured observation.
        """
        tool_name = step["tool"]
        arguments = step["arguments"]
        step_id = step["step_id"]

        logger.info(f"Step {step_id}: Calling tool '{tool_name}' with args {arguments}")
        tool_result = self.registry.execute_tool(tool_name, arguments)
        logger.info(f"Step {step_id}: Tool returned {len(str(tool_result))} characters.")

        # In dry_run mode, skip the Executor LLM and auto-mark as success
        if self.dry_run:
            return {
                "step_id": step_id,
                "status": "success",
                "summary": f"[DRY RUN] Tool '{tool_name}' returned data successfully.",
                "raw_result": tool_result,
                "revise_plan": False,
                "revision_note": ""
            }

        # Real LLM call to interpret the observation
        prompt = f"""{EXECUTOR_SYSTEM_PROMPT}

Step executed: {json.dumps(step)}
Tool result:
{tool_result}

Previous findings summary:
{chr(10).join([f['summary'] for f in findings]) if findings else 'None yet.'}

Respond in JSON:"""

        raw_response = self.llm.generate(prompt)
        observation = parse_executor_response(raw_response)

        if not observation:
            logger.warning(f"Step {step_id}: Failed to parse executor response. Defaulting to success.")
            observation = {"step_id": step_id, "status": "success", "summary": str(tool_result)[:300],
                           "revise_plan": False, "revision_note": ""}

        observation["raw_result"] = tool_result
        return observation

    # ------------------------------------------------------------------
    # PHASE 3: Synthesizer
    # ------------------------------------------------------------------
    def _synthesize(self, query: str, findings: list) -> str:
        """
        Produces the final research report from all accumulated findings.
        """
        findings_text = "\n\n---\n\n".join(
            [f"Step {f['step_id']} ({f.get('tool', 'N/A')}): {f['raw_result']}" for f in findings]
        )

        if self.dry_run:
            logger.info("[DRY RUN] Generating mock synthesis report.")
            return (
                f"# Research Report: {query}\n\n"
                f"**Session:** {self.session_id}\n\n"
                f"## Executive Summary\n"
                f"[DRY RUN] This is a mock report generated without a live LLM.\n\n"
                f"## Findings Summary ({len(findings)} steps completed)\n"
                + "\n".join([f"- **Step {f['step_id']}**: {f['summary']}" for f in findings])
                + f"\n\n## Raw Data\n```\n{findings_text[:1000]}\n```"
            )

        prompt = SYNTHESIZER_PROMPT.format(findings=findings_text, query=query)
        logger.info("Calling Synthesizer LLM...")
        return self.llm.generate(prompt)

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------
    def research(self, query: str, ticker: Optional[str] = None) -> str:
        """
        Main research method. Runs the full Plan-and-Execute loop.
        
        Args:
            query:  The research question (e.g., "Generate a profile for Apple Inc.")
            ticker: Optional ticker symbol for memory filtering.
        
        Returns:
            A formatted investment research report as a string.
        """
        logger.info(f"=== ARA-1 Research Session Started: {self.session_id} ===")
        logger.info(f"Query: {query}")
        self._current_ticker = ticker  # make ticker available to _run_planner

        # Phase 0: Check long-term memory
        prior_knowledge = self._check_long_term_memory(query, ticker)
        if prior_knowledge:
            logger.info("Using prior knowledge from memory (skipping some tool calls).")

        # Phase 1: Generate Plan
        plan = self._run_planner(query)
        if not plan:
            return "ERROR: Agent failed to generate a research plan. Please try again."

        logger.info(f"Plan generated: {len(plan['steps'])} steps.")

        # Phase 2: Execute Plan with dependency-aware ordering
        findings = []
        completed_step_ids: set = set()

        # Build execution order respecting depends_on (topological sort)
        remaining = list(plan["steps"])
        iteration_count = 0

        while remaining:
            iteration_count += 1
            if iteration_count > MAX_ITERATIONS:
                logger.warning(f"Hit MAX_ITERATIONS ({MAX_ITERATIONS}). Stopping execution.")
                break

            # Find all steps whose dependencies are satisfied
            ready = [s for s in remaining if all(dep in completed_step_ids for dep in s.get("depends_on", []))]

            if not ready:
                logger.error("Dependency deadlock: no steps are runnable. Breaking.")
                break

            # Execute the first ready step
            step = ready[0]
            remaining.remove(step)

            observation = self._execute_step(step, findings)
            observation["tool"] = step["tool"]
            findings.append(observation)
            completed_step_ids.add(step["step_id"])

            if observation.get("status") == "conflict_detected":
                logger.warning(f"Step {step['step_id']}: Data conflict detected! Flagging for synthesis.")

            if observation.get("revise_plan"):
                logger.info(f"Step {step['step_id']}: Plan revision requested — {observation['revision_note']}")
                # In a full implementation, re-run the planner with context here.

        # Phase 3: Synthesize Report
        logger.info(f"All {len(findings)} steps complete. Running synthesis...")
        report = self._synthesize(query, findings)

        # Store key findings in long-term memory
        if ticker:
            self.memory.store_finding(
                doc_id=f"{ticker.lower()}-{self.session_id}",
                content=report[:2000],  # Store the first 2000 chars of the report
                metadata={
                    "ticker": ticker,
                    "source_type": "agent_report",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "confidence": 0.85,
                    "researcher_session": self.session_id,
                    "verified": False
                }
            )

        logger.info("=== Research Complete ===")
        return report


# ------------------------------------------------------------------
# Quick Test: Challenge 1 - Microsoft Company Profile (Dry Run)
# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = AutonomousResearchAgent(dry_run=True)
    report = agent.research(
        query="Generate a company profile for Microsoft Corporation.",
        ticker="MSFT"
    )
    print("\n" + "="*60)
    print(report)
    print("="*60)
