"""
Contains the commands for the Eggsplode game.
"""

from datetime import datetime
import logging
import discord
from discord.ext import commands
from eggsplode.core import Game
from eggsplode.ui import StartGameView
from eggsplode.ui.base import TextView


class EggsplodeApp(commands.Bot):
    def __init__(self, logger: logging.Logger, **kwargs):
        super().__init__(**kwargs)
        self.admin_maintenance: bool = False
        self.games: dict[int, Game] = {}
        self.logger = logger
        self.load_extension("eggsplode.cogs.eggsplode_game")
        self.load_extension("eggsplode.cogs.misc")
        self.load_extension("eggsplode.cogs.owner")

    async def on_ready(self):
        self.logger.info("App ready!")

    def games_with_user(self, user_id: int) -> list[int]:
        return [
            i
            for i, game in self.games.items()
            if user_id in game.players + list(game.config.get("players", []))
            and game.active
        ]

    def cleanup(self):
        for game_id in list(self.games):
            if (
                datetime.now() - self.games[game_id].last_activity
            ).total_seconds() > 1800:
                del self.games[game_id]
                self.logger.info(f"Cleaned up game {game_id}.")

    @property
    def game_count(self) -> int:
        count = 0
        for game in self.games.values():
            if game and game.active:
                count += 1
        return count

    async def create_game(self, interaction: discord.Interaction, config=None):
        self.cleanup()
        if self.admin_maintenance:
            await interaction.respond(view=TextView("maintenance"), ephemeral=True)
            return
        game_id = interaction.channel_id
        if not (game_id and interaction.user):
            return
        if self.games.get(game_id, None):
            await interaction.respond(
                view=TextView("game_already_exists"), ephemeral=True
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
            game_id=game_id,
        )
        game.anchor_interaction = interaction
        self.logger.info(f"Game created: {game_id}")
        view = StartGameView(game)
        await interaction.respond(view=view)
