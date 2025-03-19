from collections.abc import Callable, Coroutine

import discord
from .game_logic import Game


class ActionContext:  # pylint: disable=too-few-public-methods
    """
    Represents the context for an action in the game.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        app,
        game_id: int,
        action_id: int | None = None,
    ):
        """
        Initializes the action context.

        Args:
            app: The application instance.
            game_id (int): The ID of the game.
            action_id (int, optional): The ID of the action.
        """
        self.app = app
        self.games: dict[int, Game] = self.app.games
        self.game_id: int = game_id
        self.game: Game = self.games[game_id]
        if action_id is not None:
            self.action_id: int = action_id
        elif self.game:
            self.action_id: int = self.game.action_id

    def copy(self, **kwargs):
        """
        Creates a copy of the action context with optional overrides.

        Args:
            **kwargs: Optional overrides for the context attributes.

        Returns:
            ActionContext: A new action context with the specified overrides.
        """
        return self.__class__(
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
        return self.__class__(
            app=kwargs.get("app", self.app),
            game_id=kwargs.get("game_id", self.game_id),
            action_id=kwargs.get("action_id", self.action_id),
            disable_view=kwargs.get("disable_view", self.disable_view),
            update_view=kwargs.get("update_view", self.update_view),
            end_turn=kwargs.get("end_turn", self.end_turn),
            on_game_over=kwargs.get("on_game_over", self.on_game_over),
        )
