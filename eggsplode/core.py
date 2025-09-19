"""
Contains the game logic for the Eggsplode game.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Callable, Coroutine, TYPE_CHECKING
import discord
from eggsplode import cards
from eggsplode.ui import NopeView, PlayView, TurnView, TextView
from eggsplode.strings import CARDS, format_message, tooltip

if TYPE_CHECKING:
    from eggsplode.commands import EggsplodeApp


class Game:
    def __init__(self, app: "EggsplodeApp", config: dict, game_id=0):
        self.app = app
        self.config = config
        self.id = game_id
        self.recipe_cards: dict[str, int | dict] = {}
        self.players: list[int] = []
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.current_player: int = 0
        self._action_player_id: int | None = None
        self.action_id: int = 0
        self.remaining_turns: int = 0
        self.events = EventSet()
        self.last_activity = datetime.now()
        self.active = True
        self.started = False
        self.paused = False
        self.inactivity_count = 0
        self.anchor_interaction: discord.Interaction | None = None
        self.followup_count: int = 0
        self.play_actions: dict[
            str, Callable[[Game, discord.Interaction], Coroutine]
        ] = cards.PLAY_ACTIONS
        self.draw_actions: dict[
            str, Callable[[Game, discord.Interaction, bool | None], Coroutine]
        ] = cards.DRAW_ACTIONS
        self.turn_warnings: list[Callable[[Game], str]] = cards.TURN_WARNINGS
        self.events.turn_end += self.next_turn
        self.events.game_end += self.end
        self.events.action_start += self.pause
        self.events.turn_reset += self.reset_timer
        self.events.action_end += self.resume
        self.events.turn_start += self.resume

    def setup(self):
        self.load_recipe(self.config["recipe"])

    def load_recipe(self, recipe: str | bytes | bytearray | dict):
        if not isinstance(recipe, dict):
            recipe = json.loads(recipe)
        if not isinstance(recipe, dict):
            raise TypeError(f"Recipe must be a dict, but is a {type(recipe)}")

        self.recipe_cards = recipe.get("cards", {})
        self.players = list(self.config["players"])
        self.deck = []
        self.hands = {player: [] for player in self.players}
        hand_out_pool = []

        for card, info in self.recipe_cards.items():
            if card not in CARDS:
                raise ValueError(f"Card `{card}` does not exist")
            if isinstance(info, int):
                cards_to_add = [card] * info * self.card_multiplier(5)
                hand_out_pool += cards_to_add
            else:
                # Handle automatic card amount
                if "auto_amount" in info:
                    cards_to_add = [card] * max(
                        0, len(self.players) + info["auto_amount"]
                    )
                else:
                    cards_to_add = (
                        [card]
                        * info.get("amount", 0)
                        * self.card_multiplier(info.get("expand_beyond", 5))
                    )

                if "hand_out" in info:
                    self.deck += cards_to_add
                else:
                    hand_out_pool += cards_to_add

                # Hand out fixed cards
                for _ in range(info.get("hand_out", 0)):
                    for hand in self.hands.values():
                        hand.append(card)

        self.hand_out(recipe, hand_out_pool)

        self.deck += hand_out_pool

        self.shuffle_deck()
        self.trim_deck()
        self.ensure_minimum_eggsplode()
        self.shuffle_deck()

    def hand_out(self, recipe: dict, hand_out_pool: list):
        max_cards_per_player = min(
            recipe.get("cards_per_player", 8), len(hand_out_pool) // len(self.players)
        )
        random.shuffle(hand_out_pool)
        for hand in self.hands.values():
            while len(hand) < max_cards_per_player:
                hand.append(
                    hand_out_pool.pop(random.randint(0, len(hand_out_pool) - 1))
                )

    def ensure_minimum_eggsplode(self):
        while (
            self.deck.count("eggsplode") + self.deck.count("radioeggtive")
            < len(self.players) - 1
        ):
            self.deck.append("eggsplode")

    def trim_deck(self):
        max_deck_size = self.config.get("deck_size", None)
        if not max_deck_size:
            return
        max_deck_size = int(max_deck_size)
        # Prevent infinite loop if no more cards can be removed
        loop_counter = 0
        max_loops = len(self.deck)
        while len(self.deck) > max_deck_size and loop_counter <= max_loops:
            loop_counter += 1
            card = self.deck.pop(0)
            info = self.recipe_cards.get(card)
            if info is None:
                continue
            if isinstance(info, dict) and info.get("preserve", False):
                self.deck.append(card)

    def card_multiplier(self, multiply_beyond: int | None) -> int:
        if multiply_beyond == 0:
            raise ValueError("`multiply_beyond` cannot be 0")
        return (
            (1 + len(self.players) // multiply_beyond)
            if multiply_beyond is not None
            else 1
        )

    async def start(self, interaction: discord.Interaction):
        self.setup()
        self.last_activity = datetime.now()
        self.inactivity_count = 0
        self.started = True
        self.app.logger.info(f"Game {self.id} started with players: {self.players}")
        await self.send(view=TextView("game_started"), anchor=interaction)
        await self.events.turn_start()
        await self.action_timer()

    def shuffle_deck(self):
        random.shuffle(self.deck)

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
    def action_player_id(self) -> int:
        return (
            self.current_player_id
            if self._action_player_id is None
            else self._action_player_id
        )

    @action_player_id.setter
    def action_player_id(self, value: int | None):
        self._action_player_id = value

    @property
    def action_player_hand(self) -> list[str]:
        return self.hands[self.action_player_id]

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
        return (
            self.next_player_id if self.remaining_turns == 0 else self.current_player_id
        )

    @property
    def player_list(self) -> str:
        return "\n".join(
            format_message("players_list_item", player)
            for player in self.config["players"]
        )

    async def next_turn(self):
        self.action_id += 1
        self.last_activity = datetime.now()
        self.action_player_id = None
        if self.remaining_turns > 1:
            self.remaining_turns -= 1
            if self.remaining_turns == 1:
                self.remaining_turns = 0
        else:
            self.current_player = self.next_player
        await self.events.turn_start()

    def group_hand(self, user_id: int, usable_only: bool = False) -> dict[str, int]:
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

    async def action_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user:
            raise TypeError("interaction.user is None")
        if interaction.user.id != self.action_player_id:
            await interaction.respond(
                view=TextView("not_your_turn"), ephemeral=True, delete_after=5
            )
            return False
        if self.paused:
            await interaction.respond(
                view=TextView("awaiting_prompt"), ephemeral=True, delete_after=5
            )
            return False
        return True

    async def draw_callback(self, interaction: discord.Interaction):
        if not await self.action_check(interaction):
            return
        await self.events.action_start()
        _, hold = await self.draw_from(interaction)
        if hold:
            await self.events.turn_end()

    async def show_hand(self, interaction: discord.Interaction):
        if not interaction.user:
            raise TypeError("interaction.user is None")
        view = PlayView(self, interaction.user.id)
        await interaction.respond(view=view, ephemeral=True)
        await self.events.turn_reset()

    async def play_callback(self, interaction: discord.Interaction, card: str):
        if not interaction.user:
            return
        if CARDS[card].get("now"):
            self.action_player_id = interaction.user.id
        if not await self.action_check(interaction):
            return
        self.action_player_hand.remove(card)
        await self.events.action_start()
        if CARDS[card].get("explicit", False):
            await self.play(interaction, card)
        else:
            view = NopeView(
                self,
                ok_callback_action=lambda _: self.play(interaction, card),
                message=format_message(
                    "play_card",
                    CARDS[card]["emoji"],
                    self.action_player_id,
                    tooltip(card, emoji=False),
                ),
            )
            await self.send(view=view)

    async def draw_from(
        self, interaction: discord.Interaction, index: int = -1, timed_out: bool = False
    ) -> tuple[str, bool]:
        turn_player: int = self.current_player_id
        self.anchor_interaction = interaction
        card, hold = await self.draw(interaction, self.deck.pop(index), timed_out)
        if hold:
            await self.send(
                view=TextView("user_drew_card", turn_player), anchor=interaction
            )
            if not timed_out:
                await interaction.respond(
                    view=TextView(
                        "you_drew_card",
                        tooltip(card),
                    ),
                    ephemeral=True,
                )
        return card, hold

    def remove_player(self, user_id: int):
        del self.players[self.players.index(user_id)]
        del self.hands[user_id]
        self.current_player -= 1
        self.remaining_turns = 0

    def players_with_cards(self, *card_names: str) -> list[int]:
        return [
            player
            for player in self.players
            if any(card in self.hands[player] for card in card_names)
        ]

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
        while self.active:
            if (
                datetime.now() - self.last_activity
                > timedelta(seconds=float(self.config.get("turn_timeout", 40)))
            ) and not self.paused:
                await self.on_action_timeout()
            await asyncio.sleep(5)

    async def on_action_timeout(self):
        if self.anchor_interaction is None:
            raise TypeError("anchor_interaction is None")
        if not self.active:
            return
        self.pause()
        self.inactivity_count += 1
        if self.inactivity_count > 5:
            self.app.logger.info(f"Game {self.id} ended due to inactivity.")
            await self.send(view=TextView("game_timeout"))
            await self.events.game_end()
            return
        self.last_activity = datetime.now()
        await self.send(view=TextView("timeout"))
        await self.draw_from(self.anchor_interaction, timed_out=True)
        await self.events.turn_end()

    def pause(self):
        self.paused = True

    async def resume(self):
        if not self.active:
            return
        self.reset_timer()
        self.action_player_id = None
        self.action_id += 1
        self.paused = False
        await self.send(view=TurnView(self))

    def reset_timer(self):
        self.last_activity = datetime.now()

    async def end(self):
        self.active = False
        self.started = False
        self.paused = False
        self.current_player = 0
        self.players = []
        self.hands = {}
        self.deck = []
        self.action_id = 0
        self.remaining_turns = 0
        self.followup_count = 0
        self.app.logger.info(f"Game {self.id} ended.")

    async def send(
        self,
        message: str | None = None,
        view: discord.ui.View | None = None,
        anchor: discord.Interaction | None = None,
    ):
        use_view = view
        if message is not None:
            if use_view is None:
                use_view = discord.ui.View()
            use_view.add_item(discord.ui.TextDisplay(message))
        if use_view is None:
            raise ValueError("Either message or view must be provided")
        if anchor is not None:
            self.anchor_interaction = anchor
            self.followup_count = 0  # Reset counter for new interaction
        if self.anchor_interaction is None:
            raise ValueError("anchor_interaction is None")

        # Discord allows max 15 follow-up messages per interaction
        # Use 10 as a safe limit to avoid hitting the exact limit
        max_followups = 10
        try:
            await self.anchor_interaction.response.send_message(view=use_view)
        except discord.errors.InteractionResponded:
            if self.followup_count >= max_followups:
                # If we've hit the follow-up limit, send a new message to the channel
                # This won't be linked to the interaction but will keep the game flowing
                if self.anchor_interaction.channel:
                    await self.anchor_interaction.channel.send(view=use_view)
                else:
                    # Fallback: try the follow-up anyway and let Discord handle the error
                    await self.anchor_interaction.followup.send(view=use_view)
            else:
                await self.anchor_interaction.followup.send(view=use_view)
                self.followup_count += 1

    @property
    def turn_prompt(self) -> str:
        return format_message("next_turn", self.current_player_id)

    @property
    def warnings(self) -> str:
        return "\n".join(warning(self) for warning in self.turn_warnings)

    def __bool__(self) -> bool:
        return self.active


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
