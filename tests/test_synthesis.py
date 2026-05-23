"""
tests/test_synthesis.py

Unit tests for the synthesis engine.
"""

import unittest
from synthesis.engine import rank_findings, deduplicate_findings, route_to_sections

class TestSynthesisEngine(unittest.TestCase):
    def setUp(self):
        self.findings = [
            {"tool": "web_search", "status": "success", "summary": "web"},
            {"tool": "sec_filing_search", "status": "success", "summary": "sec"},
        ]

    def test_ranking(self):
        ranked = rank_findings(self.findings)
        self.assertEqual(ranked[0]["tool"], "sec_filing_search")

    def test_deduplication(self):
        dupes = [
            {"tool": "web_search", "status": "success", "summary": "web1"},
            {"tool": "web_search", "status": "success", "summary": "web2"},
        ]
        deduped = deduplicate_findings(dupes)
        self.assertEqual(len(deduped), 1)

if __name__ == '__main__':
    unittest.main()
