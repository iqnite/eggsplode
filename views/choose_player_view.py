"""
Contains the ChoosePlayerView class, which handles the UI for selecting a player.
"""

from collections.abc import Callable, Coroutine
import discord
from game_logic import ActionContext
from .base_view import BaseView


class ChoosePlayerView(BaseView):
    """
    A view that allows the current player to choose another player from the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
        callback_action (function): The callback function to execute after a player is selected.
        eligible_players (list): List of player IDs eligible for selection.
        user_select (discord.ui.Select): The select menu for choosing a player.
    """

    def __init__(self, ctx: ActionContext, callback_action: Callable[[int], Coroutine]):
        """
        Initializes the ChoosePlayerView with the given context and callback action.

        Args:
            ctx (ActionContext): The context of the current action.
            callback_action (function): The callback function to execute after a player is selected.
        """
        super().__init__(ctx, timeout=10)
        self.ctx.game.awaiting_prompt = True
        self.eligible_players = self.ctx.game.players.copy()
        self.eligible_players.remove(self.ctx.game.current_player_id)
        self.callback_action = callback_action
        self.user_select = None

    async def on_timeout(self):
        """
        Handles the timeout event for the view.
        """
        if not self.user_select:
            return
        try:
            await super().on_timeout()
        finally:
            await self.callback_action(int(self.user_select.options[0].value))

    async def create_user_selection(self):
        """
        Creates the user selection menu with eligible players.
        """
        options = []
        for user_id in self.eligible_players:
            user = await self.ctx.app.get_or_fetch_user(user_id)
            if not user:
                continue
            if not self.ctx.game.hands[user_id]:
                continue
            options.append(
                discord.SelectOption(
                    value=str(user_id),
                    label=f"{user.display_name} ({len(self.ctx.game.hands[user_id])} cards)",
                )
            )
        self.user_select = discord.ui.Select(
            placeholder="Select another player",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user_select.callback = self.selection_callback
        self.add_item(self.user_select)

    async def selection_callback(self, interaction: discord.Interaction):
        """
        Handles the selection of a player from the user selection menu.

        Args:
            interaction (Interaction): The interaction object representing the user's action.
        """
        if not (interaction and self.user_select):
            return
        self.on_timeout = super().on_timeout
        self.disable_all_items()
        await interaction.edit(view=self)
        if not isinstance(self.user_select.values[0], str):
            raise TypeError("user_select.values[0] is not a str")
        await self.callback_action(int(self.user_select.values[0]))
