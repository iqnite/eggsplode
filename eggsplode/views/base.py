"""
Contains the BaseView class which is used to create a Discord UI view for the game.
"""

import discord
from ..ctx import ActionContext


class BaseView(discord.ui.View):
    def __init__(self, ctx: ActionContext, timeout=None):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.ctx = ctx

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass


class ButtonView(discord.ui.View):
    def __init__(self, callback, amount):
        super().__init__(timeout=60, disable_on_timeout=True)
        for i in range(1, amount + 1):
            button = discord.ui.Button(
                label=f"[{i}]",
                style=discord.ButtonStyle.primary,
            )
            button.callback = lambda interaction: self.handle(
                lambda: callback(interaction, i)
            )
            self.add_item(button)

    async def handle(self, callback):
        await callback()
        self.disable_all_items()
