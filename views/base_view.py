"""
Contains the BaseView class which is used to create a Discord UI view for the game.
"""

import discord
from strings import MESSAGES
from game_logic import ActionContext


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

    def default_message(self, user_id: int) -> str:
        """
        Generates the default message to be displayed to the user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            str: The formatted message to be displayed.
        """
        return MESSAGES["play_prompt"].format(
            self.ctx.game.cards_help(user_id, template=MESSAGES["hand_list"]),
            len(self.ctx.game.deck),
            self.ctx.game.deck.count("eggsplode"),
        )
