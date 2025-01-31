"""
Contains the NopeView class, which handles the interaction logic for "Nopeable" actions.
"""

from collections.abc import Callable, Coroutine
import discord
from strings import MESSAGES
from game_logic import ActionContext
from .base_view import BaseView


class NopeView(BaseView):
    """
    A view that handles the "Nope" and "OK" button interactions in the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
        target_player_id (int): The ID of the target player.
        callback_action (function): The callback function to be called after the interaction.
        nopes (int): The count of "Nope" interactions.
    """

    def __init__(
        self,
        ctx: ActionContext,
        target_player_id: int,
        callback_action: Callable[[discord.Interaction | None], Coroutine],
    ):
        """
        Initializes the NopeView with the given context, target player ID, and callback action.

        Args:
            ctx (ActionContext): The context of the current action.
            target_player_id (int): The ID of the target player.
            callback_action (function): The callback function to be called after the interaction.
        """
        super().__init__(ctx, timeout=10)
        self.ctx.game.awaiting_prompt = True
        self.target_player = target_player_id
        self.callback_action = callback_action
        self.nopes = 0

    async def on_timeout(self):
        """
        Handles the timeout event for the view.
        """
        if self.ctx.action_id == self.ctx.game.action_id:
            self.ctx.game.awaiting_prompt = False
            if not self.nopes % 2:
                await self.callback_action(None)
        await super().on_timeout()

    @discord.ui.button(label="OK!", style=discord.ButtonStyle.green, emoji="✅")
    async def ok_callback(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the "OK" button interaction.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if not interaction.user:
            return
        if interaction.user.id != self.target_player:
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return
        if self.nopes % 2:
            await interaction.respond(MESSAGES["action_noped"], ephemeral=True)
            return
        self.on_timeout = super().on_timeout
        self.disable_all_items()
        await interaction.edit(view=self)
        self.ctx.game.awaiting_prompt = False
        await self.callback_action(interaction)

    @discord.ui.button(label="Nope!", style=discord.ButtonStyle.red, emoji="🛑")
    async def nope_callback(
        self, _: discord.ui.Button, interaction: discord.Interaction
    ):
        """
        Handles the "Nope" button interaction.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if not interaction.user:
            return
        if (
            not self.nopes % 2
            and self.ctx.game.current_player_id == interaction.user.id
        ):
            await interaction.respond(MESSAGES["no_self_nope"], ephemeral=True)
            return
        if interaction.user.id not in self.ctx.game.players:
            await interaction.respond(MESSAGES["user_not_in_game"], ephemeral=True)
            return
        try:
            self.ctx.game.hands[interaction.user.id].remove("nope")
        except ValueError:
            await interaction.respond(MESSAGES["no_nope_cards"], ephemeral=True)
            return
        if not interaction.message:
            return
        self.nopes += 1
        new_message_content = "".join(
            (line.strip("~~") + "\n" if line.startswith("~~") else "~~" + line + "~~\n")
            for line in interaction.message.content.split("\n")
        ) + (
            MESSAGES["message_edit_on_nope"].format(interaction.user.id)
            if self.nopes % 2
            else MESSAGES["message_edit_on_yup"].format(interaction.user.id)
        )
        await interaction.edit(content=new_message_content, view=self)
