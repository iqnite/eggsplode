"""
Contains the DefuseView class, which handles the defuse interaction in the game.
"""

from collections.abc import Callable, Coroutine
import discord
from strings import MESSAGES
from game_logic import ActionContext
from .base_view import BaseView


class DefuseView(BaseView):
    """
    A view that allows players to interact with the defuse action in the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
        callback_action (callable): The function to execute after finishing the interaction.
        eggsplode_position (int): The position of the "eggsplode" card in the deck.
    """

    def __init__(self, ctx: ActionContext, callback_action: Callable[[], Coroutine]):
        """
        Initializes the DefuseView with the given context and callback action.

        Args:
            ctx (ActionContext): The context of the current action.
            callback_action (callable): The function to execute after finishing the interaction.
        """
        super().__init__(ctx, timeout=10)
        self.callback_action = callback_action
        self.eggsplode_position = 0

    async def finish(self):
        """
        Inserts the "eggsplode" card back into the deck and disables all interaction items.
        """
        self.ctx.game.deck.insert(self.eggsplode_position, "eggsplode")
        await self.callback_action()

    async def on_timeout(self):
        """
        Handles the timeout event by finishing the interaction.
        """
        await self.finish()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the confirm button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        self.disable_all_items()
        await interaction.edit(view=self)
        await self.finish()

    @discord.ui.button(label="Move up", style=discord.ButtonStyle.blurple, emoji="⬆️")
    async def move_up(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the move up button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if self.eggsplode_position > 0:
            self.eggsplode_position -= 1
        else:
            self.eggsplode_position = len(self.ctx.game.deck)
        await self.update_view(interaction)

    @discord.ui.button(label="Move down", style=discord.ButtonStyle.blurple, emoji="⬇️")
    async def move_down(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the move down button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if self.eggsplode_position < len(self.ctx.game.deck):
            self.eggsplode_position += 1
        else:
            self.eggsplode_position = 0
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        """
        Updates the view with the current state of the defuse interaction.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.edit(
            content=MESSAGES["defuse_prompt"].format(
                self.eggsplode_position,
                "\n".join(
                    MESSAGES["players_list_item"].format(player)
                    for player in self.ctx.game.players
                ),
            ),
            view=self,
        )
