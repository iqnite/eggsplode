"""
Contains tests for the core module.
"""

import json
import unittest
from unittest.mock import MagicMock
from eggsplode import cards
from eggsplode.core import Game
from eggsplode.strings import CARDS, RECIPES
from eggsplode.ui.start import COVERED_RECIPE_EXCEPTIONS


class TestGameSetup(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.game = Game(MagicMock(), {"players": [], "recipe": {}})

    @property
    def recipe(self) -> dict:
        return self.game.config.get("recipe", {})

    @recipe.setter
    def recipe(self, value: dict):
        self.game.config["recipe"] = value

    @property
    def players(self) -> list[str]:
        return self.game.config.get("players", [])

    @players.setter
    def players(self, value: list):
        self.game.config["players"] = value

    def assert_deck_count_equal(self, card, amount):
        self.assertEqual(self.game.deck.count(card), amount)

    def test_empty(self):
        self.players = ["forb", "dorb", "sorb"]
        self.game.setup()
        for hand in self.game.hands.values():
            self.assertEqual(len(hand), 0)
        self.assertEqual(self.game.deck, ["eggsplode"] * 2)

    def test_classic(self):
        self.players = ["forb", "dorb", "sorb", "gorb"]
        self.recipe = RECIPES["classic"]
        self.game.config["deck_size"] = 1000
        expected_cards = {
            "skip": 4,
            "nope": 5,
            "attegg": 4,
            "shuffle": 4,
            "see_future": 5,
            "food0": 4,
            "food1": 4,
            "food2": 4,
            "food3": 4,
        }
        self.game.setup()
        for hand in self.game.hands.values():
            self.assertEqual(hand.count("defuse"), 1)
            self.assertEqual(len(hand), 8)
        self.assert_deck_count_equal("eggsplode", 3)
        self.assert_deck_count_equal("radioeggtive", 0)
        for card, count in expected_cards.items():
            hand_count = sum(hand.count(card) for hand in self.game.hands.values())
            self.assertEqual(self.game.deck.count(card) + hand_count, count)

    def test_trim_classic(self):
        self.players = ["forb", "dorb", "sorb"]
        self.recipe = RECIPES["classic"]
        self.game.config["deck_size"] = 10
        self.game.setup()
        self.assert_deck_count_equal("eggsplode", 2)
        self.assertLessEqual(len(self.game.deck), 12)

    def test_expand(self):
        self.players = ["forb", "dorb", "sorb", "iorb", "gorb", "morb"]
        self.recipe = RECIPES["classic"]
        self.game.setup()
        for hand in self.game.hands.values():
            self.assertEqual(hand.count("defuse"), 1)
            self.assertEqual(len(hand), 8)
        self.assert_deck_count_equal("eggsplode", 5)

    def test_expand_radioeggtive(self):
        self.players = ["forb", "dorb", "sorb", "iorb", "gorb", "morb"]
        self.recipe = RECIPES["classic_radioeggtive"]
        self.game.setup()
        self.assert_deck_count_equal("radioeggtive", 1)
        self.assert_deck_count_equal("eggsplode", 4)

    def test_expand_eggsperiment(self):
        self.players = ["forb", "dorb", "sorb", "iorb", "gorb", "morb"]
        self.recipe = RECIPES["classic_eggsperiment"]
        self.game.setup()
        self.assert_deck_count_equal("eggsperiment", 2)
        self.assert_deck_count_equal("eggsplode", 5)

    def test_trim_eggsperiment(self):
        self.players = ["forb", "dorb", "sorb", "iorb", "gorb"]
        self.recipe = RECIPES["classic_eggsperiment"]
        self.game.config["deck_size"] = 5
        for _ in range(5):
            self.game.setup()
            self.assert_deck_count_equal("eggsperiment", 2)
            self.assert_deck_count_equal("eggsplode", 4)

    def test_auto_amount(self):
        self.players = ["forb", "dorb", "sorb"]
        self.recipe = {
            "cards": {
                "radioeggtive": {"auto_amount": -1, "hand_out": 0, "preserve": True}
            }
        }
        self.game.config["deck_size"] = None
        self.game.setup()
        for hand in self.game.hands.values():
            self.assertEqual(hand.count("radioeggtive"), 0)
        self.assert_deck_count_equal("radioeggtive", 2)
        self.assert_deck_count_equal("eggsplode", 0)

    def test_all_recipes(self):
        self.players = ["forb", "dorb", "sorb"]
        for recipe_name, recipe in RECIPES.items():
            with self.subTest(recipe=recipe_name):
                self.recipe = recipe
                self.game.setup()
                for card in self.game.deck:
                    self.assertIn(
                        card,
                        cards.PLAY_ACTIONS
                        | cards.DRAW_ACTIONS
                        | {"defuse": ..., "nope": ...},
                    )
                    self.assertIn(card, CARDS)


class TestRecipeLoading(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.game = Game(MagicMock(), {"players": ["forb", "sorb"]})

    def test_empty(self):
        self.game.load_recipe(r"{}")
        self.assertEqual(self.game.deck, ["eggsplode"])

    def test_no_dict(self):
        with self.assertRaises(TypeError):
            self.game.load_recipe(r'"test"')

    def test_invalid(self):
        dummy_recipe = r'"cards": {"foo": 99, "bar": {"x": 99}}}'
        with self.assertRaises(json.JSONDecodeError):
            self.game.load_recipe(dummy_recipe)

    def test_wrong_types(self):
        dummy_cards = [
            r"True",
            r"-1",
            r'"amount": True',
            r'"hand_out": True',
            r'"expand_beyond": True',
            r'"auto_amount": True',
        ]
        dummy_recipes = [
            r'{"cards_per_player": "1"}',
            r'{"cards": 1}',
        ] + [r'{"cards": {"foo": {' + card + r"}}}" for card in dummy_cards]
        for recipe in dummy_recipes:
            with self.assertRaises(COVERED_RECIPE_EXCEPTIONS):
                self.game.load_recipe(recipe)
