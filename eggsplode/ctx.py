"""
Contains the context classes for the game actions.
"""

from collections.abc import Callable, Coroutine
from typing import Generator

import discord

from .game_logic import Game
from .strings import get_message


class ActionContext:  # pylint: disable=too-few-public-methods
    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        app,
        game_id: int,
        action_id: int | None = None,
    ):
        self.app = app
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
            game_id=kwargs.get("game_id", self.game_id),
            action_id=kwargs.get("action_id", self.action_id),
        )


class PlayActionContext(ActionContext):
    def __init__(
        self,
        disable_view: Callable[[discord.Interaction], Coroutine],
        update_view: Callable[[discord.Interaction], Coroutine],
        end_turn: Callable[[discord.Interaction], Coroutine],
        on_game_over: Callable[[], None],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.disable_view = disable_view
        self.update_view = update_view
        self.end_turn = end_turn
        self.on_game_over = on_game_over

    @classmethod
    def from_ctx(
        cls,
        ctx: ActionContext,
        *,
        disable_view,
        update_view,
        end_turn,
        on_game_over,
    ):
        return cls(
            app=ctx.app,
            game_id=ctx.game_id,
            action_id=ctx.action_id,
            disable_view=disable_view,
            update_view=update_view,
            end_turn=end_turn,
            on_game_over=on_game_over,
        )

    def copy(self, **kwargs):
        return PlayActionContext(
            app=kwargs.get("app", self.app),
            game_id=kwargs.get("game_id", self.game_id),
            action_id=kwargs.get("action_id", self.action_id),
            disable_view=kwargs.get("disable_view", self.disable_view),
            update_view=kwargs.get("update_view", self.update_view),
            end_turn=kwargs.get("end_turn", self.end_turn),
            on_game_over=kwargs.get("on_game_over", self.on_game_over),
        )


class ActionLog:
    def __init__(self, actions, character_limit: int | None = 2000):
        self._actions: list[str] = list(actions)
        self.character_limit = character_limit

    def add(self, action: str):
        self._actions.append(action)

    def clear(self):
        self._actions.clear()

    @property
    def amount_of_pages(self) -> int:
        return 1 + sum(1 for _ in self.pages)

    @property
    def pages(self):
        if self.character_limit is None:
            yield str(self)
            return
        from_line = 0
        to_line = 0
        total_characters = 0
        while to_line < len(self._actions):
            action = self[to_line]
            total_characters += len(action)
            if total_characters > self.character_limit:
                yield "\n".join(self[from_line:to_line])
                from_line = to_line
                total_characters = 0
                continue
            to_line += 1

    def __str__(self):
        return "\n".join(get_message(action) for action in self._actions)

    def __len__(self):
        return len(self._actions)

    def __iter__(self):
        for i, _ in enumerate(self._actions):
            yield self[i]

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [get_message(action) for action in self._actions[index]]
        return get_message(self._actions[index])
