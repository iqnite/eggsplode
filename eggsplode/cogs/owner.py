"""
Contains owner only commands.
"""

import asyncio
import discord
from discord.ext import commands

from eggsplode.commands import EggsplodeApp
from eggsplode.strings import get_message, TEST_GUILD_ID, CONFIG


class Owner(commands.Cog):
    def __init__(self, bot: EggsplodeApp):
        self.bot = bot

    @discord.slash_command(
        name="restart",
        description="Restart the bot.",
        guild_ids=[TEST_GUILD_ID],
    )
    @commands.is_owner()
    async def restart(self, ctx: discord.ApplicationContext):
        await self.maintenance(ctx)
        while self.bot.games and self.bot.admin_maintenance:
            await asyncio.sleep(10)
        print("RESTARTING VIA ADMIN COMMAND")
        await asyncio.create_subprocess_shell(CONFIG.get("restart_command", ""))

    @discord.slash_command(
        name="update",
        description="Download the latest version, install dependencies, and restart the bot.",
        guild_ids=[TEST_GUILD_ID],
    )
    @commands.is_owner()
    async def update(self, ctx: discord.ApplicationContext):
        update_command = CONFIG.get("update_command", "")
        if not update_command:
            await ctx.respond("Update command is not configured.", ephemeral=True)
            return
        await self.execute(ctx, update_command)
        await self.restart(ctx)

    @discord.slash_command(
        name="maintenance",
        description="Enable maintenance mode on the bot.",
        guild_ids=[TEST_GUILD_ID],
    )
    @commands.is_owner()
    async def maintenance(self, ctx: discord.ApplicationContext):
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

    @discord.slash_command(
        name="execute",
        description="Run a command on the bot.",
        guild_ids=[TEST_GUILD_ID],
    )
    @discord.option(
        name="command",
        description="The command to run on the bot.",
        input_type=str,
        required=True,
    )
    @commands.is_owner()
    async def execute(self, ctx: discord.ApplicationContext, command: str):
        await ctx.response.defer(ephemeral=True)
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            await ctx.edit(
                content=get_message("command_success").format(stdout.decode()[1800:])
            )
        else:
            await ctx.edit(
                content=get_message("command_failed").format(stderr.decode()[1800:])
            )

    @discord.slash_command(
        name="all_games",
        description="List all games.",
        guild_ids=[TEST_GUILD_ID],
    )
    @commands.is_owner()
    async def list_games(self, ctx):
        await ctx.respond(
            get_message("list_games_title").format(
                "\n".join(f"- {i}" for i in self.bot.games)
            ),
            ephemeral=True,
        )


def setup(bot: EggsplodeApp):
    bot.add_cog(Owner(bot))
