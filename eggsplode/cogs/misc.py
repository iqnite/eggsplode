"""
Contains additional commands.
"""

import discord
from discord.ext import commands
from eggsplode.commands import EggsplodeApp
from eggsplode.ui import HelpView, InfoView
from eggsplode.strings import format_message
from eggsplode.ui.base import TextView


class Misc(commands.Cog):
    def __init__(self, app: EggsplodeApp):
        self.app = app

    @discord.slash_command(
        name="help",
        description="Learn how to play Eggsplode and view useful info!",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def show_help(self, ctx: discord.ApplicationContext):
        await ctx.respond(view=HelpView())

    @discord.slash_command(
        name="info",
        description="Show the status and some other info about the app.",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def info(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        view = InfoView(self.app)
        await ctx.respond(view=view, ephemeral=True)

    @discord.message_command(
        name="Eggify",
        description="Eggify a message!",
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
                    text=message.content.replace("eg", "egg")
                    .replace("egg", "**egg**")
                    .replace("Egg", "**EGG**")
                    .replace("EGG", "**__EGG__**")
                    .replace("ex", "eggs")
                    .replace("ack", "egg")
                    .replace("ac", "egg")
                    .replace("O", "🥚")
                    .replace("0", "🥚")
                )
            )
        except discord.HTTPException:
            await ctx.respond(view=TextView("eggify_error"), ephemeral=True)


def setup(app: EggsplodeApp):
    app.add_cog(Misc(app))
