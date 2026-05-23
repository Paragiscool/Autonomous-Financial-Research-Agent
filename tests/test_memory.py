"""
tests/test_memory.py

Unit tests for the memory components (ContextManager, EpisodicMemory).
"""

import unittest
import os
import tempfile
from memory.episodic import EpisodicMemory

class TestEpisodicMemory(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.memory = EpisodicMemory(store_path=self.temp_file.name)

    def tearDown(self):
        os.remove(self.temp_file.name)

    def test_store_and_recall(self):
        self.memory.store_episode("test-id", "test query", "TEST", [], 0, 0, 1.0, "snippet", False)
        episodes = self.memory.recall_episodes(ticker="TEST")
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["episode_id"], "test-id")

if __name__ == '__main__':
    unittest.main()
