"""
Contains tests for the game logic of the Eggsplode game.
"""

import unittest
from datetime import datetime, timedelta
from eggsplode.game_logic import Game


class TestGame(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.config: dict = {"players": [1, 2, 3, 4, 5, 6, 7]}
        self.game = Game(self.config)

    def test_init(self):
        self.assertEqual(self.game.config, self.config)
        self.assertEqual(self.game.players, [])
        self.assertEqual(self.game.hands, {})
        self.assertEqual(self.game.deck, [])
        self.assertEqual(self.game.current_player, 0)
        self.assertEqual(self.game.action_id, 0)
        self.assertEqual(self.game.draw_in_turn, 0)
        self.assertIsInstance(self.game.last_activity, datetime)

    def test_start(self):
        self.game.start()
        self.assertAlmostEqual(
            self.game.last_activity, datetime.now(), delta=timedelta(seconds=1)
        )
        self.assertEqual(len(self.game.deck), 41)
        self.assertEqual(len(self.game.hands), 7)
        for hand in self.game.hands.values():
            self.assertEqual(len(hand), 8)
        self.assertEqual(self.game.deck.count("eggsplode"), 6)
        self.assertEqual(self.game.deck.count("radioeggtive"), 0)

    def test_start_with_expansions(self):
        self.config["expansions"] = ["radioeggtive"]
        self.game = Game(self.config)
        self.game.start()
        self.assertEqual(len(self.game.deck), 74)
        self.assertEqual(self.game.deck.count("eggsplode"), 6)
        self.assertEqual(self.game.deck.count("radioeggtive"), 1)

    def test_next_turn(self):
        self.game.start()
        for i in range(21):
            self.game.next_turn()
            self.assertEqual(self.game.current_player, (i + 1) % 7)

    def test_next_turn_with_draw_in_turn(self):
        self.game.start()
        self.game.current_player = 0
        self.game.draw_in_turn = 2
        self.game.next_turn()
        self.assertEqual(self.game.current_player, 0)
        self.assertEqual(self.game.draw_in_turn, 0)

    def test_group_hand(self):
        self.game.start()
        self.game.hands[1] = [
            "defuse",
            "nope",
            "nope",
            "predict",
            "skip",
            "skip",
            "attegg",
            "attegg",
            "predict",
            "food1",
            "food1",
            "food2",
        ]
        self.assertEqual(
            self.game.group_hand(1),
            {
                "defuse": 1,
                "nope": 2,
                "predict": 2,
                "skip": 2,
                "attegg": 2,
                "food1": 2,
                "food2": 1,
            },
        )

    def test_group_hand_with_empty_hand(self):
        self.game.start()
        self.game.hands[1] = []
        self.assertEqual(self.game.group_hand(1), {})

    def test_group_hand_usable_only(self):
        self.game.start()
        self.game.hands[1] = [
            "defuse",
            "nope",
            "nope",
            "predict",
            "skip",
            "skip",
            "attegg",
            "attegg",
            "predict",
            "food1",
            "food1",
            "food2",
        ]
        self.assertEqual(
            self.game.group_hand(1, usable_only=True),
            {
                "predict": 2,
                "skip": 2,
                "attegg": 2,
                "food1": 2,
            },
        )

    def test_draw_card(self):
        self.game.start()
        next_card = "predict"
        self.game.deck[-1] = next_card
        prev_hand = self.game.hands[1].copy()
        self.game.draw_card()
        self.assertEqual(self.game.hands[1], prev_hand + [next_card])
        self.assertEqual(len(self.game.hands[1]), 9)
        self.assertEqual(len(self.game.deck), 40)
        self.assertEqual(self.game.current_player_id, 2)

    def test_draw_card_defuse(self):
        self.game.start()
        self.game.deck[-1] = "eggsplode"
        self.game.hands[1] = ["defuse"]
        self.assertEqual(self.game.draw_card(), "defused")
        self.assertEqual(self.game.hands[1], [])
        self.assertEqual(len(self.game.hands), 7)
        self.assertEqual(len(self.game.deck), 40)
        self.assertEqual(self.game.current_player_id, 2)

    def test_draw_card_eggsplode(self):
        self.game.start()
        self.game.deck[-1] = "eggsplode"
        self.game.hands[1] = ["food1", "food2"]
        self.game.draw_card()
        self.assertEqual(len(self.game.hands), 6)
        self.assertEqual(len(self.game.deck), 40)
        self.assertEqual(self.game.current_player_id, 2)

    def test_draw_card_game_over(self):
        self.game.start()
        result = ""
        for _ in range(13):
            self.game.deck[-1] = "eggsplode"
            result = self.game.draw_card()
        self.assertEqual(result, "gameover")

    def test_draw_card_radioeggtive(self):
        self.game.start()
        self.game.deck[-1] = "radioeggtive"
        self.game.hands[1] = ["food1", "food2"]
        self.game.draw_card()
        self.assertEqual(len(self.game.hands), 7)
        self.assertEqual(len(self.game.deck), 40)
        self.assertEqual(self.game.current_player_id, 2)

    def test_draw_card_radioeggtive_face_up(self):
        self.game.start()
        self.game.deck[-1] = "radioeggtive_face_up"
        self.game.hands[1] = ["defuse", "food1", "food2"]
        self.game.draw_card()
        self.assertEqual(len(self.game.hands), 6)
        self.assertEqual(len(self.game.deck), 40)
        self.assertEqual(self.game.current_player_id, 2)

    def test_draw_card_radioeggtive_game_over(self):
        self.game.start()
        for _ in range(12):
            self.game.deck[-1] = "eggsplode"
            result = self.game.draw_card()
        self.game.deck[-1] = "radioeggtive_face_up"
        result = self.game.draw_card()
        self.assertEqual(result, "gameover")

    def test_any_player_has_cards(self):
        self.game.start()
        self.assertTrue(self.game.any_player_has_cards())
        for i in range(1, 8):
            self.game.hands[i] = []
        self.assertFalse(self.game.any_player_has_cards())

    def test_card_comes_in(self):
        self.game.start()
        for i, _ in enumerate(self.game.deck):
            self.game.deck[i] = ""
        self.game.deck[-1] = "eggsplode"
        self.game.deck[0] = "food1"
        self.game.deck[1] = "food2"
        self.assertEqual(self.game.card_comes_in("eggsplode"), 0)
        self.assertEqual(self.game.card_comes_in("does_not_exist"), None)
        self.assertEqual(self.game.card_comes_in("food1"), 40)
        self.assertEqual(self.game.card_comes_in("food2"), 39)

    def test_current_player_hand(self):
        self.game.start()
        self.game.hands[1] = ["food1", "food2"]
        self.assertEqual(self.game.current_player_hand, ["food1", "food2"])

    def test_next_player_id(self):
        self.game.start()
        self.assertEqual(self.game.next_player_id, 2)
        self.game.current_player = 6
        self.assertEqual(self.game.next_player_id, 1)

    def test_reverse(self):
        self.game.start()
        self.game.current_player = 1
        self.game.reverse()
        self.assertEqual(self.game.current_player_id, 2)
        self.assertEqual(self.game.next_player_id, 1)
        self.assertEqual(self.game.players, [7, 6, 5, 4, 3, 2, 1])


if __name__ == "__main__":
    unittest.main()
