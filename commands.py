"""
Contains the commands for the Eggsplode game.
"""

import asyncio
from datetime import datetime
import os
import discord
from discord.ext import commands
from game_logic import ActionContext, Game
from strings import (
    ADMIN_LISTGAMES_CODE,
    ADMIN_MAINTENANCE_CODE,
    MESSAGES,
    RESTART_CMD,
    VERSION,
)
from views.starter import StartGameView, HelpView


class Eggsplode(commands.Bot):  # pylint: disable=too-many-ancestors
    """
    A subclass of commands.Bot for the Eggsplode game.

    Attributes:
        admin_maintenance (bool): Indicates if the bot is in maintenance mode.
        games (dict[int, Game]): A dictionary of active games.
    """

    def __init__(self, **kwargs):
        """
        Initialize the Eggsplode bot.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the superclass.
        """
        super().__init__(**kwargs)
        self.admin_maintenance: bool = False
        self.games: dict[int, Game] = {}
        self.create_commands()

    def games_with_user(self, user_id: int) -> list[int]:
        """
        Get a list of game IDs that the user is participating in.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of game IDs.
        """
        return [i for i, game in self.games.items() if user_id in game.players]

    def cleanup(self):
        """
        Delete games that have been inactive for 30 minutes.
        """
        for game_id in list(self.games):
            if (
                datetime.now() - self.games[game_id].last_activity
            ).total_seconds() > 1800:
                del self.games[game_id]

    async def show_help(
        self, ctx: discord.ApplicationContext | discord.Interaction, ephemeral=False
    ):
        """
        Show help information for the Eggsplode game.

        Args:
            ctx (discord.ApplicationContext): The context of the command.
        """
        await ctx.respond(
            "\n".join(MESSAGES["help"]).format(
                self.latency * 1000,
                VERSION,
                MESSAGES["maintenance"] if self.admin_maintenance else "",
            ),
            view=HelpView(),
            ephemeral=ephemeral,
        )

    def create_commands(self):
        """
        Create the commands for the Eggsplode game.
        """

        @self.slash_command(
            name="start",
            description="Start a new Eggsplode game!",
            integration_types={
                discord.IntegrationType.guild_install,
                discord.IntegrationType.user_install,
            },
        )
        async def start_game(ctx: discord.ApplicationContext):
            """
            Start a new Eggsplode game.

            Args:
                ctx (discord.ApplicationContext): The context of the command.
            """
            self.cleanup()
            if self.admin_maintenance:
                await ctx.respond(MESSAGES["maintenance"], ephemeral=True)
                return
            game_id = ctx.interaction.channel_id
            if not (game_id and ctx.interaction.user):
                return
            if game_id in self.games:
                await ctx.respond(MESSAGES["game_already_exists"], ephemeral=True)
                return
            self.games[game_id] = Game(
                {
                    "players": [ctx.interaction.user.id],
                }
            )
            async with StartGameView(ActionContext(app=self, game_id=game_id)) as view:
                view.message = await ctx.respond(
                    "\n".join(
                        (
                            MESSAGES["start"].format(ctx.interaction.user.id),
                            MESSAGES["players"],
                            MESSAGES["players_list_item"].format(
                                ctx.interaction.user.id
                            ),
                        )
                    ),
                    view=view,
                )

        @self.slash_command(
            name="hand",
            description="View your hand.",
            integration_types={
                discord.IntegrationType.guild_install,
                discord.IntegrationType.user_install,
            },
        )
        async def hand(ctx: discord.ApplicationContext):
            """
            View the user's hand in the current game.

            Args:
                ctx (discord.ApplicationContext): The context of the command.
            """
            game_id = ctx.interaction.channel_id
            if not (game_id and ctx.interaction.user):
                return
            if game_id not in self.games:
                await ctx.respond(MESSAGES["game_not_found"], ephemeral=True)
                return
            if ctx.interaction.user.id not in self.games[game_id].players:
                await ctx.respond(MESSAGES["user_not_in_game"], ephemeral=True)
                return
            if not self.games[game_id].hands:
                await ctx.respond(MESSAGES["game_not_started"], ephemeral=True)
                return
            await ctx.respond(
                MESSAGES["hand_title"].format(
                    self.games[game_id].cards_help(
                        ctx.interaction.user.id, template=MESSAGES["hand_list"]
                    )
                ),
                ephemeral=True,
            )

        @self.slash_command(
            name="games",
            description="View which games you're in.",
            integration_types={
                discord.IntegrationType.guild_install,
                discord.IntegrationType.user_install,
            },
        )
        async def list_user_games(ctx: discord.ApplicationContext):
            """
            View the games the user is participating in.

            Args:
                ctx (discord.ApplicationContext): The context of the command.
            """
            self.cleanup()
            if not ctx.interaction.user:
                return
            found_games = self.games_with_user(ctx.interaction.user.id)
            await ctx.respond(
                (
                    MESSAGES["list_games_title"].format(
                        "\n".join(
                            MESSAGES["list_games_item"].format(i) for i in found_games
                        )
                    )
                    if found_games
                    else MESSAGES["user_not_in_any_games"]
                ),
                ephemeral=True,
            )

        @self.slash_command(
            name="help",
            description="Learn how to play Eggsplode and view useful info!",
            integration_types={
                discord.IntegrationType.guild_install,
                discord.IntegrationType.user_install,
            },
        )
        async def show_help_command(ctx: discord.ApplicationContext):
            """
            Show help information for the Eggsplode game.

            Args:
                ctx (discord.ApplicationContext): The context of the command.
            """
            await self.show_help(ctx)

        @self.slash_command(
            name="terminal",
            description="Staff only.",
            integration_types={
                discord.IntegrationType.guild_install,
                discord.IntegrationType.user_install,
            },
        )
        @discord.option(
            name="command",
            description="If you don't know any command, you're not an admin.",
            input_type=str,
            required=True,
        )
        async def terminal(ctx: discord.ApplicationContext, command: str):
            """
            Execute an admin command.

            Args:
                ctx (discord.ApplicationContext): The context of the command.
                command (str): The admin command to execute.
            """
            if command == ADMIN_MAINTENANCE_CODE:
                self.cleanup()
                self.admin_maintenance = not self.admin_maintenance
                await ctx.respond(
                    MESSAGES["maintenance_mode_toggle"].format(
                        "enabled" if self.admin_maintenance else "disabled",
                        (
                            MESSAGES["maintenance_mode_no_games_running"]
                            if not self.games
                            else ""
                        ),
                    ),
                    ephemeral=True,
                )
                while self.games and self.admin_maintenance:
                    await asyncio.sleep(10)
                if RESTART_CMD and self.admin_maintenance:
                    print("RESTARTING VIA ADMIN COMMAND")
                    os.system(RESTART_CMD)
            elif command == ADMIN_LISTGAMES_CODE:
                await ctx.respond(
                    MESSAGES["list_games_title"].format(
                        "\n".join(f"- {i}" for i in self.games)
                    ),
                    ephemeral=True,
                )
            else:
                await ctx.respond(MESSAGES["invalid_command"], ephemeral=True)
