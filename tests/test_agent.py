"""
tests/test_agent.py

Unit tests for the core AutonomousResearchAgent.
"""

import unittest
from agent.core import AutonomousResearchAgent

class TestAgentCore(unittest.TestCase):
    def setUp(self):
        self.agent = AutonomousResearchAgent(dry_run=True)

    def test_initialization(self):
        self.assertTrue(self.agent.dry_run)
        self.assertIsNotNone(self.agent.session_id)

    def test_research_flow_dry_run(self):
        result = self.agent.research("Test query", ticker="TEST")
        self.assertIn("report", result)
        self.assertIn("tool_calls_made", result)

if __name__ == '__main__':
    unittest.main()
