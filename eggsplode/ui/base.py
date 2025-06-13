"""
Contains the BaseView class for the Eggsplode game.
"""

from typing import TYPE_CHECKING
import discord

from eggsplode.strings import format_message

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
        if interaction.user is None or interaction.user.id not in self.game.players:
            await interaction.response.send_message(
                format_message("user_not_in_game"), ephemeral=True
            )
            return False
        await interaction.response.defer(invisible=True)
        return True


class TextView(discord.ui.View):
    def __init__(self, key="", *format_args, text=""):
        super().__init__(
            discord.ui.TextDisplay(text or format_message(key, *format_args))
        )
