"""
Contains the commands for the Eggsplode game.
"""

from datetime import datetime
import discord
from discord.ext import commands


from .game_logic import Game
from .strings import VERSION, get_message
from .views.starter import HelpView


class EggsplodeApp(commands.Bot):  # pylint: disable=too-many-ancestors
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin_maintenance: bool = False
        self.games: dict[int, Game] = {}
        self.load_extension("eggsplode.cogs.eggsplode_game")
        self.load_extension("eggsplode.cogs.mini_games")
        self.load_extension("eggsplode.cogs.misc")

    def games_with_user(self, user_id: int) -> list[int]:
        return [i for i, game in self.games.items() if user_id in game.players]

    def cleanup(self):
        for game_id in list(self.games):
            if (
                datetime.now() - self.games[game_id].last_activity
            ).total_seconds() > 1800:
                del self.games[game_id]

    async def show_help(
        self, ctx: discord.ApplicationContext | discord.Interaction, ephemeral=False
    ):
        await ctx.respond(
            get_message("help0")
            + "\n"
            + get_message("status").format(
                self.latency * 1000,
                VERSION,
                get_message("maintenance") if self.admin_maintenance else "",
            ),
            view=HelpView(),
            ephemeral=ephemeral,
        )
