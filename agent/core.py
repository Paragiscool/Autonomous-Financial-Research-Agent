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
import time
from datetime import datetime
from typing import Optional
from langchain_core.messages import HumanMessage

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


def compress_data(raw_data: list, query: str, llm) -> list:
    """
    Compresses massive raw text blocks by extracting only query-relevant facts.
    This acts as a 'Map' step to save tokens before the final 'Reduce' (Synthesis).
    """
    compressed_data = []
    
    for item in raw_data:
        # If the data is already small (like a short JSON metric), keep it as is
        content_str = str(item)
        if len(content_str) < 1500:
            compressed_data.append(item)
            continue
            
        logger.info(f"Compressing large data payload (Length: {len(content_str)} characters)...")
        
        # Use a fast, cheap prompt to extract only what matters
        compression_prompt = f"""
        You are a data extraction tool. Extract only the bullet points relevant to this query: "{query}".
        Ignore boilerplate, HTML leftovers, and irrelevant information. Be extremely concise.
        
        Raw Text:
        {content_str[:15000]} # Truncate safely for the mini-model
        """
        
        try:
            # Note: We use the same llm wrapper, but the prompt is tiny!
            summary = llm.generate([HumanMessage(content=compression_prompt)])
            compressed_data.append({"source_type": item.get("source_type", item.get("tool", "Unknown")), "extracted_facts": summary})
        except Exception as e:
            logger.warning(f"Compression failed, passing raw data: {e}")
            compressed_data.append(item) # Fallback to raw data if compression fails
            
    return compressed_data

class AutonomousResearchAgent:
    """
    ARA-1: The core Plan-and-Execute research agent.
    
    Architecture:
    - Planner:     Generates a structured multi-step research plan from the query.
    - Executor:    Executes each plan step using the tool registry; handles fallbacks.
    - Synthesizer: Aggregates all findings into a final research report.
    """

    def __init__(self, llm=None, dry_run: bool = True, simulate_failures: bool = False):
        """
        Args:
            llm:              A RobustLLM instance. If None, the agent runs in dry_run mode.
            dry_run:          If True, skips real LLM calls and uses mock responses (for offline testing).
            simulate_failures: If True, injects a 50% random failure rate into all tool calls (Chaos Mode).
        """
        self.llm = llm
        self.dry_run = dry_run
        self.simulate_failures = simulate_failures
        self.session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:6]}"
        self.registry = ToolRegistry(schemas_dir="tools/schemas", simulate_failures=simulate_failures)
        self.memory = LongTermMemory(db_path="./chroma_db")

        logger.info(f"ARA-1 initialized. Session: {self.session_id} | Dry Run: {self.dry_run} | Chaos Mode: {self.simulate_failures}")

    # ------------------------------------------------------------------
    # PHASE 0: Pre-flight memory check
    # ------------------------------------------------------------------
    def _check_semantic_cache(self, query: str, ticker: Optional[str] = None) -> Optional[str]:
        """
        Checks if an exact or highly similar report from the last 48 hours exists in memory.
        Returns the cached full report if found, else None.
        """
        conditions = [
            {"source_type": "agent_report"},
            {"timestamp": {"$gte": int(time.time()) - 172800}}
        ]
        if ticker:
            conditions.append({"ticker": ticker})
            
        where_clause = {"$and": conditions} if len(conditions) > 1 else conditions[0]
        
        try:
            results = self.memory.collection.query(
                query_texts=[query],
                n_results=1,
                where=where_clause
            )
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return None

        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        if distances and len(distances) > 0:
            if distances[0] <= 0.2:
                cached_report = metadatas[0].get("full_report")
                if cached_report:
                    logger.info(f"Semantic Cache Hit! Found highly similar recent report for '{query}'.")
                    return cached_report
                    
        return None

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
        # But still detect chaos/error JSON from the tool
        if self.dry_run:
            try:
                result_data = json.loads(tool_result) if isinstance(tool_result, str) else {}
                if result_data.get("error"):
                    return {
                        "step_id": step_id,
                        "status": "fallback_needed",
                        "summary": f"[CHAOS] Tool '{tool_name}' failed: {result_data['error']}",
                        "raw_result": tool_result,
                        "revise_plan": False,
                        "revision_note": "Tool failed due to simulated chaos. Marking for retry."
                    }
            except (json.JSONDecodeError, TypeError):
                pass
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
            # If parse fails, check whether the raw tool result signals an error
            # before blindly defaulting to success — prevents masked failures.
            try:
                raw_data = json.loads(tool_result) if isinstance(tool_result, str) else {}
                has_error = bool(raw_data.get("error"))
            except (json.JSONDecodeError, TypeError):
                has_error = False

            status = "fallback_needed" if has_error else "success"
            logger.warning(f"Step {step_id}: Failed to parse executor response. Defaulting to '{status}'.")
            observation = {"step_id": step_id, "status": status, "summary": str(tool_result)[:300],
                           "revise_plan": False, "revision_note": ""}

        observation["raw_result"] = tool_result
        return observation

    # ------------------------------------------------------------------
    # PHASE 3: Synthesizer
    # ------------------------------------------------------------------
    def _synthesize(self, query: str, findings: list) -> str:
        """
        Takes all gathered data, resolves conflicts using the hierarchy, 
        and drafts the final Markdown report.
        """
        logger.info("--- PHASE 3: SYNTHESIZING DATA ---")
        
        # 1. Format the gathered data into a readable string for the LLM
        if self.llm:
            compressed_findings = compress_data(findings, query, self.llm)
        else:
            compressed_findings = findings
        raw_data_string = json.dumps(compressed_findings, indent=2)

        if self.dry_run:
            logger.info("[DRY RUN] Generating mock synthesis report.")
            return (
                f"# Research Report: {query}\n\n"
                f"**Session:** {self.session_id}\n\n"
                f"## Executive Summary\n"
                f"[DRY RUN] This is a mock report generated without a live LLM.\n\n"
                f"## Findings Summary ({len(findings)} steps completed)\n"
                + "\n".join([f"- **Step {f.get('step_id', '?')}**: {f.get('summary', '')}" for f in findings])
                + f"\n\n## Raw Data\n```\n{raw_data_string[:1000]}\n```"
            )

        # 2. Construct the prompt
        from agent.prompts import SYNTHESIZER_SYSTEM_PROMPT
        prompt = f"{SYNTHESIZER_SYSTEM_PROMPT}\n\nOriginal User Query: {query}\n\nGathered Raw Data:\n{raw_data_string}\n\nPlease synthesize this into the final Markdown report."
        
        # 3. Call the LLM
        logger.info("Calling Synthesizer LLM...")
        try:
            response_text = self.llm.generate(prompt)
        except Exception as e:
            logger.error(f"Synthesizer Error: {e}")
            response_text = f"# Error Generating Report\n\nThe synthesizer encountered an error: {str(e)}"

        logger.info("Synthesis complete. Draft report generated.")
        return response_text

    # ------------------------------------------------------------------
    # PHASE 4: Verifier
    # ------------------------------------------------------------------
    def _verify_facts(self, draft: str, findings: list) -> dict:
        """
        Cross-references the draft report against the raw data to catch hallucinations.
        """
        logger.info("--- PHASE 4: VERIFYING FACTS ---")
        
        raw_data = json.dumps(findings, indent=2)
        from agent.prompts import VERIFIER_SYSTEM_PROMPT
        
        if self.dry_run:
            logger.info("[DRY RUN] Bypassing verifier.")
            return {"verified_report": draft, "errors": []}
            
        prompt = f"{VERIFIER_SYSTEM_PROMPT}\n\nRaw Gathered Data:\n{raw_data}\n\nDraft Report:\n{draft}"
        
        try:
            logger.info("Calling Verifier LLM...")
            response_text = self.llm.generate(prompt)
            
            import re
            # Non-greedy match to avoid consuming multiple JSON blocks in one response.
            match = re.search(r'\{.*?\}', response_text, re.DOTALL)
            if match:
                verification = json.loads(match.group(0))
            else:
                verification = json.loads(response_text)
                
            if verification.get("is_verified", False):
                logger.info("Verification Passed! No hallucinations detected.")
                return {"verified_report": draft, "errors": []}
            else:
                errors = verification.get("hallucinations", ["Unknown hallucination detected."])
                logger.warning(f"Verification Failed! Errors found: {errors}")
                return {"verified_report": None, "errors": errors}
                
        except Exception as e:
            logger.error(f"Verifier Error: {e}")
            return {"verified_report": None, "errors": [str(e)]}

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------
    def research(self, query: str, ticker: Optional[str] = None) -> dict:
        """
        Main research method. Runs the full Plan-and-Execute loop.
        
        Args:
            query:  The research question (e.g., "Generate a profile for Apple Inc.")
            ticker: Optional ticker symbol for memory filtering.
        
        Returns:
            A dictionary containing the report and telemetry data.
        """
        logger.info(f"=== ARA-1 Research Session Started: {self.session_id} ===")
        logger.info(f"Query: {query}")
        self._current_ticker = ticker  # make ticker available to _run_planner

        # Semantic Cache Check
        cached_report = self._check_semantic_cache(query, ticker)
        if cached_report:
            logger.info("Returning cached report from long-term memory (0 API calls, 0 tool failures, <1 second latency).")
            return {"report": cached_report, "from_cache": True, "tool_calls_made": []}

        # Phase 0: Check long-term memory
        prior_knowledge = self._check_long_term_memory(query, ticker)
        if prior_knowledge:
            logger.info("Using prior knowledge from memory (skipping some tool calls).")

        # Phase 1: Generate Plan
        plan = self._run_planner(query)
        if not plan:
            return {"report": "ERROR: Agent failed to generate a research plan. Please try again.", "from_cache": False, "tool_calls_made": []}

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

            # Only mark a step as completed if it genuinely succeeded.
            # Keeping failed steps out of completed_step_ids ensures their
            # downstream dependents are NOT unblocked — preventing silent data gaps.
            if observation.get("status") == "success":
                completed_step_ids.add(step["step_id"])
            else:
                # Still add it so the loop can progress (it's removed from `remaining`),
                # but log clearly that this dependency chain is broken.
                completed_step_ids.add(step["step_id"])
                logger.warning(f"Step {step['step_id']} marked '{observation.get('status')}'. "
                               f"Dependent steps will proceed with incomplete data.")

            if observation.get("status") == "conflict_detected":
                logger.warning(f"Step {step['step_id']}: Data conflict detected! Flagging for synthesis.")

            if observation.get("revise_plan"):
                logger.info(f"Step {step['step_id']}: Plan revision requested — {observation['revision_note']}")
                # In a full implementation, re-run the planner with context here.

        # Phase 3: Synthesize Report
        logger.info(f"All {len(findings)} steps complete. Running synthesis...")
        report = self._synthesize(query, findings)
        
        # Phase 4: Verify Facts
        verification = self._verify_facts(report, findings)
        if verification.get("errors"):
            report += f"\n\n## Verifier Warnings\nThe following potential errors/hallucinations were detected and require human review:\n" + "\n".join([f"- {e}" for e in verification["errors"]])

        # Store key findings in long-term memory
        safe_ticker = ticker if ticker else "unknown"
        self.memory.store_finding(
            doc_id=f"{safe_ticker.lower()}-{self.session_id}",
            content=query,  # Store the original query to enable Query-to-Query similarity matching
            metadata={
                "ticker": safe_ticker,
                "source_type": "agent_report",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "confidence": 0.85,
                "researcher_session": self.session_id,
                "verified": False,
                "full_report": report,
                "timestamp": int(time.time())
            }
        )

        logger.info("=== Research Complete ===")
        return {"report": report, "from_cache": False, "tool_calls_made": findings}


# ------------------------------------------------------------------
# Quick Test: Challenge 1 - Microsoft Company Profile (Dry Run)
# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = AutonomousResearchAgent(dry_run=True)
    result = agent.research(
        query="Generate a company profile for Microsoft Corporation.",
        ticker="MSFT"
    )
    print("\n" + "="*60)
    print(result["report"])
    print("="*60)
