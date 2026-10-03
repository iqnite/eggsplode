"""
Contains the UI for user profiles and stats.
"""

import asyncio
from typing import TYPE_CHECKING

import discord

from eggsplode import database
from eggsplode.strings import format_message
from eggsplode.ui.paginator import PaginatedView

if TYPE_CHECKING:
    from eggsplode.commands import EggsplodeApp


class ProfileView(discord.ui.DesignerView):
    def __init__(self, app: "EggsplodeApp", user_id: int, requester_id: int):
        super().__init__(timeout=None)
        self.app = app
        self.user_id = user_id
        self.user_info_db: database.User | None = None
        self.achievements_button = None
        self.is_own = self.user_id == requester_id
        self.achievements_view = AchievementsView(is_own=self.is_own)
        self.settings_buttton = discord.ui.Button(
            label=format_message("profile_settings_button"),
            emoji="⚙️",
            style=discord.ButtonStyle.secondary,
        )

    async def load_user_profile(self):
        self.user_info_db = await database.get_user(self.user_id, create=False)
        if self.user_info_db is None:
            self.add_item(discord.ui.TextDisplay(format_message("user_not_registered")))
            return
        user_info_discord, user_achievements = await asyncio.gather(
            self.app.get_or_fetch(discord.User, self.user_id),
            database.get_user_achievements(self.user_id),
        )
        if user_info_discord is None:
            self.add_item(discord.ui.TextDisplay(format_message("user_not_found")))
            return
        if not self.user_info_db.is_profile_public and not self.is_own:
            self.add_item(discord.ui.TextDisplay(format_message("profile_private")))
            return
        user_achievements = await database.get_user_achievements(self.user_id)
        self.achievements_view.set_achievements(user_achievements)
        unlocked_achievements = (
            self.achievements_view.unlocked_achievements
            if self.achievements_view.unlocked_achievements
            else []
        )
        self.achievements_button = discord.ui.Button(
            label=format_message("profile_achievements_button"),
            style=discord.ButtonStyle.primary,
        )
        self.achievements_button.callback = self.show_achievements
        self.add_item(
            discord.ui.Container(
                discord.ui.Section(
                    discord.ui.TextDisplay(
                        format_message("profile_title", self.user_id)
                    ),
                    discord.ui.TextDisplay(
                        format_message(
                            "profile_games_played", self.user_info_db.games_played
                        )
                    ),
                    discord.ui.TextDisplay(
                        format_message("profile_games_won", self.user_info_db.games_won)
                    ),
                    accessory=discord.ui.Thumbnail(
                        url=user_info_discord.display_avatar.url
                    ),
                ),
                discord.ui.Separator(),
                discord.ui.Section(
                    discord.ui.TextDisplay(
                        format_message(
                            "profile_achievements",
                            len(unlocked_achievements),
                            len(user_achievements),
                        )
                    ),
                    discord.ui.TextDisplay(
                        get_achievement_preview(user_achievements, max_count=3)
                    ),
                    accessory=self.achievements_button,
                ),
                color=discord.Color(self.user_info_db.color),
            )
        )
        if self.is_own:
            self.settings_buttton.callback = self.show_settings
            self.add_item(discord.ui.ActionRow(self.settings_buttton))

    async def show_achievements(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_achievements = await database.get_user_achievements(self.user_id)
        self.achievements_view.set_achievements(user_achievements)
        await interaction.respond(view=self.achievements_view, ephemeral=True)

    async def show_settings(self, interaction: discord.Interaction):
        if self.user_info_db is None:
            return
        if interaction.user is None:
            return
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                format_message("profile_settings_not_own"), ephemeral=True
            )
            return
        await interaction.response.send_modal(ProfileSettingsModal(self.user_info_db))


class AchievementsView(PaginatedView):
    def __init__(
        self,
        achievements: list[database.Achievement] | None = None,
        is_own: bool = False,
    ):
        super().__init__(timeout=None)
        self.is_own = is_own
        self.achievements = []
        self.divided_achievements = ([], [], [])
        if achievements is not None:
            self.set_achievements(achievements)

    def set_achievements(self, achievements: list[database.Achievement]):
        self.divided_achievements = divide_achievements(achievements)
        self.achievements = (
            self.divided_achievements[0]
            + list(reversed(self.divided_achievements[1]))
            + self.divided_achievements[2]
        )
        self.update_pagination(list(self.get_displays_for_achievements()))

    def get_displays_for_achievements(self):
        for achievement in self.achievements:
            yield discord.ui.TextDisplay(
                format_message(
                    "profile_achievements_list_item",
                    emoji=achievement.emoji if achievement.is_unlocked else "❔",
                    title=achievement.title,
                    flavor=achievement.flavor,
                    message=achievement.message if self.is_own else "",
                )
            )

    @property
    def unlocked_achievements(self) -> list[database.Achievement]:
        return self.divided_achievements[0]

    @property
    def locked_achievements(self) -> list[database.Achievement]:
        return self.divided_achievements[1]


def divide_achievements(
    achievements: list[database.Achievement],
) -> tuple[
    list[database.Achievement], list[database.Achievement], list[database.Achievement]
]:
    locked = []
    unlocked = []
    hidden = []
    for achievement in achievements:
        if achievement.is_unlocked:
            unlocked.append(achievement)
        elif achievement._locked_message == "Locked":
            hidden.append(achievement)
        else:
            locked.append(achievement)
    return unlocked, locked, hidden


def get_achievement_preview(
    achievements: list[database.Achievement], max_count: int = 3
) -> str:
    unlocked, _, __ = divide_achievements(achievements)
    preview = []
    for achievement in unlocked[:max_count]:
        preview.append(
            format_message(
                "profile_achievements_preview_item",
                emoji=achievement.emoji,
                title=achievement.title,
            )
        )
    if len(unlocked) == 0:
        return format_message("profile_no_achievements")
    if len(unlocked) > max_count:
        preview.append(f"+{len(unlocked) - max_count}")
    return ", ".join(preview)


class ProfileSettingsModal(discord.ui.DesignerModal):
    def __init__(self, user: database.User):
        super().__init__(
            title=format_message("profile_settings_title"),
            timeout=None,
        )
        self.user = user
        self.public_profile_checkbox = discord.ui.Checkbox(
            default=user.is_profile_public
        )
        self.color_input = discord.ui.TextInput(
            placeholder="FE9804",
            value=f"{user.color:06X}",
            max_length=7,
            min_length=6,
            required=False,
        )
        self.add_item(
            discord.ui.Label(
                format_message("profile_settings_public"), self.public_profile_checkbox
            )
        )
        self.add_item(
            discord.ui.Label(format_message("profile_settings_color"), self.color_input)
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if self.color_input.value:
            try:
                color_value = int(self.color_input.value.lstrip("#"), 16)
            except ValueError:
                await interaction.respond(
                    "Invalid color value. Please enter a valid hex color code.",
                    ephemeral=True,
                )
                return
            self.user.color = color_value
        self.user.is_profile_public = bool(self.public_profile_checkbox.value)
        await self.user.save()
        await interaction.respond(
            format_message("profile_settings_updated"), ephemeral=True
        )
