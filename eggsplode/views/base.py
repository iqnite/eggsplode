"""
Contains the BaseView class which is used to create a Discord UI view for the game.
"""

import discord
from ..ctx import ActionContext


class BaseView(discord.ui.View):
    def __init__(self, ctx: ActionContext, timeout=600):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.ctx = ctx

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
