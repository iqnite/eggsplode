"""
Eggsplode Discord Bot Application

This module contains the main application logic for the Eggsplode Discord bot.
"""

import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from strings import MESSAGES
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
ADMIN_MAINTENANCE_CODE = os.getenv("ADMIN_MAINTENANCE_CODE")
ADMIN_LISTGAMES_CODE = os.getenv("ADMIN_LISTGAMES_CODE")
if not (DISCORD_TOKEN and ADMIN_MAINTENANCE_CODE and ADMIN_LISTGAMES_CODE):
    raise TypeError(
        "DISCORD_TOKEN, ADMIN_MAINTENANCE_CODE, and ADMIN_LISTGAMES_CODE must be set in .env file"
    )
eggsplode_app = Eggsplode(
    activity=discord.Activity(type=discord.ActivityType.watching, name="you")
)


def games_with_user(user_id: int) -> list[int]:
    """
    Get a list of game IDs that the user is participating in.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list: A list of game IDs.
    """
    return [i for i, game in eggsplode_app.games.items() if user_id in game.players]


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
    view = StartGameView(ActionContext(app=eggsplode_app, game_id=game_id))
    await ctx.respond(
        MESSAGES["start"].format(ctx.interaction.user.id, ctx.interaction.user.id),
        view=view,
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
    description="Learn how to play Eggsplode!",
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
    await ctx.respond("\n".join(MESSAGES["help"]))


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
    if not ctx.interaction.user:
        return
    print(
        MESSAGES["bug_report_print"].format(
            ctx.interaction.user.id, ctx.interaction.channel_id, bug_type, description
        )
    )
    await ctx.respond(MESSAGES["bug_reported"], ephemeral=True)


@eggsplode_app.slash_command(
    name="ping",
    description="Check if Eggsplode is online.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def ping(ctx: discord.ApplicationContext):
    """
    Check if the Eggsplode bot is online.

    Args:
        ctx (discord.ApplicationContext): The context of the command.
    """
    await ctx.respond(f"Pong! ({eggsplode_app.latency*1000:.0f}ms)")


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
    if command == ADMIN_MAINTENANCE_CODE:
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
    elif command == ADMIN_LISTGAMES_CODE:
        await ctx.respond(
            MESSAGES["list_games_title"].format(
                "\n".join(f"- {i}" for i in eggsplode_app.games)
            ),
            ephemeral=True,
        )
    else:
        await ctx.respond(MESSAGES["invalid_command"], ephemeral=True)


print("Hello, World!")
eggsplode_app.run(DISCORD_TOKEN)
