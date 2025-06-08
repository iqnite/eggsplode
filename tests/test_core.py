"""
Contains tests for the core module.
"""

import unittest
from unittest.mock import MagicMock
from eggsplode.core import Game


class TestGame(unittest.TestCase):
    def setUp(self):
        self.config = {
            "players": ["foo", "bar", "baz", "qux"],
            "expansions": ["radioeggtive"],
        }
        self.game = Game(MagicMock(), self.config)

    def test_setup(self):
        self.game.setup()
        for hand in self.game.hands.values():
            self.assertEqual(hand.count("defuse"), 1)
            self.assertEqual(len(hand), 8)
        self.assertEqual(self.game.deck.count("eggsplode"), 3)
        self.assertEqual(self.game.deck.count("radioeggtive"), 1)

        self.game.config["expansions"].remove("radioeggtive")
        self.game.setup()
        self.assertEqual(self.game.deck.count("radioeggtive"), 0)

        self.game.config["deck_eggsplode_cards"] = 2
        self.game.setup()
        self.assertEqual(self.game.deck.count("eggsplode"), 3)

        self.game.config["deck_eggsplode_cards"] = 10
        self.game.setup()
        self.assertEqual(self.game.deck.count("eggsplode"), 10)

        self.game.config["deck_defuse_cards"] = 2
        self.game.setup()
        self.assertEqual(self.game.deck.count("defuse"), 2)

        self.game.config["players"] = ["foo", "bar"]
        self.game.config["deck_eggsplode_cards"] = 1
        self.game.setup()
        self.assertEqual(self.game.deck.count("eggsplode"), 1)

        del self.game.config["deck_eggsplode_cards"]
        self.game.setup()
        self.assertEqual(self.game.deck.count("eggsplode"), 2)
