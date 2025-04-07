"""
Contains the BaseView class which is used to create a Discord UI view for the game.
"""

import discord
from ..ctx import ActionContext
from ..strings import get_message


class BaseView(discord.ui.View):
    def __init__(self, ctx: ActionContext, timeout=None):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.ctx = ctx
        self.ephemeral_full_log = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        await interaction.response.defer(invisible=True)
        return True

    @discord.ui.button(
        label="Full game log", style=discord.ButtonStyle.gray, emoji="📜", row=4
    )
    async def full_log(self, _: discord.ui.Button, interaction: discord.Interaction):
        view = UpDownView(
            lambda interaction, index: None,  # Placeholder lambda
            len(self.ctx.log.pages),
        )
        view.callback = lambda interaction, index: interaction.edit(
            content=self.get_page_with_count(index),
            view=view,
        )
        await interaction.respond(
            self.get_page_with_count(len(self.ctx.log.pages) - 1),
            view=view,
            ephemeral=self.ephemeral_full_log,
        )

    def get_page_with_count(self, index):
        return self.ctx.log.pages[index] + get_message("page_count").format(
            index + 1, len(self.ctx.log.pages)
        )


class UpDownView(discord.ui.View):
    def __init__(self, callback, amount):
        super().__init__(timeout=60, disable_on_timeout=True)
        self.callback = callback
        self.amount = amount
        self.index = 0

    @discord.ui.button(label="⬆️", style=discord.ButtonStyle.grey)
    async def up(self, _: discord.ui.Button, interaction: discord.Interaction):
        if self.index > 0:
            self.index -= 1
        else:
            self.index = self.amount - 1
        await self.callback(interaction, self.index)

    @discord.ui.button(label="⬇️", style=discord.ButtonStyle.grey)
    async def down(self, _: discord.ui.Button, interaction: discord.Interaction):
        if self.index < self.amount - 1:
            self.index += 1
        else:
            self.index = 0
        await self.callback(interaction, self.index)
