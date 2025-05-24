"""
Contains the TurnView class, which provides buttons to take actions.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.base_view import BaseView
from eggsplode.selections import PlayView
from eggsplode.strings import get_message

if TYPE_CHECKING:
    from eggsplode.core import Game


class TurnView(BaseView):
    def __init__(self, game: "Game"):
        super().__init__(game)
        self.turn_prompt = discord.ui.TextDisplay(game.turn_prompt)
        self.add_item(self.turn_prompt)
        self.play_button = discord.ui.Button(
            label="Play a card", style=discord.ButtonStyle.primary, emoji="🎴"
        )
        self.play_button.callback = self.play_callback
        self.add_item(self.play_button)
        self.draw_button = discord.ui.Button(
            label="Draw", style=discord.ButtonStyle.secondary, emoji="🤚"
        )
        self.draw_button.callback = self.draw_callback
        self.add_item(self.draw_button)
        self.warnings = discord.ui.TextDisplay(self.game.warnings)
        self.add_item(self.warnings)
        self.game.events.turn_end.subscribe(self.deactivate, 0)
        self.game.events.game_end.subscribe(self.deactivate, 0)

    async def interaction_check(self, interaction: discord.Interaction):
        if not await super().interaction_check(interaction):
            return False
        if not interaction.user:
            raise TypeError("interaction.user is None")
        if interaction.user.id != self.game.current_player_id:
            await interaction.respond(
                get_message("not_your_turn"), ephemeral=True, delete_after=5
            )
            return False
        if self.game.paused:
            await interaction.respond(
                get_message("awaiting_prompt"), ephemeral=True, delete_after=5
            )
            return False
        self.game.anchor_interaction = interaction
        self.game.inactivity_count = 0
        return True

    async def draw_callback(self, interaction: discord.Interaction):
        await self.game.events.action_start()
        _, hold = await self.game.draw_from(interaction)
        if hold:
            await self.game.events.turn_end()

    async def play_callback(self, interaction: discord.Interaction):
        view = PlayView(self.game)
        await interaction.respond(view=view, ephemeral=True)
        await self.game.events.turn_reset()

    async def deactivate(self):
        self.stop()
        self.disable_all_items()
        self.game.events.turn_end.unsubscribe(self.deactivate)
        for item in (self.draw_button, self.play_button, self.warnings):
            self.remove_item(item)
        if self.game.anchor_interaction:
            await self.game.anchor_interaction.edit_original_response(view=self)
