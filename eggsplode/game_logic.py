"""
Contains the game logic for the Eggsplode game.
"""

import asyncio
from datetime import datetime, timedelta
from importlib import import_module
import random
from typing import Callable, Coroutine

import discord
from .strings import CARDS, get_message, replace_emojis


class Game:
    def __init__(self, app, config: dict):
        self.config = config
        self.app = app
        self.players: list[int] = []
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.current_player: int = 0
        self.action_id: int = 0
        self.draw_in_turn: int = 0
        self.log = ActionLog()
        self.events = EventSet()
        self.last_activity = datetime.now()
        self.running = True
        self.paused = False
        self.inactivity_count = 0
        self.play_actions: dict[str, Callable[[Game, discord.Interaction], Coroutine]]
        self.draw_actions: dict[
            str, Callable[[Game, discord.Interaction, bool], Coroutine]
        ]
        self.turn_warnings: list[Callable[[Game], str]]
        self.events.turn_end += self.next_turn
        self.events.game_end += self.end
        self.events.action_start += self.pause

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
        self.play_actions = {}
        self.draw_actions = {}
        self.turn_warnings = []
        for card_set in self.config.get("expansions", []) + ["base"]:
            try:
                module = import_module(f".cards.{card_set}", __package__)
                self.play_actions.update(getattr(module, "PLAY_ACTIONS", {}))
                self.draw_actions.update(getattr(module, "DRAW_ACTIONS", {}))
                self.turn_warnings.extend(getattr(module, "TURN_WARNINGS", []))
            except ImportError as e:
                raise ImportError(f"Card set {card_set} not found.") from e

    @property
    def current_player_id(self) -> int:
        return self.players[self.current_player]

    @current_player_id.setter
    def current_player_id(self, value: int):
        if value in self.players:
            self.current_player = self.players.index(value)
        else:
            raise ValueError(f"Player {value} not found in the game.")

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

    @property
    def next_turn_player_id(self) -> int:
        return self.next_player_id if self.draw_in_turn == 0 else self.current_player_id

    async def next_turn(self):
        self.action_id += 1
        self.last_activity = datetime.now()
        if self.draw_in_turn > 1:
            self.draw_in_turn -= 1
            if self.draw_in_turn == 1:
                self.draw_in_turn = 0
        else:
            self.current_player = self.next_player
        await self.events.turn_start()

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
        await self.play_actions[card](self, interaction)

    async def draw(
        self, interaction: discord.Interaction, card: str, timed_out: bool = False
    ) -> tuple[str, bool]:
        if card in self.draw_actions:
            await self.draw_actions[card](self, interaction, timed_out)
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

    async def action_timer(self):
        while (
            datetime.now() - self.last_activity
            < timedelta(seconds=self.config.get("turn_timeout", 60))
        ) or self.paused:
            await asyncio.sleep(1)
        await self.on_action_timeout()

    async def on_action_timeout(self):
        assert self.log.anchor_interaction is not None
        self.pause()
        self.inactivity_count += 1
        if self.inactivity_count > 5:
            await self.log(get_message("game_timeout"))
            await self.events.game_end()
            return
        turn_player: int = self.current_player_id
        await self.log(get_message("timeout"))
        _, hold = await self.draw_from(
            self.log.anchor_interaction, timed_out=True
        )
        if hold:
            await self.log(get_message("user_drew_card").format(turn_player))
        if not self.running:
            return
        await self.events.turn_end()

    def pause(self):
        self.paused = True

    async def end(self):
        self.running = False
        self.paused = False
        self.current_player = 0
        self.players = []
        self.hands = {}
        self.deck = []
        self.action_id = 0
        self.draw_in_turn = 0

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

    def create_turn_prompt_message(self) -> str:
        return (
            get_message("next_turn").format(
                self.current_player_id,
            )
            + "\n"
            + self.warnings()
        )

    def warnings(self) -> str:
        return "\n".join(warning(self) for warning in self.turn_warnings)

    def __bool__(self):
        return self.running


class ActionLog:
    def __init__(
        self,
        actions=None,
        anchor_interaction: discord.Interaction | None = None,
        anchor_message: discord.Message | None = None,
        character_limit: int | None = 1800,
    ):
        self.actions: list[str] = list(actions) if actions else []
        self.character_limit = character_limit
        self.anchor_interaction = anchor_interaction
        self.anchor_message = anchor_message

    def add(self, action: str):
        self.actions.append(action)

    def clear(self):
        self.actions.clear()

    @property
    def pages(self):
        if self.character_limit is None:
            return [str(self)]
        if len(self) == 0:
            return [""]
        result = []
        line = len(self) - 1
        action = next_action = ""
        while line >= 0:
            next_action = self[line] + "\n" + action
            if len(next_action) > self.character_limit:
                result.insert(0, action)
                action = ""
                continue
            line -= 1
            action = next_action
        return [next_action] + result

    async def temporary(
        self,
        message: str,
        view: discord.ui.View | None = None,
        anchor: discord.Interaction | None = None,
    ):
        await self(message, view, anchor)
        del self[-1]

    async def __call__(
        self,
        message: str,
        view: discord.ui.View | None = None,
        anchor: discord.Interaction | None = None,
    ):
        self.add(message)
        if anchor is not None:
            self.anchor_interaction = anchor
        if self.anchor_interaction is None:
            raise ValueError("anchor_interaction is None")
        args = {"content": self.pages[-1], "view": view}
        try:
            await self.anchor_interaction.response.edit_message(**args)
        except discord.errors.InteractionResponded:
            if self.anchor_message is None:
                self.anchor_message = await self.anchor_interaction.original_response()
            await self.anchor_interaction.followup.edit_message(
                self.anchor_message.id,
                **args,
            )
        else:
            if self.anchor_message is None:
                self.anchor_message = await self.anchor_interaction.original_response()

    def __str__(self):
        return "\n".join(self.actions)

    def __len__(self):
        return len(self.actions)

    def __iter__(self):
        return self.actions.__iter__()

    def __getitem__(self, index):
        return self.actions[index]

    def __setitem__(self, index, value):
        self.actions[index] = value

    def __delitem__(self, index):
        del self.actions[index]


class Event:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, callback: Callable):
        self.subscribers.append(callback)
        return self

    def unsubscribe(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)
        return self

    async def notify(self, *args, **kwargs):
        for callback in self.subscribers:
            r = callback(*args, **kwargs)
            if isinstance(r, Coroutine):
                await r

    __call__ = notify
    __add__ = subscribe
    __sub__ = unsubscribe


class EventSet:
    def __init__(self):
        self.game_start = Event()
        self.game_end = Event()
        self.turn_start = Event()
        self.turn_reset = Event()
        self.turn_end = Event()
        self.action_start = Event()
        self.action_end = Event()
