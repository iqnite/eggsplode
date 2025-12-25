"""
Contains the TurnView class, which provides buttons to take actions.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.ui.base import BaseGameView

if TYPE_CHECKING:
    from eggsplode.core import Game


class TurnView(BaseGameView):
    def __init__(self, game: "Game"):
        super().__init__(game)
        self.turn_prompt = discord.ui.TextDisplay(game.turn_prompt)
        self.add_item(self.turn_prompt)
        self.play_button = discord.ui.Button(
            label="Play a card", style=discord.ButtonStyle.primary, emoji="🎴"
        )
        self.play_button.callback = self.game.show_hand
        self.draw_button = discord.ui.Button(
            label="Draw", style=discord.ButtonStyle.secondary, emoji="🤚"
        )
        self.draw_button.callback = self.game.draw_callback
        self.action_row = discord.ui.ActionRow(self.play_button, self.draw_button)
        self.add_item(self.action_row)
        self.warnings = discord.ui.TextDisplay(self.game.warnings)
        self.add_item(self.warnings)
        self.game.events.turn_end.subscribe(self.deactivate, index=0)
        self.game.events.game_end.subscribe(self.deactivate, index=0)

    async def interaction_check(self, interaction: discord.Interaction):
        if not await super().interaction_check(interaction):
            return False
        self.game.last_interaction = interaction
        self.game.inactivity_count = 0
        return True

    async def deactivate(self):
        self.stop()
        self.game.events.turn_end -= self.deactivate
        self.game.events.game_end -= self.deactivate
