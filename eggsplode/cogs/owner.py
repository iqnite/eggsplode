"""
Contains owner only commands.
"""

import asyncio
import discord
from discord.ext import commands
from eggsplode.commands import EggsplodeApp
from eggsplode.strings import format_message, test_guild_id, app_config


class Owner(commands.Cog):
    def __init__(self, app: EggsplodeApp):
        self.app = app

    @discord.slash_command(
        name="restart",
        description="Restart the bot.",
        guild_ids=[test_guild_id],
    )
    @commands.is_owner()
    async def restart(self, ctx: discord.ApplicationContext):
        await self.maintenance(ctx)
        while self.app.game_count > 0:
            await asyncio.sleep(10)
        if not self.app.admin_maintenance:
            return
        self.app.logger.info("Restarting via slash command.")
        await asyncio.create_subprocess_shell(app_config.get("restart_command", ""))

    @discord.slash_command(
        name="update",
        description="Download the latest version, install dependencies, and restart the bot.",
        guild_ids=[test_guild_id],
    )
    @commands.is_owner()
    async def update(self, ctx: discord.ApplicationContext):
        update_command = app_config.get("update_command", "")
        if not update_command:
            await ctx.respond("Update command is not configured.", ephemeral=True)
            return
        await self.execute(ctx, update_command)
        await self.restart(ctx)

    @discord.slash_command(
        name="maintenance",
        description="Enable maintenance mode on the bot.",
        guild_ids=[test_guild_id],
    )
    @commands.is_owner()
    async def maintenance(self, ctx: discord.ApplicationContext):
        self.app.remove_inactive_games()
        self.app.admin_maintenance = not self.app.admin_maintenance
        await ctx.respond(
            format_message(
                "maintenance_mode_toggle",
                "enabled" if self.app.admin_maintenance else "disabled",
                (
                    format_message("maintenance_mode_no_games_running")
                    if not self.app.games
                    else ""
                ),
            ),
            ephemeral=True,
        )

    @discord.slash_command(
        name="execute",
        description="Run a command on the bot.",
        guild_ids=[test_guild_id],
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
                content=format_message("command_success"),
                file=discord.File(fp="temp/output.txt"),
            )
        else:
            await ctx.edit(
                content=format_message("command_failed"),
                file=discord.File(fp="temp/output.txt"),
            )

    @discord.slash_command(
        name="get_file",
        description="Get a file from the bot.",
        guild_ids=[test_guild_id],
    )
    @discord.option(
        name="file_path",
        description="The path to the file to get.",
        input_type=str,
        required=True,
    )
    @commands.is_owner()
    async def get_file(self, ctx: discord.ApplicationContext, file_path: str):
        await ctx.response.defer(ephemeral=True)
        try:
            with open(file_path, "rb") as f:
                await ctx.respond(file=discord.File(fp=f))
        except (FileNotFoundError, OSError, discord.HTTPException):
            await ctx.respond(format_message("file_send_error"), ephemeral=True)

    @discord.slash_command(
        name="all_games",
        description="List all games.",
        guild_ids=[test_guild_id],
    )
    @commands.is_owner()
    async def list_games(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            format_message(
                "list_games_title",
                "\n".join(
                    format_message(
                        "list_item_2",
                        game_id,
                        (
                            "(active)"
                            if getattr(game, "running", False)
                            else "(inactive)"
                        ),
                    )
                    for game_id, game in self.app.games.items()
                ),
            ),
            ephemeral=True,
        )

    @discord.slash_command(
        name="set_status",
        description="Set the bot's status.",
        guild_ids=[test_guild_id],
    )
    @discord.option(
        name="status",
        description="The status to set the bot to.",
        input_type=str,
        required=False,
        choices=list(discord.Status.__members__.keys()),
    )
    @discord.option(
        name="status_message",
        description="The status message to show.",
        input_type=str,
        required=False,
    )
    @commands.is_owner()
    async def set_status(
        self,
        ctx: discord.ApplicationContext,
        status: str,
        status_message: str | None = None,
    ):
        await ctx.response.defer(ephemeral=True)
        await self.app.change_presence(
            activity=(discord.CustomActivity(name=status_message or "")),
            status=discord.Status[status or "online"],
        )
        await ctx.respond(format_message("set_status_success"), ephemeral=True)


def setup(app: EggsplodeApp):
    app.add_cog(Owner(app))
