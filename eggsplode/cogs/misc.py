"""
Contains additional commands.
"""

import discord
from discord.ext import commands
from eggsplode.commands import EggsplodeApp
from eggsplode.strings import format_message
from eggsplode.ui import HelpView, InfoView
from eggsplode.ui.base import TextView


class Misc(commands.Cog):
    def __init__(self, app: EggsplodeApp):
        self.app = app

    @discord.slash_command(
        name="help",
        description=format_message("cmd_help_desc"),
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def show_help(self, ctx: discord.ApplicationContext):
        await ctx.respond(view=HelpView())

    @discord.slash_command(
        name="info",
        description=format_message("cmd_info_desc"),
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def info(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        view = InfoView(self.app)
        await view.create_container()
        await ctx.respond(view=view, ephemeral=True)

    @discord.message_command(
        name="Eggify",
        description=format_message("cmd_eggify_desc"),
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def eggify(self, ctx: discord.ApplicationContext, message: discord.Message):
        await ctx.defer(invisible=True)
        try:
            await ctx.respond(
                view=TextView(
                    message.content.replace("eg", "egg")
                    .replace("egg", "**egg**")
                    .replace("Egg", "**EGG**")
                    .replace("EGG", "**__EGG__**")
                    .replace("ex", "eggs")
                    .replace("ack", "egg")
                    .replace("ac", "egg")
                    .replace("O", "🥚")
                    .replace("0", "🥚"),
                    verbatim=True,
                )
            )
        except discord.HTTPException:
            await ctx.respond(view=TextView("eggify_error"), ephemeral=True)

    @discord.message_command(
        name="Clownify",
        description=format_message("cmd_clownify_desc"),
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def clownify(self, ctx: discord.ApplicationContext, message: discord.Message):
        await ctx.defer(invisible=True)
        new_message = ""
        for i, char in enumerate(message.content):
            new_message += char.lower() if i % 2 else char.upper()
        try:
            await ctx.respond(
                view=TextView(
                    format_message("clownify_output", new_message),
                    verbatim=True,
                )
            )
        except discord.HTTPException:
            await ctx.respond(view=TextView("eggify_error"), ephemeral=True)


def setup(app: EggsplodeApp):
    app.add_cog(Misc(app))
