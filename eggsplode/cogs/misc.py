"""
Contains additional utility commands.
"""

import discord
from discord.ext import commands
from ..commands import EggsplodeApp


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
        await self.bot.show_help(ctx.interaction)


def setup(bot: EggsplodeApp):
    bot.add_cog(Misc(bot))
