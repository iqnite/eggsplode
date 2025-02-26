"""
Eggsplode Discord Bot Application

This module contains the main application logic for the Eggsplode Discord bot.
"""

import asyncio
from datetime import datetime
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands
from strings import MESSAGES, VERSION
from game_logic import Game, ActionContext
from views.start_game_view import StartGameView


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


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOG_PATH = os.getenv("LOG_PATH")
RESTART_CMD = os.getenv("RESTART_CMD")
ADMIN_MAINTENANCE_CODE = os.getenv("ADMIN_MAINTENANCE_CODE")
ADMIN_LISTGAMES_CODE = os.getenv("ADMIN_LISTGAMES_CODE")
if not DISCORD_TOKEN:
    raise TypeError("DISCORD_TOKEN must be set in .env file. ")
eggsplode_app = Eggsplode(
    activity=discord.Activity(type=discord.ActivityType.watching, name="you")
)

logger = logging.getLogger("discord")
if LOG_PATH:
    handler = RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    sys.excepthook = logger.error


def games_with_user(user_id: int) -> list[int]:
    """
    Get a list of game IDs that the user is participating in.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list: A list of game IDs.
    """
    return [i for i, game in eggsplode_app.games.items() if user_id in game.players]


def cleanup():
    """
    Delete games that have been inactive for 30 minutes.
    """
    for game_id in list(eggsplode_app.games):
        if (datetime.now() - eggsplode_app.games[game_id].last_activity).total_seconds() > 1800:
            del eggsplode_app.games[game_id]


@eggsplode_app.slash_command(
    name="start",
    description="Start a new Eggsplode game!",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def start(ctx: discord.ApplicationContext):
    """
    Start a new Eggsplode game.

    Args:
        ctx (discord.ApplicationContext): The context of the command.
    """
    await ctx.response.defer()
    cleanup()
    if eggsplode_app.admin_maintenance:
        await ctx.respond(MESSAGES["maintenance"], ephemeral=True)
        return
    game_id = ctx.interaction.channel_id
    if not (game_id and ctx.interaction.user):
        return
    if game_id in eggsplode_app.games:
        await ctx.respond(MESSAGES["game_already_exists"], ephemeral=True)
        return
    eggsplode_app.games[game_id] = Game(ctx.interaction.user.id)
    await ctx.respond(
        MESSAGES["start"].format(ctx.interaction.user.id, ctx.interaction.user.id),
        view=StartGameView(ActionContext(app=eggsplode_app, game_id=game_id)),
    )


@eggsplode_app.slash_command(
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
    await ctx.response.defer()
    game_id = ctx.interaction.channel_id
    if not (game_id and ctx.interaction.user):
        return
    if game_id not in eggsplode_app.games:
        await ctx.respond(MESSAGES["game_not_found"], ephemeral=True)
        return
    if ctx.interaction.user.id not in eggsplode_app.games[game_id].players:
        await ctx.respond(MESSAGES["user_not_in_game"], ephemeral=True)
        return
    if not eggsplode_app.games[game_id].hands:
        await ctx.respond(MESSAGES["game_not_started"], ephemeral=True)
        return
    await ctx.respond(
        MESSAGES["hand_title"].format(
            eggsplode_app.games[game_id].cards_help(
                ctx.interaction.user.id, template=MESSAGES["hand_list"]
            )
        ),
        ephemeral=True,
    )


@eggsplode_app.slash_command(
    name="games",
    description="View which games you're in.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def games(ctx: discord.ApplicationContext):
    """
    View the games the user is participating in.

    Args:
        ctx (discord.ApplicationContext): The context of the command.
    """
    await ctx.response.defer()
    cleanup()
    if not ctx.interaction.user:
        return
    found_games = games_with_user(ctx.interaction.user.id)
    await ctx.respond(
        (
            MESSAGES["list_games_title"].format(
                "\n".join(MESSAGES["list_games_item"].format(i) for i in found_games)
            )
            if found_games
            else MESSAGES["user_not_in_any_games"]
        ),
        ephemeral=True,
    )


@eggsplode_app.slash_command(
    name="help",
    description="Learn how to play Eggsplode and view useful info!",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def show_help(ctx: discord.ApplicationContext):
    """
    Show help information for the Eggsplode game.

    Args:
        ctx (discord.ApplicationContext): The context of the command.
    """
    await ctx.response.defer()
    await ctx.respond(
        "\n".join(MESSAGES["help"]).format(
            eggsplode_app.latency * 1000,
            VERSION,
            MESSAGES["maintenance"] if eggsplode_app.admin_maintenance else "",
        )
    )


@eggsplode_app.slash_command(
    name="bugreport",
    description="Report a bug to the Eggsplode developers.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
@discord.option(
    "bug_type",
    type=str,
    description="The type of bug you're reporting.",
    required=True,
    autocomplete=lambda _: [
        "Eggsplode is lagging or does not respond.",
        "It's my turn, but it says that it's not valid.",
        "I can't play or draw a card.",
        "A card is not working as expected.",
        "I can't start a game, even if there are no other games in the current channel.",
        "Something else (please describe).",
    ],
)
@discord.option(
    "description",
    type=str,
    description="Please describe your bug. Provide as many details as possible.",
    required=True,
)
async def bugreport(ctx: discord.ApplicationContext, bug_type: str, description: str):
    """
    Report a bug to the developers.

    Args:
        ctx (discord.ApplicationContext): The context of the command.
        bug_type (str): The type of bug being reported.
        description (str): A detailed description of the bug.
    """
    await ctx.response.defer()
    if not ctx.interaction.user:
        return
    logger.info(
        MESSAGES["bug_report_print"].format(
            ctx.interaction.user.id, ctx.interaction.channel_id, bug_type, description
        )
    )
    await ctx.respond(MESSAGES["bug_reported"], ephemeral=True)


@eggsplode_app.slash_command(
    name="admincmd",
    description="Staff only.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
@discord.option(
    "command",
    type=str,
    description="If you don't know any command, you're not an admin.",
    required=True,
)
async def admincmd(
    ctx: discord.ApplicationContext,
    command: str,
):
    """
    Execute an admin command.

    Args:
        ctx (discord.ApplicationContext): The context of the command.
        command (str): The admin command to execute.
    """
    await ctx.response.defer()
    if command == ADMIN_MAINTENANCE_CODE:
        cleanup()
        eggsplode_app.admin_maintenance = not eggsplode_app.admin_maintenance
        await ctx.respond(
            MESSAGES["maintenance_mode_toggle"].format(
                "enabled" if eggsplode_app.admin_maintenance else "disabled",
                (
                    MESSAGES["maintenance_mode_no_games_running"]
                    if not eggsplode_app.games
                    else ""
                ),
            ),
            ephemeral=True,
        )
        while eggsplode_app.games and eggsplode_app.admin_maintenance:
            await asyncio.sleep(10)
        if RESTART_CMD and eggsplode_app.admin_maintenance:
            if LOG_PATH:
                logger.info("RESTARTING VIA ADMIN COMMAND")
            else:
                print("RESTARING VIA ADMIN COMMAND")
            os.system(RESTART_CMD)
    elif command == ADMIN_LISTGAMES_CODE:
        await ctx.respond(
            MESSAGES["list_games_title"].format(
                "\n".join(f"- {i}" for i in eggsplode_app.games)
            ),
            ephemeral=True,
        )
    else:
        await ctx.respond(MESSAGES["invalid_command"], ephemeral=True)


if __name__ == "__main__":
    if LOG_PATH:
        logger.info("PROGRAM STARTED!")
    else:
        print("PROGRAM STARTED!")
    eggsplode_app.run(DISCORD_TOKEN)
