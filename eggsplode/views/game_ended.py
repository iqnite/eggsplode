"""
Contains the view for the game end screen.
"""

import discord
from ..ctx import ActionContext
from .base import BaseView


class GameEndedView(BaseView):
    def __init__(self, ctx: ActionContext):
        super().__init__(ctx)
        self.ephemeral_full_log = False

    # FIXME:
    # @discord.ui.button(
    #     label="Play again", style=discord.ButtonStyle.blurple, emoji="🔁"
    # )
    # async def play_again(self, _: discord.ui.Button, interaction: discord.Interaction):
    #     await self.ctx.app.start_game(
    #         interaction, config=self.ctx.game.config
    #     )
