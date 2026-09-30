"""
Contains the UI for user profiles and stats.
"""

from typing import TYPE_CHECKING

import discord

from eggsplode import database
from eggsplode.strings import format_message

if TYPE_CHECKING:
    from eggsplode.commands import EggsplodeApp


class ProfileView(discord.ui.DesignerView):
    def __init__(self, app: "EggsplodeApp", user_id: int):
        super().__init__(timeout=None)
        self.app = app
        self.user_id = user_id

    async def load_user_profile(self):
        database_task = database.get_user(self.user_id)
        discord_task = self.app.get_or_fetch(discord.User, self.user_id)
        user_info_db = await database_task
        user_info_discord = await discord_task
        if user_info_discord is None:
            self.add_item(discord.ui.TextDisplay(format_message("user_not_found")))
            return
        self.add_item(
            discord.ui.Section(
                discord.ui.TextDisplay(format_message("profile_title", self.user_id)),
                discord.ui.TextDisplay(
                    format_message("profile_games_won", user_info_db.games_won)
                ),
                discord.ui.TextDisplay(
                    format_message("profile_games_played", user_info_db.games_played)
                ),
                accessory=discord.ui.Thumbnail(
                    url=user_info_discord.display_avatar.url
                ),
            )
        )
