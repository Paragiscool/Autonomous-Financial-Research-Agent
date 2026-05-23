import os
import sys
from dotenv import load_dotenv

# Ensure project root is on path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from agent.core import AutonomousResearchAgent
from agent.llm_wrapper import RobustLLM

fake_data = [
  {"source_type": "Tier 4 - Web Search", "content": "NVIDIA just announced Q4 data center revenue hit exactly $19.0 Billion."},
  {"source_type": "Tier 1 - SEC 10-K", "content": "Fiscal Q4 Data Center Revenue was officially recorded at $18.4 Billion."}
]

def test_conflict_resolution():
    print("Initializing Agent with LLM for Conflict Resolution & Verifier Test...")
    try:
        llm = RobustLLM()
        agent = AutonomousResearchAgent(llm=llm, dry_run=False)
        
        query = "Generate a report on NVIDIA's Q4 data center revenue."
        
        print("\n[1] Running Synthesizer with fake conflicting data...")
        report = agent._synthesize(query=query, findings=fake_data)
        
        print("\n" + "="*60)
        print("OUTPUT DRAFT REPORT:")
        print("="*60)
        print(report)
        print("="*60)
        
        print("\n[2] Running Verifier on the correct report...")
        verification = agent._verify_facts(report, fake_data)
        print(f"Verification Results:")
        print(f"Verified: {verification.get('verified_report') is not None}")
        print(f"Errors caught: {verification.get('errors')}")
        
        print("\n[3] Running Verifier on a report containing a hallucinated number ($18.5 Billion)...")
        hallucinated_report = report.replace("$18.4 Billion", "$18.5 Billion")
        verification_hallucinated = agent._verify_facts(hallucinated_report, fake_data)
        print(f"Verification Results for Hallucinated Report:")
        print(f"Verified: {verification_hallucinated.get('verified_report') is not None}")
        print(f"Errors caught: {verification_hallucinated.get('errors')}")

    except Exception as e:
        print(f"\n[ERROR] Failed to run test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conflict_resolution()
