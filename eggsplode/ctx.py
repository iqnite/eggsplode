"""
Contains the context classes for the game actions.
"""

from collections.abc import Callable, Coroutine
import discord
from .game_logic import Game


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

    async def temporary(self, message: str, view: discord.ui.View | None = None):
        await self(message, view)
        del self[-1]

    async def __call__(
        self,
        message: str,
        view: discord.ui.View | None = None,
    ):
        self.add(message)
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


class EventController:
    GAME_START = 1
    GAME_END = 2
    TURN_START = 3
    TURN_RESET = 4
    TURN_END = 5
    ACTION_START = 6
    ACTION_END = 7

    def __init__(self):
        self.subscribers: dict[int, list[Callable]] = {
            self.GAME_START: [],
            self.GAME_END: [],
            self.TURN_START: [],
            self.TURN_RESET: [],
            self.TURN_END: [],
            self.ACTION_START: [],
            self.ACTION_END: [],
        }

    def subscribe(self, event: int, callback: Callable):
        if event not in self.subscribers:
            raise ValueError(f"Invalid event: {event}")
        self.subscribers[event].append(callback)
        return callback

    def unsubscribe(self, event: int, callback):
        if event not in self.subscribers:
            raise ValueError(f"Invalid event: {event}")
        if callback in self.subscribers[event]:
            self.subscribers[event].remove(callback)

    async def notify(self, event: int, *args, **kwargs):
        if event not in self.subscribers:
            raise ValueError(f"Invalid event: {event}")
        for callback in self.subscribers[event]:
            r = callback(*args, **kwargs)
            if isinstance(r, Coroutine):
                await r


class ActionContext:
    def __init__(
        self,
        *,
        app,
        log: ActionLog,
        events: EventController,
        game_id: int,
        action_id: int | None = None,
    ):
        self.app = app
        self.log = log
        self.events = events
        self.games: dict[int, Game] = self.app.games
        self.game_id: int = game_id
        self.game: Game = self.games[game_id]
        if action_id is not None:
            self.action_id: int = action_id
        elif self.game:
            self.action_id: int = self.game.action_id

    def copy(self, **kwargs):
        return ActionContext(
            app=kwargs.get("app", self.app),
            log=kwargs.get("log", self.log),
            events=kwargs.get("events", self.events),
            game_id=kwargs.get("game_id", self.game_id),
            action_id=kwargs.get("action_id", self.action_id),
        )
