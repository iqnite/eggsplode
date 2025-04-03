"""
Contains commands for the main Eggsplode game.
"""

import discord
from discord.ext import commands

from ..commands import EggsplodeApp
from ..strings import get_message
from ..ctx import ActionContext, ActionLog, EventController
from ..game_logic import Game
from ..views.starter import StartGameView


class MainGame(commands.Cog):
    def __init__(self, bot: EggsplodeApp):
        self.bot = bot

    @discord.slash_command(
        name="start",
        description="Start a new Eggsplode game!",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def start_game(self, ctx: discord.ApplicationContext):
        self.bot.cleanup()
        if self.bot.admin_maintenance:
            await ctx.respond(get_message("maintenance"), ephemeral=True)
            return
        game_id = ctx.interaction.channel_id
        if not (game_id and ctx.interaction.user):
            return
        if game_id in self.bot.games:
            await ctx.respond(get_message("game_already_exists"), ephemeral=True)
            return
        await ctx.defer()
        self.bot.games[game_id] = Game(
            {
                "players": [ctx.interaction.user.id],
            }
        )
        action_log = ActionLog(anchor_interaction=ctx.interaction, character_limit=2000)
        action_ctx = ActionContext(
            app=self.bot, game_id=game_id, log=action_log, events=EventController()
        )
        view = StartGameView(action_ctx)
        await ctx.interaction.respond(
            view.generate_game_start_message(),
            view=view,
        )

    @discord.slash_command(
        name="hand",
        description="View your hand.",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def hand(self, ctx: discord.ApplicationContext):
        game_id = ctx.interaction.channel_id
        if not (game_id and ctx.interaction.user):
            return
        if game_id not in self.bot.games:
            await ctx.respond(get_message("game_not_found"), ephemeral=True)
            return
        if ctx.interaction.user.id not in self.bot.games[game_id].players:
            await ctx.respond(get_message("user_not_in_game"), ephemeral=True)
            return
        if not self.bot.games[game_id].hands:
            await ctx.respond(get_message("game_not_started"), ephemeral=True)
            return
        await ctx.respond(
            get_message("hand_title").format(
                self.bot.games[game_id].cards_help(
                    ctx.interaction.user.id, template=get_message("hand_list")
                )
            ),
            ephemeral=True,
        )

    @discord.slash_command(
        name="games",
        description="View which games you're in.",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def list_user_games(self, ctx: discord.ApplicationContext):
        self.bot.cleanup()
        if not ctx.interaction.user:
            return
        found_games = self.bot.games_with_user(ctx.interaction.user.id)
        await ctx.respond(
            (
                get_message("list_games_title").format(
                    "\n".join(
                        get_message("list_games_item").format(i) for i in found_games
                    )
                )
                if found_games
                else get_message("user_not_in_any_games")
            ),
            ephemeral=True,
        )


def setup(bot: EggsplodeApp):
    bot.add_cog(MainGame(bot))
