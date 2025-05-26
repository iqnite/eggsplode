"""
Contains the BaseView class for the Eggsplode game.
"""

from typing import TYPE_CHECKING
import discord

if TYPE_CHECKING:
    from eggsplode.core import Game


class BaseView(discord.ui.View):
    def __init__(self, game: "Game", timeout=None):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.game = game
        self.game.events.game_end += self.stop

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await super().interaction_check(interaction):
            return False
        await interaction.response.defer(invisible=True)
        return True
