"""
Contains commands for minigames.
"""

import discord
from discord.ext import commands
from eggsplode.commands import EggsplodeApp


class MiniGames(commands.Cog):
    def __init__(self, bot: EggsplodeApp):
        self.bot = bot

    @discord.message_command(
        name="Eggify",
        description="Eggify a message!",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def eggify(self, ctx: discord.ApplicationContext, message: discord.Message):
        await ctx.defer()
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


def setup(bot: EggsplodeApp):
    bot.add_cog(MiniGames(bot))
