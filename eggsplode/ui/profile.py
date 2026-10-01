"""
Contains the UI for user profiles and stats.
"""

import asyncio
from typing import TYPE_CHECKING

import discord

from eggsplode import database
from eggsplode.strings import all_achievements, format_message
from eggsplode.ui.paginator import PaginatedView

if TYPE_CHECKING:
    from eggsplode.commands import EggsplodeApp


class ProfileView(discord.ui.DesignerView):
    def __init__(self, app: "EggsplodeApp", user_id: int):
        super().__init__(timeout=None)
        self.app = app
        self.user_id = user_id
        self.achievements_button = discord.ui.Button(
            label=format_message("profile_achievements_button"),
            emoji="🏆",
            style=discord.ButtonStyle.primary,
        )

    async def load_user_profile(self):
        user_info_discord, user_info_db, user_achievements = await asyncio.gather(
            self.app.get_or_fetch(discord.User, self.user_id),
            database.get_user(self.user_id),
            database.get_user_achievements(self.user_id),
        )
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
        self.achievements_button = discord.ui.Button(
            label=format_message("profile_achievements_button"),
            emoji=(
                all_achievements[user_achievements[0]]["emoji"]
                if user_achievements
                else "❔"
            ),
            style=discord.ButtonStyle.primary,
        )
        self.achievements_button.callback = self.show_achievements
        self.add_item(discord.ui.ActionRow(self.achievements_button))

    async def show_achievements(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_achievements = await database.get_user_achievements(self.user_id)
        view = AchievementsView(user_achievements)
        await interaction.respond(view=view, ephemeral=True)


class AchievementsView(PaginatedView):
    def __init__(self, achievements: list[database.Achievement], is_own: bool = False):
        super().__init__(timeout=None)
        self.is_own = is_own
        self.achievements = achievements
        self.update_pagination(self.populate_items())

    def populate_items(self):
        locked = []
        unlocked = []
        for achievement in self.achievements:
            item = discord.ui.TextDisplay(
                format_message(
                    "profile_achievements_list_item",
                    achievement.emoji if achievement.is_unlocked else "❔",
                    achievement.title,
                    (achievement.message if self.is_own else ""),
                    achievement.flavor,
                )
            )
            if achievement.is_unlocked:
                unlocked.append(item)
            else:
                locked.append(item)
        return unlocked + locked
