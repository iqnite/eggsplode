"""
Eggsplode Discord Bot
"""

import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from common import MESSAGES
from game_logic import Game, ActionContext
from views import StartGameView, TurnView


class Eggsplode(commands.Bot):  # pylint: disable=too-many-ancestors
    """
    Represents the Eggsplode bot.

    Attributes:
        admin_maintenance (bool): Whether the bot is in maintenance mode.
        games (dict[int, Game]): Dictionary of active games.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Eggsplode bot.

        Args:
            kwargs: Additional keyword arguments.
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
    Starts a new Eggsplode game.

    Args:
        ctx (discord.ApplicationContext): The application context.
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


def games_with_user(user_id):
    """
    Returns a list of games that the user is in.

    Args:
        user_id (int): The user ID.

    Returns:
        list[int]: List of games.
    """
    return [i for i, game in eggsplode_app.games.items() if user_id in game.players]


async def game_id_autocomplete(ctx: discord.AutocompleteContext):
    """
    Autocompletes the game ID for the user.

    Args:
        ctx (discord.AutocompleteContext): The autocomplete context.

    Returns:
        list[str]: List of game IDs.
    """
    return (
        map(str, games_with_user(ctx.interaction.user.id))
        if ctx.interaction.user
        else []
    )


@eggsplode_app.slash_command(
    name="play",
    description="Play your turn.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def play(ctx: discord.ApplicationContext):
    """
    Plays the user's turn.

    Args:
        ctx (discord.ApplicationContext): The application context.
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
    view = TurnView(ActionContext(app=eggsplode_app, game_id=game_id))
    await ctx.respond(
        MESSAGES["turn_prompt"].format(
            eggsplode_app.games[game_id].cards_help(
                ctx.interaction.user.id, template=MESSAGES["hand_list"]
            )
        ),
        view=view,
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
    Views the user's games.

    Args:
        ctx (discord.ApplicationContext): The application context.
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
    Shows the help message.

    Args:
        ctx (discord.ApplicationContext): The application context.
    """
    await ctx.respond("\n".join(MESSAGES["help"]))


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
    Checks if the Eggsplode bot is online.

    Args:
        ctx (discord.ApplicationContext): The application context.
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
    Executes an admin command.

    Args:
        ctx (discord.ApplicationContext): The application context.
        command (str): The admin command.
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
