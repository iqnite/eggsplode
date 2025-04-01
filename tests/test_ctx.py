"""
Contains tests for the ctx module.
"""

import unittest
from unittest.mock import patch
from eggsplode.ctx import ActionLog
from eggsplode.strings import get_message


def mock_get_message(key):
    clean_key = int(key.replace("action", ""))
    if clean_key > 10:
        raise KeyError(f"Key {key} not found")
    return f"Action message {clean_key}!"


@patch(
    "eggsplode.ctx.get_message",
    side_effect=mock_get_message,
)
class TestActionLog(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.log = ActionLog((f"action{i}" for i in range(11)), character_limit=60)
        self.messages = []
        self.messages = [f"Action message {i}!" for i in range(11)]

    def test_init(self, *_):
        self.assertEqual(self.log._actions, [f"action{i}" for i in range(11)])
        self.assertEqual(self.log.character_limit, 60)

    def test_add(self, *_):
        self.log.add("action10")
        self.assertIn("action10", self.log._actions)

    def test_pages(self, *_):
        for i, page in enumerate(self.log.pages):
            self.assertEqual(page, "\n".join(self.messages[i * 3 : (i + 1) * 3]))
            self.assertLessEqual(len(page), 60)

    def test_amount_of_pages(self, *_):
        self.assertEqual(self.log.amount_of_pages, 4)

    def test_clear(self, *_):
        self.log.clear()
        self.assertEqual(self.log._actions, [])
        self.assertEqual(self.log.character_limit, 60)

    def test_str(self, *_):
        expected_str = "\n".join(self.messages)
        self.assertEqual(str(self.log), expected_str)

    def test_len(self, *_):
        self.assertEqual(len(self.log), 11)

    def test_iter(self, *_):
        actions = [action for action in self.log]
        self.assertEqual(actions, [f"Action message {i}!" for i in range(11)])

    def test_pages_no_character_limit(self, *_):
        log = ActionLog((f"action{i}" for i in range(11)), character_limit=None)
        expected_str = "\n".join(self.messages)
        self.assertEqual(next(log.pages), expected_str)


if __name__ == "__main__":
    unittest.main()
