"""
Contains the game logic for the Eggsplode game.
"""

import asyncio
from datetime import datetime, timedelta
from importlib import import_module
import random
from typing import Callable, Coroutine, TYPE_CHECKING
import discord
from eggsplode.selections import PlayView
from eggsplode.strings import CARDS, EXPANSIONS, get_message, replace_emojis

if TYPE_CHECKING:
    from eggsplode.commands import EggsplodeApp


class Game:
    def __init__(self, app: "EggsplodeApp", config: dict):
        self.app = app
        self.config = config
        self.players: list[int] = []
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.current_player: int = 0
        self.action_id: int = 0
        self.draw_in_turn: int = 0
        self.events = EventSet()
        self.last_activity = datetime.now()
        self.running = True
        self.paused = False
        self.inactivity_count = 0
        self.play_actions: dict[str, Callable[[Game, discord.Interaction], Coroutine]]
        self.draw_actions: dict[
            str, Callable[[Game, discord.Interaction, bool | None], Coroutine]
        ]
        self.turn_warnings: list[Callable[[Game], str]]
        self.events.turn_end += self.next_turn
        self.events.game_end += self.end
        self.events.action_start += self.pause
        self.events.turn_reset += self.resume
        self.events.action_end += self.resume
        self.events.turn_start += self.resume

    async def start(self, interaction: discord.Interaction):
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
        await self.send(get_message("game_started"), anchor=interaction)
        await self.events.turn_start()
        await self.action_timer()

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

    @property
    def player_list(self) -> str:
        return "\n".join(
            get_message("players_list_item").format(player)
            for player in self.config["players"]
        )

    @property
    def expansion_list(self) -> str:
        return "\n".join(
            (
                *(
                    get_message("bold_list_item").format(
                        replace_emojis(EXPANSIONS[expansion]["emoji"]),
                        EXPANSIONS[expansion]["name"],
                    )
                    for expansion in self.config.get("expansions", [])
                ),
                (
                    ""
                    if self.config.get("expansions", [])
                    else get_message("no_expansions")
                ),
            )
        )

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
    ) -> tuple[str, bool]:
        turn_player: int = self.current_player_id
        card, hold = await self.draw(interaction, self.deck.pop(index), timed_out)
        if hold:
            await self.send(get_message("user_drew_card").format(turn_player))
            if not timed_out:
                await interaction.respond(
                    get_message("you_drew_card").format(
                        replace_emojis(CARDS[card]["emoji"]), CARDS[card]["title"]
                    ),
                    ephemeral=True,
                    delete_after=10,
                )
        return card, hold

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
        while self.running:
            if (
                datetime.now() - self.last_activity
                > timedelta(seconds=float(self.config.get("turn_timeout", 60)))
            ) and not self.paused:
                await self.on_action_timeout()
            await asyncio.sleep(5)

    async def on_action_timeout(self):
        assert self.anchor_interaction is not None
        self.pause()
        self.inactivity_count += 1
        if self.inactivity_count > 5:
            await self.send(get_message("game_timeout"))
            await self.events.game_end()
            return
        self.last_activity = datetime.now()
        await self.send(get_message("timeout"))
        await self.draw_from(self.anchor_interaction, timed_out=True)
        if not self.running:
            return
        await self.events.turn_end()

    def pause(self):
        self.paused = True

    async def resume(self):
        if not self.running:
            return
        self.last_activity = datetime.now()
        self.action_id += 1
        self.paused = False
        await self.send(view=TurnView(self))

    async def end(self):
        self.running = False
        self.paused = False
        self.current_player = 0
        self.players = []
        self.hands = {}
        self.deck = []
        self.action_id = 0
        self.draw_in_turn = 0

    async def send(
        self,
        message: str | None = None,
        view: discord.ui.View | None = None,
        anchor: discord.Interaction | None = None,
    ):
        use_view = view
        if message is not None:
            use_view = discord.ui.View(discord.ui.TextDisplay(message))
        if use_view is None:
            raise ValueError("Either message or view must be provided")
        if anchor is not None:
            self.anchor_interaction = anchor
        if self.anchor_interaction is None:
            raise ValueError("anchor_interaction is None")
        try:
            await self.anchor_interaction.response.send_message(view=use_view)
        except discord.errors.InteractionResponded:
            await self.anchor_interaction.followup.send(view=use_view)

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

    @property
    def turn_prompt(self) -> str:
        return get_message("next_turn").format(self.current_player_id)

    @property
    def warnings(self) -> str:
        return "\n".join(warning(self) for warning in self.turn_warnings)

    def __bool__(self) -> bool:
        return self.running


class Event:
    def __init__(self):
        self._subscribers = []

    def subscribe(self, callback: Callable, index=-1):
        self._subscribers.insert(index, callback)
        return self

    def unsubscribe(self, callback):
        if callback in self._subscribers:
            self._subscribers.remove(callback)
        return self

    async def notify(self, *args, **kwargs):
        callbacks = self._subscribers.copy()
        for callback in callbacks:
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


class BaseView(discord.ui.View):
    def __init__(self, game: Game):
        super().__init__(timeout=None)
        self.game = game

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await super().interaction_check(interaction):
            return False
        await interaction.response.defer(invisible=True)
        return True


class TurnView(BaseView):
    def __init__(self, game: Game):
        super().__init__(game)
        self.turn_prompt = discord.ui.TextDisplay(game.turn_prompt)
        self.add_item(self.turn_prompt)
        self.draw_button = discord.ui.Button(
            label="Draw", style=discord.ButtonStyle.blurple, emoji="🤚"
        )
        self.draw_button.callback = self.draw_callback
        self.add_item(self.draw_button)
        self.play_button = discord.ui.Button(
            label="Play a card", style=discord.ButtonStyle.green, emoji="🎴"
        )
        self.play_button.callback = self.play_callback
        self.add_item(self.play_button)
        self.warnings = discord.ui.TextDisplay(self.game.warnings)
        self.add_item(self.warnings)
        self.game.events.turn_end.subscribe(self.deactivate, 0)
        self.game.events.game_end.subscribe(self.deactivate, 0)

    async def interaction_check(self, interaction: discord.Interaction):
        if not await super().interaction_check(interaction):
            return False
        if not interaction.user:
            raise TypeError("interaction.user is None")
        if interaction.user.id != self.game.current_player_id:
            await interaction.respond(
                get_message("not_your_turn"), ephemeral=True, delete_after=5
            )
            return False
        if self.game.paused:
            await interaction.respond(
                get_message("awaiting_prompt"), ephemeral=True, delete_after=5
            )
            return False
        self.game.anchor_interaction = interaction
        self.game.inactivity_count = 0
        return True

    async def draw_callback(self, interaction: discord.Interaction):
        await self.game.events.action_start()
        _, hold = await self.game.draw_from(interaction)
        if hold:
            await self.game.events.turn_end()

    async def play_callback(self, interaction: discord.Interaction):
        view = PlayView(self.game)
        await interaction.respond(
            view.create_play_prompt_message(self.game.current_player_id),
            view=view,
            ephemeral=True,
        )
        await self.game.events.turn_reset()

    async def deactivate(self):
        self.stop()
        self.disable_all_items()
        self.game.events.turn_end.unsubscribe(self.deactivate)
        for item in (self.draw_button, self.play_button, self.warnings):
            self.remove_item(item)
        if self.game.anchor_interaction:
            await self.game.anchor_interaction.edit_original_response(view=self)
