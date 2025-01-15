"""
Eggsplode Discord Bot
"""

import os
import json
from dotenv import load_dotenv
import discord
from game_logic import CARDS, Eggsplode, Game, StartGameView, TurnView, ActionContext

load_dotenv()
ADMIN_MAINTENANCE_CODE = os.getenv("ADMIN_MAINTENANCE_CODE")
ADMIN_LISTGAMES_CODE = os.getenv("ADMIN_LISTGAMES_CODE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
assert DISCORD_TOKEN is not None, "DISCORD_TOKEN is not set in .env file"
eggsplode_app = Eggsplode(
    activity=discord.Activity(type=discord.ActivityType.watching, name="you")
)
with open("messages.json", encoding="utf-8") as f:
    MESSAGES = json.load(f)


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
    assert ctx.interaction.user
    game_id = ctx.interaction.id
    view = StartGameView(eggsplode_app, game_id)
    eggsplode_app.games[game_id] = Game(ctx.interaction.user.id)
    await ctx.respond(
        MESSAGES["start"].format(
            game_id, ctx.interaction.user.id, ctx.interaction.user.id
        ),
        view=view,
    )


def games_with_user(user_id):
    """
    Returns a list of games that the user is in.

    Args:
        user_id (int): The user ID.

    Returns:
        list[Game]: List of games.
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
    if not ctx.interaction.user:
        return []
    return map(str, games_with_user(ctx.interaction.user.id))


@eggsplode_app.slash_command(
    name="play",
    description="Play your turn.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
@discord.option(
    "game_id",
    type=str,
    description="The game ID",
    required=False,
    default="",
    autocomplete=game_id_autocomplete,
)
async def play(
    ctx: discord.ApplicationContext,
    game_id: str,
):
    """
    Plays the user's turn.

    Args:
        ctx (discord.ApplicationContext): The application context.
        game_id (str): The game ID.
    """
    assert ctx.interaction.user
    if not game_id:
        games_with_id = games_with_user(ctx.interaction.user.id)
        if not games_with_id:
            await ctx.respond(MESSAGES["user_not_in_any_games"], ephemeral=True)
            return
        new_game_id = games_with_id[0]
    else:
        new_game_id = int(game_id)
    if new_game_id not in eggsplode_app.games:
        await ctx.respond(MESSAGES["gmae_not_found"], ephemeral=True)
        return
    if ctx.interaction.user.id not in eggsplode_app.games[new_game_id].players:
        await ctx.respond(MESSAGES["user_not_in_game"], ephemeral=True)
        return
    if not eggsplode_app.games[new_game_id].hands:
        await ctx.respond(MESSAGES["game_not_started"], ephemeral=True)
        return
    view = TurnView(
        ActionContext(
            app=eggsplode_app,
            game_id=new_game_id,
        )
    )
    await ctx.respond(MESSAGES["turn_prompt"], view=view, ephemeral=True)


@eggsplode_app.slash_command(
    name="hand",
    description="View your hand.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
@discord.option(
    "game_id",
    type=str,
    description="The game ID",
    required=False,
    default="",
    autocomplete=game_id_autocomplete,
)
async def hand(
    ctx: discord.ApplicationContext,
    game_id: str,
):
    """
    Views the user's hand.

    Args:
        ctx (discord.ApplicationContext): The application context.
        game_id (str): The game ID.
    """
    assert ctx.interaction.user
    if not game_id:
        games_with_id = games_with_user(ctx.interaction.user.id)
        if not games_with_id:
            await ctx.respond(MESSAGES["user_not_in_any_games"], ephemeral=True)
            return
        new_game_id = games_with_id[0]
    else:
        new_game_id = int(game_id)
    if new_game_id not in eggsplode_app.games:
        await ctx.respond(MESSAGES["game_not_found"], ephemeral=True)
        return
    if ctx.interaction.user.id not in eggsplode_app.games[new_game_id].players:
        await ctx.respond(MESSAGES["user_not_in_game"], ephemeral=True)
        return
    try:
        player_hand = eggsplode_app.games[new_game_id].group_hand(
            ctx.interaction.user.id
        )
        hand_details = "".join(
            MESSAGES["hand_list"].format(
                CARDS[card]["emoji"],
                CARDS[card]["title"],
                count,
                CARDS[card]["description"],
            )
            for card, count in player_hand
        )
        await ctx.respond(MESSAGES["hand_title"].format(hand_details), ephemeral=True)
    except KeyError:
        await ctx.respond("❌ Game has not started yet!", ephemeral=True)


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
                MESSAGES["maintenance_mode_no_games_running"] if not eggsplode_app.games else "",
            ),
            ephemeral=True,
        )
    elif command == ADMIN_LISTGAMES_CODE:
        await ctx.respond(
            MESSAGES["list_games_title"].format(
                ", ".join(str(i) for i in eggsplode_app.games)
            ),
            ephemeral=True,
        )
    else:
        await ctx.respond(MESSAGES["invalid_command"], ephemeral=True)


print("Hello, World!")
eggsplode_app.run(DISCORD_TOKEN)
