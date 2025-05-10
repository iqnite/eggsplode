"""
Contains additional views.
"""

import discord


class UpDownView(discord.ui.View):
    def __init__(self, callback, amount):
        super().__init__(timeout=60, disable_on_timeout=True)
        self.callback = callback
        self.amount = amount
        self.index = amount - 1

    @discord.ui.button(label="⬆️", style=discord.ButtonStyle.grey)
    async def up(self, _, interaction: discord.Interaction):
        if self.index > 0:
            self.index -= 1
        else:
            self.index = self.amount - 1
        await self.callback(interaction, self.index)

    @discord.ui.button(label="⬇️", style=discord.ButtonStyle.grey)
    async def down(self, _, interaction: discord.Interaction):
        if self.index < self.amount - 1:
            self.index += 1
        else:
            self.index = 0
        await self.callback(interaction, self.index)
