"""
Contains tests for the ctx module.
"""

import unittest
from eggsplode.ctx import ActionLog


class TestActionLog(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.log = ActionLog(
            (f"Action message {i}!" for i in range(11)), character_limit=60
        )
        self.messages = []
        self.messages = [f"Action message {i}!" for i in range(11)]

    def test_init(self, *_):
        self.assertEqual(self.log.actions, [f"Action message {i}!" for i in range(11)])
        self.assertEqual(self.log.character_limit, 60)

    def test_add(self, *_):
        self.log.add("Action message 11!")
        self.assertIn("Action message 11!", self.log.actions)

    def test_pages(self, *_):
        for i, page in enumerate(self.log.pages):
            self.assertEqual(page, "\n".join(self.messages[i * 3 : (i + 1) * 3]))
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
