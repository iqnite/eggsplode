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


class ActionContext:
    def __init__(
        self,
        *,
        app,
        log: ActionLog,
        game_id: int,
        action_id: int | None = None,
    ):
        self.app = app
        self.log = log
        self.events = EventSet()
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
            game_id=kwargs.get("game_id", self.game_id),
            action_id=kwargs.get("action_id", self.action_id),
        )
