"""
Contains the game logic for the Eggsplode game.
"""

from datetime import datetime
import random
from .strings import CARDS, replace_emojis


class Game:
    def __init__(self, config: dict):
        self.config = config
        self.players: list[int] = []
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.current_player: int = 0
        self.action_id: int = 0
        self.draw_in_turn: int = 0
        self.last_activity = datetime.now()

    def start(self):
        self.last_activity = datetime.now()
        self.deck = []
        self.players = list(self.config["players"])
        for card in CARDS:
            self.deck += (
                [card]
                * CARDS[card].get("count", 0)
                * (
                    CARDS[card].get("expansion", "base")
                    in self.config.get("expansions", []) + ["base"]
                )
            )
        self.deck = self.deck * (1 + len(self.players) // 5)
        random.shuffle(self.deck)
        self.hands = {
            player: ["defuse"] + [self.deck.pop() for _ in range(7)]
            for player in self.players
        }
        if self.config.get("short", not len(self.players) > 2):
            # Remove a random number of cards from the deck
            deck_size = len(self.deck)
            cards_to_remove = random.randint(deck_size // 3, deck_size // 2)
            for _ in range(cards_to_remove):
                self.deck.pop(random.randint(0, len(self.deck) - 1))
        self.deck += ["radioeggtive"] * (
            "radioeggtive" in self.config.get("expansions", [])
        )
        self.deck += ["eggsplode"] * int(
            self.config.get(
                "deck_eggsplode_cards",
                len(self.players) - 1,
            )
        )
        self.deck += ["defuse"] * int(self.config.get("deck_defuse_cards", 0))
        random.shuffle(self.deck)

    @property
    def current_player_id(self) -> int:
        return self.players[self.current_player]

    @property
    def current_player_hand(self) -> list[str]:
        return self.hands[self.current_player_id]

    @property
    def next_player(self) -> int:
        return (
            0
            if self.current_player >= len(self.players) - 1
            else self.current_player + 1
        )

    @property
    def next_player_id(self) -> int:
        return self.players[self.next_player]

    def next_turn(self):
        self.last_activity = datetime.now()
        if self.draw_in_turn > 1:
            self.draw_in_turn -= 1
            if self.draw_in_turn == 1:
                self.draw_in_turn = 0
            return
        self.current_player = self.next_player

    def group_hand(self, user_id: int, usable_only: bool = False) -> dict:
        player_cards = self.hands[user_id]
        result = {}
        for card in player_cards:
            if usable_only:
                if not CARDS[card].get("usable", False):
                    continue
                if CARDS[card].get("combo", 0) > 0 and player_cards.count(card) < 2:
                    continue
            if card in result:
                continue
            result[card] = player_cards.count(card)
        return result

    def draw_card(self, index: int = -1) -> str:
        card = self.deck.pop(index)
        if card == "eggsplode":
            if "defuse" in self.hands[self.current_player_id]:
                self.hands[self.current_player_id].remove("defuse")
                return "defused"
            self.remove_player(self.current_player_id)
            self.draw_in_turn = 0
            if len(self.players) == 1:
                return "gameover"
        elif card == "radioeggtive_face_up":
            self.remove_player(self.current_player_id)
            self.draw_in_turn = 0
            if len(self.players) == 1:
                return "gameover"
        elif card != "radioeggtive":
            self.hands[self.current_player_id].append(card)
        return card

    def remove_player(self, user_id: int):
        del self.players[self.players.index(user_id)]
        del self.hands[user_id]
        self.current_player -= 1
        self.draw_in_turn = 0

    def any_player_has_cards(self) -> bool:
        eligible_players = self.players.copy()
        eligible_players.remove(self.current_player_id)
        return any(self.hands[player] for player in eligible_players)

    def card_comes_in(self, card) -> int | None:
        for i in range(len(self.deck) - 1, -1, -1):
            if self.deck[i] == card:
                return len(self.deck) - 1 - i
        return None

    def reverse(self):
        self.players = self.players[::-1]
        self.current_player = len(self.players) - self.current_player - 1

    def cards_help(self, user_id: int, template: str = "") -> str:
        grouped_hand = self.group_hand(user_id)
        return "\n".join(
            template.format(
                replace_emojis(CARDS[card]["emoji"]),
                CARDS[card]["title"],
                count,
                CARDS[card]["description"],
            )
            for card, count in grouped_hand.items()
        )
