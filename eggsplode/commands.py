"""
Contains the commands for the Eggsplode game.
"""

from datetime import datetime
import logging
import discord
from discord.ext import commands
from eggsplode.core import Game
from eggsplode.strings import GAME_TIMEOUT
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
        self.add_listener(self.ready, "on_ready")
        self.add_listener(self.handle_error, "on_error")
        self.add_listener(self.handle_view_error, "on_view_error")
        self.add_listener(self.handle_modal_error, "on_modal_error")
        self.add_listener(
            self.handle_application_command_error, "on_application_command_error"
        )

    async def ready(self):
        self.logger.info("App ready.")

    async def handle_error(self, event_method: str, *args, **kwargs) -> None:
        self.logger.exception(f"in {event_method}", exc_info=True)

    async def handle_view_error(
        self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction
    ) -> None:
        self.logger.exception(
            f"in view {item.view} item {item}: {error}", exc_info=error
        )

    async def handle_modal_error(
        self,
        error: Exception,
        modal: discord.ui.Modal,
        interaction: discord.Interaction,
    ) -> None:
        self.logger.exception(f"in modal {modal}: {error}", exc_info=error)

    async def handle_application_command_error(
        self, context: discord.ApplicationContext, exception: discord.DiscordException
    ) -> None:
        self.logger.exception(
            f"in command {context.command}: {exception}", exc_info=exception
        )

    def games_with_user(self, user_id: int) -> list[int]:
        return [
            i
            for i, game in self.games.items()
            if user_id in game.players + list(game.config.get("players", []))
            and game.active
        ]

    def remove_inactive_games(self):
        for game_id in list(self.games):
            if (
                datetime.now() - self.games[game_id].last_activity
            ).total_seconds() > GAME_TIMEOUT or not self.games[game_id].active:
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
        self.remove_inactive_games()
        if interaction.guild_id is None:
            await interaction.respond(view=TextView("dm_not_supported"), ephemeral=True)
            return
        if not interaction.is_guild_authorised():
            await interaction.respond(
                view=TextView("guild_not_authorised"), ephemeral=True
            )
            return
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
