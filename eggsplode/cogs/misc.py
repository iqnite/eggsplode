"""
Contains additional commands.
"""

import discord
from discord.ext import commands
from eggsplode.commands import EggsplodeApp
from eggsplode.ui.start import HelpView
from eggsplode.strings import INFO, get_message


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
    async def show_help(self, ctx: discord.ApplicationContext):
        await ctx.respond(view=HelpView())

    @discord.slash_command(
        name="status",
        description="Check the status of the app.",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def status(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        await ctx.respond(
            get_message("status").format(
                self.bot.latency * 1000,
                INFO["version"],
                get_message("maintenance") if self.bot.admin_maintenance else "",
            ),
            ephemeral=True,
        )

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
                message.content.replace("eg", "egg")
                .replace("egg", "**egg**")
                .replace("Egg", "**EGG**")
                .replace("EGG", "**__EGG__**")
                .replace("ex", "eggs")
                .replace("ack", "egg")
                .replace("ac", "egg")
                .replace("O", "🥚")
                .replace("0", "🥚")
            )
        except discord.HTTPException:
            await ctx.respond(get_message("eggify_error"), ephemeral=True)


def setup(bot: EggsplodeApp):
    bot.add_cog(Misc(bot))
