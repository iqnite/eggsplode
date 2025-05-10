"""
Contains the commands for the Eggsplode game.
"""

from datetime import datetime
import discord
from discord.ext import commands
from eggsplode.core import Game
from eggsplode.strings import INFO, get_message
from eggsplode.start import HelpView, StartGameView


class EggsplodeApp(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin_maintenance: bool = False
        self.games: dict[int, Game] = {}
        self.load_extension("eggsplode.cogs.eggsplode_game")
        self.load_extension("eggsplode.cogs.mini_games")
        self.load_extension("eggsplode.cogs.misc")
        self.load_extension("eggsplode.cogs.owner")

    async def on_ready(self):
        print("APP READY!")

    def games_with_user(self, user_id: int) -> list[int]:
        return [i for i, game in self.games.items() if user_id in game.players]

    def cleanup(self):
        for game_id in list(self.games):
            if (
                datetime.now() - self.games[game_id].last_activity
            ).total_seconds() > 1800:
                del self.games[game_id]

    async def start_game(self, interaction: discord.Interaction, config=None):
        self.cleanup()
        if self.admin_maintenance:
            await interaction.respond(get_message("maintenance"), ephemeral=True)
            return
        game_id = interaction.channel_id
        if not (game_id and interaction.user):
            return
        if self.games.get(game_id, None):
            await interaction.respond(
                get_message("game_already_exists"), ephemeral=True
            )
            return
        await interaction.response.defer()
        game = self.games[game_id] = Game(
            self,
            (
                {
                    "players": [interaction.user.id],
                }
                if config is None
                else config
            ),
        )
        game.log.anchor_interaction = interaction
        view = StartGameView(game)
        await interaction.respond(view=view)

    async def show_help(self, interaction: discord.Interaction, ephemeral=False):
        await interaction.respond(
            get_message("help0")
            + "\n"
            + get_message("status").format(
                self.latency * 1000,
                INFO["version"],
                get_message("maintenance") if self.admin_maintenance else "",
            ),
            view=HelpView(),
            ephemeral=ephemeral,
        )
