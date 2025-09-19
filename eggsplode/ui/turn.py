"""
Contains the TurnView class, which provides buttons to take actions.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.ui.base import BaseView

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
        self.play_button.callback = self.game.show_hand
        self.add_item(self.play_button)
        self.draw_button = discord.ui.Button(
            label="Draw", style=discord.ButtonStyle.secondary, emoji="🤚"
        )
        self.draw_button.callback = self.game.draw_callback
        self.add_item(self.draw_button)
        self.warnings = discord.ui.TextDisplay(self.game.warnings)
        self.add_item(self.warnings)
        self.game.events.turn_end.subscribe(self.deactivate, 0)
        self.game.events.game_end.subscribe(self.deactivate, 0)

    async def interaction_check(self, interaction: discord.Interaction):
        if not await super().interaction_check(interaction):
            return False
        self.game.anchor_interaction = interaction
        self.game.followup_count = 0  # Reset counter for new interaction
        self.game.inactivity_count = 0
        return True

    async def deactivate(self):
        self.stop()
        self.game.events.turn_end -= self.deactivate
        self.game.events.game_end -= self.deactivate
        # self.disable_all_items()
        # for item in (self.draw_button, self.play_button, self.warnings):
        #     self.remove_item(item)
        # if self.game.anchor_interaction:
        #     await self.game.anchor_interaction.edit_original_response(view=self)
