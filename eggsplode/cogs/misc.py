"""
Contains commands for the main Eggsplode game.
"""

import asyncio
import os
import discord
from discord.ext import commands

from ..commands import EggsplodeApp
from ..strings import ADMIN_LISTGAMES_CODE, ADMIN_MAINTENANCE_CODE, RESTART_CMD, get_message
from ..ctx import ActionContext
from ..game_logic import Game
from ..views.starter import StartGameView


class Misc(commands.Cog):
    def __init__(self, bot: EggsplodeApp):
        self.bot = bot

    @discord.slash_command(
        name="help",
        description="Learn how to play Eggsplode and view useful info!",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def show_help_command(self, ctx: discord.ApplicationContext):
        await self.bot.show_help(ctx)

    @discord.slash_command(
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
    async def terminal(self, ctx: discord.ApplicationContext, command: str):
        if command == ADMIN_MAINTENANCE_CODE:
            self.bot.cleanup()
            self.bot.admin_maintenance = not self.bot.admin_maintenance
            await ctx.respond(
                get_message("maintenance_mode_toggle").format(
                    "enabled" if self.bot.admin_maintenance else "disabled",
                    (
                        get_message("maintenance_mode_no_games_running")
                        if not self.bot.games
                        else ""
                    ),
                ),
                ephemeral=True,
            )
            while self.bot.games and self.bot.admin_maintenance:
                await asyncio.sleep(10)
            if RESTART_CMD and self.bot.admin_maintenance:
                print("RESTARTING VIA ADMIN COMMAND")
                os.system(RESTART_CMD)
        elif command == ADMIN_LISTGAMES_CODE:
            await ctx.respond(
                get_message("list_games_title").format(
                    "\n".join(f"- {i}" for i in self.bot.games)
                ),
                ephemeral=True,
            )
        else:
            await ctx.respond(get_message("invalid_command"), ephemeral=True)


def setup(bot: EggsplodeApp):
    bot.add_cog(Misc(bot))
