"""
Contains tests for the ctx module.
"""

import unittest
from eggsplode.core import ActionLog


class TestActionLog(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.log = ActionLog(
            (f"Action message {i}!" for i in range(11)), character_limit=60
        )
        self.messages = []
        self.messages = [f"Action message {i}!" for i in range(11)]
        self.expected_pages = [
            "Action message 0!\nAction message 1!\n",
            "Action message 2!\nAction message 3!\nAction message 4!\n",
            "Action message 5!\nAction message 6!\nAction message 7!\n",
            "Action message 8!\nAction message 9!\nAction message 10!\n",
        ]

    def test_init(self, *_):
        self.assertEqual(self.log.actions, [f"Action message {i}!" for i in range(11)])
        self.assertEqual(self.log.character_limit, 60)

    def test_add(self, *_):
        self.log.add("Action message 11!")
        self.assertIn("Action message 11!", self.log.actions)

    def test_pages(self, *_):
        self.assertEqual(self.log.pages, self.expected_pages)
        for page in self.log.pages:
            self.assertLessEqual(len(page), 60)
        self.assertEqual(len(self.log.pages), 4)

    def test_clear(self, *_):
        self.log.clear()
        self.assertEqual(self.log.actions, [])
        self.assertEqual(self.log.character_limit, 60)

    def test_str(self, *_):
        expected_str = "\n".join(self.messages)
        self.assertEqual(str(self.log), expected_str)

    def test_len(self, *_):
        self.assertEqual(len(self.log), 11)

    def test_iter(self, *_):
        actions = [action for action in self.log]
        self.assertEqual(actions, [f"Action message {i}!" for i in range(11)])

    def test_getitem(self):
        self.log[1] = "Test action 1"
        self.assertEqual(self.log[1], "Test action 1")

    def test_pages_no_character_limit(self, *_):
        log = ActionLog(
            (f"Action message {i}!" for i in range(11)), character_limit=None
        )
        expected_list = ["\n".join(self.messages)]
        self.assertEqual(log.pages, expected_list)


if __name__ == "__main__":
    unittest.main()
