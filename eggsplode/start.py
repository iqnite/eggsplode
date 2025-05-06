"""
Contains the StartGameView class which handles the start game view in the Discord bot.
"""

import discord

from .strings import EXPANSIONS, get_message, replace_emojis
from .game_logic import Game
from .action import TurnView


async def check_permissions(game: Game, interaction: discord.Interaction):
    if not interaction.user:
        return
    if interaction.user.id != game.config["players"][0]:
        await interaction.respond(
            get_message("not_game_creator"),
            ephemeral=True,
            delete_after=5,
        )
        return False
    return True


class StartGameView(discord.ui.View):
    def __init__(self, game: Game):
        super().__init__(timeout=600, disable_on_timeout=True)
        self.game = game
        self.create_settings()
        self.title = discord.ui.TextDisplay(get_message("start"))
        self.add_item(self.title)
        self.players_container = discord.ui.Container()
        self.players_container.add_text(get_message("players"))
        self.players_display = discord.ui.TextDisplay(self.get_players())
        self.players_container.add_item(self.players_display)
        self.add_item(self.players_container)
        self.expansions_container = discord.ui.Container()
        self.expansions_container.add_text(get_message("expansions"))
        self.expansions_container.add_item(self.expansion_select)
        self.add_item(self.expansions_container)
        self.settings_container = discord.ui.Container()
        self.settings_container.add_text(get_message("settings"))
        self.settings_container.add_section(
            discord.ui.TextDisplay(get_message("short_mode")),
            discord.ui.TextDisplay(get_message("short_mode_description")),
            accessory=self.short_mode_button,
        )
        self.settings_container.add_separator()
        self.advanced_settings_button = discord.ui.Button(
            label="View", style=discord.ButtonStyle.grey, emoji="⚙️"
        )
        self.advanced_settings_button.callback = self.advanced_settings
        self.settings_container.add_section(
            discord.ui.TextDisplay(get_message("advanced_settings")),
            accessory=self.advanced_settings_button,
        )
        self.add_item(self.settings_container)
        self.join_game_button = discord.ui.Button(
            label="Join", style=discord.ButtonStyle.blurple, emoji="👋"
        )
        self.join_game_button.callback = self.join_game
        self.add_item(self.join_game_button)
        self.start_game_button = discord.ui.Button(
            label="Start Game", style=discord.ButtonStyle.green, emoji="🚀"
        )
        self.start_game_button.callback = self.start_game
        self.add_item(self.start_game_button)
        self.help_button = discord.ui.Button(
            label="Help", style=discord.ButtonStyle.grey, emoji="❓"
        )
        self.help_button.callback = self.help
        self.add_item(self.help_button)

    async def on_timeout(self):
        await self.game.events.game_end()
        await super().on_timeout()

    async def join_game(self, interaction: discord.Interaction):
        if not interaction.user:
            return
        if interaction.user.id in self.game.config["players"]:
            self.game.config["players"].remove(interaction.user.id)
            if not self.game.config["players"]:
                await self.game.events.game_end()
                self.on_timeout = super().on_timeout
                self.stop()
                self.remove_item(self.players_container)
                self.remove_item(self.expansions_container)
                self.remove_item(self.settings_container)
                self.remove_item(self.join_game_button)
                self.remove_item(self.start_game_button)
                self.remove_item(self.help_button)
                self.title.content = get_message("game_cancelled")
                await interaction.edit(view=self)
                return
        else:
            self.game.config["players"].append(interaction.user.id)
        self.players_display.content = self.get_players()
        await interaction.edit(view=self)

    def get_players(self):
        return "\n".join(
            get_message("players_list_item").format(player)
            for player in self.game.config["players"]
        )

    def get_expansions(self):
        return "\n".join(
            (
                *(
                    get_message("bold_list_item").format(
                        replace_emojis(EXPANSIONS[expansion]["emoji"]),
                        EXPANSIONS[expansion]["name"],
                    )
                    for expansion in self.game.config.get("expansions", [])
                ),
                (
                    ""
                    if self.game.config.get("expansions", [])
                    else get_message("no_expansions")
                ),
            )
        )

    async def start_game(self, interaction: discord.Interaction):
        if not await check_permissions(self.game, interaction):
            return
        if len(self.game.config["players"]) < 2:
            await interaction.respond(
                get_message("not_enough_players_to_start"),
                ephemeral=True,
                delete_after=5,
            )
            return
        await interaction.response.defer()
        self.stop()
        self.game.start()
        await self.game.log(
            "\n".join(
                (
                    get_message("game_started"),
                    get_message("players"),
                    self.get_players(),
                    get_message("expansions"),
                    self.get_expansions(),
                )
            ),
            view=self,
            anchor=interaction,
        )
        await self.game.events.game_start()
        async with TurnView(self.game):
            await self.game.events.turn_start()

    async def help(self, interaction: discord.Interaction):
        await self.game.app.show_help(interaction, ephemeral=True)

    def create_settings(self):
        self.expansion_select = discord.ui.Select(
            options=self.generate_expansion_options(),
            placeholder=get_message("no_expansions"),
            min_values=0,
            max_values=len(EXPANSIONS),
        )
        self.expansion_select.callback = self.expansion_callback
        self.short_mode_button = discord.ui.Button()
        self.update_short_mode_button()
        self.short_mode_button.callback = self.short_mode_callback

    def update_short_mode_button(self):
        short = self.game.config.get("short", None)
        short_mode_states = {
            None: ("⚡", "Auto"),
            True: ("⏩", "On"),
            False: ("🕒", "Off"),
        }
        self.short_mode_button.emoji, self.short_mode_button.label = short_mode_states[
            short
        ]
        self.short_mode_button.style = (
            discord.ButtonStyle.green
            if self.game.config.get("short", False)
            else discord.ButtonStyle.grey
        )

    def generate_expansion_options(self):
        return [
            discord.SelectOption(
                value=name,
                label=expansion["name"],
                emoji=replace_emojis(expansion["emoji"]),
                default=name in self.game.config.get("expansions", []),
            )
            for name, expansion in EXPANSIONS.items()
        ]

    async def expansion_callback(self, interaction: discord.Interaction):
        if not self.expansion_select or not await check_permissions(
            self.game, interaction
        ):
            return
        self.game.config["expansions"] = self.expansion_select.values
        self.expansion_select.options = self.generate_expansion_options()
        await interaction.edit(view=self)

    async def short_mode_callback(self, interaction: discord.Interaction):
        if not await check_permissions(self.game, interaction):
            return
        self.game.config["short"] = not self.game.config.get("short", False)
        self.update_short_mode_button()
        await interaction.edit(view=self)

    async def advanced_settings(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SettingsModal(game=self.game, title="Advanced Settings")
        )


class SettingsModal(discord.ui.Modal):
    def __init__(self, game: Game, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.game = game
        self.inputs = {
            "deck_eggsplode_cards": {
                "input": discord.ui.InputText(
                    label="Eggsplode cards in deck",
                    placeholder=str(len(self.game.config["players"]) - 1),
                    value=self.game.config.get("deck_eggsplode_cards", None),
                    required=False,
                ),
                "min": 1,
            },
            "deck_defuse_cards": {
                "input": discord.ui.InputText(
                    label="Defuse cards in deck",
                    placeholder="0",
                    value=self.game.config.get("deck_defuse_cards", None),
                    required=False,
                ),
            },
            # "turn_timeout": {
            #     "input": discord.ui.InputText(
            #         label="Turn timer (in seconds; 40-600)",
            #         placeholder="60",
            #         value=self.game.config.get("turn_timeout", None),
            #         required=False,
            #     ),
            #     "min": 40,
            #     "max": 600,
            # },
        }
        for _, i in self.inputs.items():
            self.add_item(i["input"])

    async def callback(self, interaction: discord.Interaction):
        if not self.game:
            return
        if not await check_permissions(self.game, interaction):
            return
        response = get_message("settings_updated")
        for input_name, item in self.inputs.items():
            item_input = item["input"]
            if item_input.value == "":
                self.game.config.pop(input_name, None)
                response += "\n" + get_message("settings_updated_success").format(
                    item_input.label, item_input.placeholder
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
                response += "\n" + get_message("settings_updated_error").format(
                    item_input.label, item_input.value, validation[1]
                )
                continue
            self.game.config[input_name] = item_input.value
            response += "\n" + get_message("settings_updated_success").format(
                item_input.label, item_input.value
            )
        await interaction.respond(response, ephemeral=True, delete_after=5)

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
        self.add_item(
            discord.ui.Button(
                label="Website",
                url="https://iqnite.github.io/eggsplode",
                style=discord.ButtonStyle.link,
                emoji=replace_emojis("🌐"),
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Support & Community server",
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
                label="Invite to your server",
                url="https://discord.com/oauth2/authorize?client_id=1325443178622484590",
                style=discord.ButtonStyle.link,
                emoji="🤖",
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

    @discord.ui.select(
        placeholder="Section",
        options=[
            discord.SelectOption(label="Getting started", emoji="🚀", value="0"),
            discord.SelectOption(label="Cards (1)", emoji="🎴", value="1"),
            discord.SelectOption(label="Cards (2)", emoji="🎴", value="2"),
            discord.SelectOption(label="Eggspansions", emoji="🧩", value="3"),
            discord.SelectOption(label="Credits", emoji="👏", value="4"),
        ],
        max_values=1,
        min_values=1,
    )
    async def section_callback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        assert isinstance(select.values[0], str)
        await interaction.edit(content=get_message(f"help{int(select.values[0])}"))
