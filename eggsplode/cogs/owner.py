"""
Contains owner only commands.
"""

import asyncio
import discord
from discord.ext import commands
from eggsplode.commands import EggsplodeApp
from eggsplode.strings import get_message, TEST_GUILD_ID, CONFIG


class Owner(commands.Cog):
    def __init__(self, app: EggsplodeApp):
        self.app = app

    @discord.slash_command(
        name="restart",
        description="Restart the bot.",
        guild_ids=[TEST_GUILD_ID],
    )
    @commands.is_owner()
    async def restart(self, ctx: discord.ApplicationContext):
        await self.maintenance(ctx)
        while self.app.game_count > 0:
            await asyncio.sleep(10)
        if not self.app.admin_maintenance:
            return
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
        self.app.cleanup()
        self.app.admin_maintenance = not self.app.admin_maintenance
        await ctx.respond(
            get_message("maintenance_mode_toggle").format(
                "enabled" if self.app.admin_maintenance else "disabled",
                (
                    get_message("maintenance_mode_no_games_running")
                    if not self.app.games
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

        with open("temp/output.txt", "w", encoding="utf-8") as f:
            f.write(stdout.decode() + "\n" + stderr.decode())
        if process.returncode == 0:
            await ctx.edit(
                content=get_message("command_success"),
                file=discord.File(fp="temp/output.txt"),
            )
        else:
            await ctx.edit(
                content=get_message("command_failed"),
                file=discord.File(fp="temp/output.txt"),
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
                "\n".join(f"- {i}" for i in self.app.games)
            ),
            ephemeral=True,
        )

    @discord.slash_command(
        name="set_status",
        description="Set the bot's status.",
        guild_ids=[TEST_GUILD_ID],
    )
    @discord.option(
        name="status",
        description="The status to set the bot to.",
        input_type=str,
        required=False,
        autocomplete=lambda _: list(discord.Status.__members__.keys()),
    )
    @discord.option(
        name="activity",
        description="The activity to set the bot to.",
        input_type=str,
        required=False,
    )
    @discord.option(
        name="activity_type",
        description="The type of activity to set the bot to.",
        input_type=str,
        required=False,
        autocomplete=lambda _: list(discord.ActivityType.__members__.keys()),
    )
    @commands.is_owner()
    async def set_status(
        self,
        ctx: discord.ApplicationContext,
        status: str,
        activity: str | None = None,
        activity_type: str | None = None,
    ):
        await ctx.response.defer(ephemeral=True)
        await self.app.change_presence(
            activity=(
                discord.Activity(
                    type=discord.ActivityType[activity_type], name=activity or ""
                )
                if activity_type
                else discord.CustomActivity(name=activity or "")
            ),
            status=discord.Status[status or "online"],
        )
        await ctx.respond(get_message("set_status_success"), ephemeral=True)


def setup(bot: EggsplodeApp):
    bot.add_cog(Owner(bot))
