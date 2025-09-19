"""
Contains the StartGameView class which handles the start game view in the Discord bot.
"""

import datetime
import json
import time
from typing import TYPE_CHECKING
import psutil
import discord
from eggsplode.strings import MESSAGES, RECIPES, INFO, format_message, replace_emojis
from eggsplode.ui.base import TextView

if TYPE_CHECKING:
    from eggsplode.commands import EggsplodeApp
    from eggsplode.core import Game


COVERED_RECIPE_EXCEPTIONS = (
    AttributeError,
    IndexError,
    OverflowError,
    TypeError,
    ValueError,
    json.JSONDecodeError,
    ZeroDivisionError,
)


async def check_permissions(game: "Game", interaction: discord.Interaction):
    if (not interaction.user) or interaction.user.id != game.config["players"][0]:
        await interaction.respond(
            view=TextView("not_game_creator"),
            ephemeral=True,
            delete_after=5,
        )
        return False
    return True


class StartGameView(discord.ui.View):
    def __init__(self, game: "Game"):
        super().__init__(timeout=600, disable_on_timeout=True)
        self.game = game
        self.game.events.game_end += self.terminate_view
        self.game.config["recipe_id"] = "classic"
        self.game.config["recipe"] = RECIPES["classic"]

        self.header = discord.ui.Section()
        self.title = discord.ui.TextDisplay(format_message("start"))
        self.header.add_item(self.title)
        self.start_game_button = discord.ui.Button(
            label="Start", style=discord.ButtonStyle.green, emoji="🚀"
        )
        self.start_game_button.callback = self.start_game
        self.header.accessory = self.start_game_button
        self.add_item(self.header)

        self.players_container = discord.ui.Container()
        self.join_game_button = discord.ui.Button(
            label="Join", style=discord.ButtonStyle.blurple, emoji="👋"
        )
        self.join_game_button.callback = self.join_game
        self.players_container.add_section(
            discord.ui.TextDisplay(format_message("players")),
            accessory=self.join_game_button,
        )
        self.players_display = discord.ui.TextDisplay(self.game.player_list)
        self.players_container.add_item(self.players_display)
        self.add_item(self.players_container)

        self.help_button = discord.ui.Button(
            label="Help", style=discord.ButtonStyle.secondary, emoji="❓"
        )
        self.help_button.callback = self.help
        self.settings_container = discord.ui.Container()
        self.settings_container.add_section(
            discord.ui.TextDisplay(format_message("settings")),
            accessory=self.help_button,
        )
        self.recipe_select = discord.ui.Select(
            options=self.recipe_options,
            placeholder="Custom",
            min_values=1,
            max_values=1,
        )
        self.recipe_select.callback = self.recipe_callback
        self.edit_recipe_button = discord.ui.Button(
            label="Edit", style=discord.ButtonStyle.secondary, emoji="✏️"
        )
        self.edit_recipe_button.callback = self.edit_recipe
        self.settings_container.add_section(
            discord.ui.TextDisplay(format_message("recipe")),
            discord.ui.TextDisplay(format_message("recipe_description")),
            accessory=self.edit_recipe_button,
        )
        self.settings_container.add_item(self.recipe_select)
        self.settings_container.add_separator()
        self.advanced_settings_button = discord.ui.Button(
            label="View", style=discord.ButtonStyle.secondary, emoji="⚙️"
        )
        self.advanced_settings_button.callback = self.advanced_settings
        self.settings_container.add_section(
            discord.ui.TextDisplay(format_message("advanced_settings")),
            discord.ui.TextDisplay(format_message("advanced_settings_description")),
            accessory=self.advanced_settings_button,
        )
        self.add_item(self.settings_container)
        self.add_item(discord.ui.TextDisplay(format_message("hang_warning")))

    async def on_timeout(self):
        await self.game.events.game_end()
        self.terminate_view()
        self.title.content = format_message("game_timeout")
        await super().on_timeout()

    async def join_game(self, interaction: discord.Interaction):
        if not interaction.user:
            return
        await interaction.response.defer(invisible=True)
        if interaction.user.id in self.game.config["players"]:
            await interaction.respond(
                view=LeaveGameView(self, interaction.user.id), ephemeral=True
            )
            return
        self.game.config["players"].append(interaction.user.id)
        self.players_display.content = self.game.player_list
        await interaction.edit(view=self)

    async def remove_player(self, user_id: int, interaction: discord.Interaction):
        if not self.message:
            return
        self.game.config["players"].remove(user_id)
        self.players_display.content = self.game.player_list
        if not self.game.config["players"]:
            await self.game.events.game_end()
            self.terminate_view()
            self.title.content = format_message("game_cancelled")
        await interaction.followup.edit_message(self.message.id, view=self)

    def terminate_view(self):
        self.stop()
        self.remove_item(self.players_container)
        self.remove_item(self.settings_container)
        self.remove_item(self.join_game_button)
        self.header.accessory = discord.ui.Button(emoji="🚫", disabled=True)

    async def start_game(self, interaction: discord.Interaction):
        if not await check_permissions(self.game, interaction):
            return
        if len(self.game.config["players"]) < 2:
            await interaction.respond(
                view=TextView("not_enough_players_to_start"),
                ephemeral=True,
                delete_after=5,
            )
            return
        await interaction.response.defer()
        self.stop()
        self.disable_all_items()
        self.start_game_button.label = format_message("started")
        await interaction.edit(view=self)
        await self.game.start(interaction)

    async def help(self, interaction: discord.Interaction):
        await interaction.respond(view=HelpView(), ephemeral=True)

    @property
    def recipe_options(self) -> list[discord.SelectOption]:
        return [
            discord.SelectOption(
                value=id,
                label=recipe["name"],
                description=recipe["description"],
                emoji=replace_emojis(recipe["emoji"]),
                default=id == self.game.config["recipe_id"],
            )
            for id, recipe in RECIPES.items()
        ]

    async def recipe_callback(self, interaction: discord.Interaction):
        await interaction.edit(view=self)
        if await check_permissions(self.game, interaction):
            recipe_id = self.game.config["recipe_id"] = self.recipe_select.values[0]
            self.game.config["recipe"] = RECIPES[recipe_id]
        self.recipe_select.options = self.recipe_options
        await interaction.edit(view=self)

    async def advanced_settings(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SettingsModal(self.game))

    async def edit_recipe(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EditRecipeModal(self))


class EditRecipeModal(discord.ui.Modal):
    def __init__(self, parent_view: StartGameView, *args, **kwargs):
        super().__init__(*args, **kwargs, title="Edit Recipe")
        self.parent_view = parent_view
        self.parent_message = self.parent_view.message
        if self.parent_message is None:
            raise TypeError("StartGameView message ID is None")
        self.game = parent_view.game
        self.recipe_input = discord.ui.InputText(
            label="Recipe JSON",
            style=discord.InputTextStyle.long,
            value=json.dumps(self.game.config["recipe"], indent=2),
            placeholder=MESSAGES["recipe_json_placeholder"],
            required=True,
            min_length=2,
            max_length=4000,
        )
        self.add_item(self.recipe_input)

    async def callback(self, interaction: discord.Interaction):
        recipe_json = self.recipe_input.value
        if recipe_json is None:
            return
        if self.parent_message is None:
            raise TypeError("StartGameView message ID is None")
        if not self.game:
            return
        if not await check_permissions(self.game, interaction):
            return
        await interaction.response.defer()
        try:
            self.game.load_recipe(recipe_json)
        except COVERED_RECIPE_EXCEPTIONS as e:
            await interaction.respond(
                view=TextView("recipe_json_error", e, recipe_json), ephemeral=True
            )
            return
        self.game.config["recipe"] = json.loads(recipe_json)
        self.game.config["recipe_id"] = ""
        self.parent_view.recipe_select.options = self.parent_view.recipe_options
        await interaction.followup.edit_message(
            self.parent_message.id, view=self.parent_view
        )


class SettingsModal(discord.ui.Modal):
    def __init__(self, game: "Game", *args, **kwargs):
        super().__init__(*args, **kwargs, title="Balancing Settings")
        self.game = game
        self.inputs = {
            "deck_size": {
                "input": discord.ui.InputText(
                    label="Maximum cards on deck",
                    placeholder="",
                    value=self.game.config.get("deck_size", None),
                    required=False,
                ),
            },
            "turn_timeout": {
                "input": discord.ui.InputText(
                    label="[Beta] Turn timeout (seconds)",
                    placeholder="40",
                    value=self.game.config.get("turn_timeout", None),
                    required=False,
                ),
                "min": 10,
                "max": 120,
            },
        }
        for i in self.inputs.values():
            self.add_item(i["input"])

    async def callback(self, interaction: discord.Interaction):
        if not self.game:
            return
        if not await check_permissions(self.game, interaction):
            return
        response = format_message("settings_updated")
        for input_name, item in self.inputs.items():
            item_input = item["input"]
            if item_input.value == "":
                self.game.config.pop(input_name, None)
                response += "\n" + format_message(
                    "settings_updated_success", item_input.label, item_input.placeholder
                )
                continue
            if not (
                validation := self.validate(
                    item_input.value,
                    int,
                    item.get("min", None),
                    item.get("max", None),
                )
            )[0]:
                response += "\n" + format_message(
                    "settings_updated_error",
                    item_input.label,
                    item_input.value,
                    validation[1],
                )
                continue
            self.game.config[input_name] = item_input.value
            response += "\n" + format_message(
                "settings_updated_success", item_input.label, item_input.value
            )
        await interaction.respond(
            view=TextView(response, verbatim=True), ephemeral=True, delete_after=5
        )

    @staticmethod
    def validate(value, required_type=None, min_value=None, max_value=None):
        if required_type and not isinstance(value, required_type):
            try:
                value = required_type(value)
            except ValueError:
                return False, f"Must be a {required_type.__name__}."
        if min_value and value < min_value:
            return False, f"Must be at least {min_value}."
        if max_value and value > max_value:
            return False, f"Must be at most {max_value}."
        return True, ""


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.help_text = discord.ui.TextDisplay(format_message("help0"))
        self.add_item(self.help_text)
        self.cards_help_button = discord.ui.Button(
            label="Cards",
            url="https://github.com/iqnite/eggsplode/wiki/Cards",
            emoji="🎴",
        )
        self.add_item(self.cards_help_button)


class LeaveGameView(discord.ui.View):
    def __init__(self, parent_view: StartGameView, user_id: int):
        super().__init__(timeout=30, disable_on_timeout=True)
        self.parent_view = parent_view
        self.game = parent_view.game
        self.user_id = user_id
        self.warning = discord.ui.TextDisplay(format_message("leave_game_warning"))
        self.add_item(self.warning)
        self.button = discord.ui.Button(
            label=format_message("leave_game_button"), style=discord.ButtonStyle.danger
        )
        self.button.callback = self.leave_game_callback
        self.add_item(self.button)

    async def leave_game_callback(self, interaction: discord.Interaction):
        if not self.game or self.game.started:
            return
        await interaction.edit(delete_after=0, view=self)
        await self.parent_view.remove_player(self.user_id, interaction)


class EndGameView(discord.ui.View):
    def __init__(self, game: "Game"):
        super().__init__(timeout=30, disable_on_timeout=True)
        self.game = game
        self.warning = discord.ui.TextDisplay(format_message("end_game_warning"))
        self.add_item(self.warning)
        self.button = discord.ui.Button(
            label=format_message("end_game_button"), style=discord.ButtonStyle.danger
        )
        self.button.callback = self.end_game_callback
        self.add_item(self.button)

    async def end_game_callback(self, interaction: discord.Interaction):
        if not self.game:
            return
        self.disable_all_items()
        await interaction.edit(view=self)
        if self.game:
            await self.game.events.game_end()
        self.stop()
        await interaction.respond(view=TextView("game_ended"))


class InfoView(discord.ui.View):
    def __init__(self, app: "EggsplodeApp"):
        super().__init__(timeout=None)
        self.app = app
        self.container = discord.ui.Container()
        self.add_item(self.container)
        self.add_item(
            discord.ui.Button(
                label="Help",
                url="https://github.com/iqnite/eggsplode/wiki",
                emoji="❓",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Website",
                url="https://iqnite.github.io/",
                style=discord.ButtonStyle.link,
                emoji=replace_emojis("🌐"),
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Official Server",
                url="https://discord.gg/UGm36FkGDF",
                style=discord.ButtonStyle.link,
                emoji=replace_emojis("💬"),
            )
        )
        self.add_item(
            discord.ui.Button(
                label="GitHub",
                url="https://github.com/iqnite/eggsplode",
                style=discord.ButtonStyle.link,
                emoji=replace_emojis("🐙"),
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Vote on top.gg",
                url="https://top.gg/bot/1325443178622484590/vote",
                style=discord.ButtonStyle.link,
                emoji="🎉",
            )
        )

    async def create_container(self):
        self.container.add_section(
            discord.ui.TextDisplay(
                format_message("version_eggsplode", INFO["version"])
            ),
            discord.ui.TextDisplay(
                format_message("version_pycord", discord.__version__)
            ),
            accessory=discord.ui.Button(
                label="Change log",
                url="https://github.com/iqnite/eggsplode/releases",
                emoji="📜",
            ),
        )
        self.container.add_separator()
        self.container.add_text(
            format_message("status_latency", self.app.latency * 1000)
        )
        uptime = get_uptime()
        self.container.add_text(
            format_message(
                "status_uptime",
                uptime.days,
                uptime.seconds // 3600,
                (uptime.seconds // 60) % 60,
                uptime.seconds % 60,
            )
        )
        self.container.add_text(
            format_message("status_memory", psutil.virtual_memory().percent)
        )
        self.container.add_separator()
        application_info = await self.app.application_info()
        self.container.add_section(
            discord.ui.TextDisplay(
                format_message(
                    "status_server_installs", application_info.approximate_guild_count
                )
            ),
            discord.ui.TextDisplay(
                format_message(
                    "status_user_installs",
                    application_info.approximate_user_install_count,
                )
            ),
            accessory=discord.ui.Button(
                label="Install",
                url="https://discord.com/oauth2/authorize?client_id=1325443178622484590",
                emoji="➕",
            ),
        )
        if self.app.admin_maintenance:
            self.container.add_text(format_message("maintenance"))


def get_uptime() -> datetime.timedelta:
    return datetime.timedelta(seconds=time.time() - psutil.boot_time())
