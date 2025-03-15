"""
Contains the BaseView class which is used to create a Discord UI view for the game.
"""

import discord
from ..game_logic import ActionContext


class BaseView(discord.ui.View):
    """
    A base view for the Discord UI used in the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
    """

    def __init__(self, ctx: ActionContext, timeout=600):
        """
        Initializes the BaseView with the given context and additional keyword arguments.

        Args:
            ctx (ActionContext): The context of the current action.
            **kwargs: Additional keyword arguments for the discord.ui.View.
        """
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.ctx = ctx

    async def __aenter__(self):
        """
        Enters the context manager.
        """
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Exits the context manager.

        Args:
            exc_type: The type of the exception that was raised
            exc_value: The instance of the exception that was raised
            traceback: The traceback of the exception
        """
