"""
Contains the game logic for the Eggsplode game.
"""

from datetime import datetime
from importlib import import_module
import random
from typing import Callable, Coroutine

import discord
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
        self.play_actions: dict[str, Callable[[discord.Interaction], Coroutine]]
        self.draw_actions: dict[str, Callable[[discord.Interaction, bool], Coroutine]]

    def start(self):
        self.last_activity = datetime.now()
        self.deck = []
        self.players = list(self.config["players"])
        self.load_cards()
        for card in CARDS:
            if CARDS[card].get("expansion", "base") in self.config.get(
                "expansions", []
            ) + ["base"]:
                self.deck += [card] * CARDS[card].get("count", 0)
        self.expand_deck()
        self.shuffle_deck()
        self.hands = {
            player: ["defuse"] + [self.deck.pop() for _ in range(7)]
            for player in self.players
        }
        if self.config.get("short", not len(self.players) > 2):
            self.trim_deck(3, 2)
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
        self.shuffle_deck()

    def trim_deck(self, min_part, max_part):
        deck_size = len(self.deck)
        cards_to_remove = random.randint(deck_size // min_part, deck_size // max_part)
        for _ in range(cards_to_remove):
            self.deck.pop(random.randint(0, len(self.deck) - 1))

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def expand_deck(self):
        self.deck = self.deck * (1 + len(self.players) // 5)

    def load_cards(self):
        for card_set in self.config.get("expansions", ["base"]):
            try:
                module = import_module(f".cards.{card_set}", __package__)
                self.play_actions = module.PLAY_ACTIONS
                self.draw_actions = module.DRAW_ACTIONS
            except ImportError as e:
                raise ImportError(f"Card set {card_set} not found.") from e

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

    async def play(self, interaction: discord.Interaction, card: str):
        if card in self.play_actions:
            await self.play_actions[card](interaction)

    async def draw(
        self, interaction: discord.Interaction, card: str, timed_out: bool = False
    ) -> tuple[str, bool]:
        if card in self.draw_actions:
            await self.draw_actions[card](interaction, timed_out)
            hold = False
        else:
            self.hands[self.current_player_id].append(card)
            hold = True
        return card, hold

    async def draw_from(
        self, interaction: discord.Interaction, index: int = -1, timed_out: bool = False
    ):
        card = self.deck.pop(index)
        return await self.draw(interaction, card, timed_out)

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
