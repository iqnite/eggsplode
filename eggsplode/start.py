"""
Contains the StartGameView class which handles the start game view in the Discord bot.
"""

import discord

from .strings import EXPANSIONS, get_message, replace_emojis
from .game_logic import Game
from .action import TurnView


class StartGameView(discord.ui.View):
    def __init__(self, game: Game):
        super().__init__(timeout=600, disable_on_timeout=True)
        self.game = game

    async def on_timeout(self):
        await self.game.events.game_end()
        await super().on_timeout()

    @discord.ui.button(label="Join", style=discord.ButtonStyle.blurple, emoji="👋")
    async def join_game(self, _, interaction: discord.Interaction):
        if not interaction.user:
            return
        game_cancelled = False
        self.game.log.actions = []
        await interaction.edit(view=self)
        if interaction.user.id in self.game.config["players"]:
            self.game.config["players"].remove(interaction.user.id)
            if not (interaction.message and interaction.message.content):
                return
            if not self.game.config["players"]:
                game_cancelled = True
                await self.game.events.game_end()
                self.on_timeout = super().on_timeout
                self.disable_all_items()
            await self.game.log(
                "\n".join(
                    line
                    for line in interaction.message.content.split("\n")
                    if not line.endswith(f"<@{interaction.user.id}>")
                )
                + "\n"
                + (get_message("game_cancelled") if game_cancelled else ""),
                view=self,
            )
            return
        self.game.config["players"].append(interaction.user.id)
        await self.game.log(self.generate_game_start_message(), view=self)

    def generate_game_start_message(self):
        return "\n".join(
            (
                get_message("start"),
                get_message("players"),
                *(
                    get_message("players_list_item").format(player)
                    for player in self.game.config["players"]
                ),
                *(
                    (
                        get_message("expansions"),
                        *(
                            get_message("bold_list_item").format(
                                replace_emojis(EXPANSIONS[expansion]["emoji"]),
                                EXPANSIONS[expansion]["name"],
                            )
                            for expansion in self.game.config.get("expansions", [])
                        ),
                    )
                ),
                (
                    ""
                    if self.game.config.get("expansions", [])
                    else get_message("no_expansions")
                ),
            )
        )

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, emoji="🚀")
    async def start_game(self, _, interaction: discord.Interaction):
        if not (interaction.user and self.message):
            return
        if interaction.user.id != self.game.config["players"][0]:
            await interaction.respond(
                get_message("not_game_creator_start"), ephemeral=True, delete_after=5
            )
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
        await self.game.log(get_message("game_started"), view=self, anchor=interaction)
        await self.game.events.game_start()
        async with TurnView(self.game):
            await self.game.events.turn_start()

    @discord.ui.button(label="Settings", style=discord.ButtonStyle.grey, emoji="⚙️")
    async def settings(self, _, interaction: discord.Interaction):
        if not (interaction.user and self.message):
            return
        if interaction.user.id != self.game.config["players"][0]:
            await interaction.respond(
                get_message("not_game_creator_edit_settings"),
                ephemeral=True,
                delete_after=5,
            )
            return
        await interaction.respond(view=SettingsView(self.game, self), ephemeral=True)

    @discord.ui.button(label="Help", style=discord.ButtonStyle.grey, emoji="❓")
    async def help(self, _, interaction: discord.Interaction):
        if not (interaction.user and self.message):
            return
        await self.game.app.show_help(interaction, ephemeral=True)


class SettingsView(discord.ui.View):
    def __init__(self, game: Game, parent_view: StartGameView):
        super().__init__(timeout=600, disable_on_timeout=True)
        self.game = game
        self.expansion_select: discord.ui.Select | None = None
        self.short_mode_button: discord.ui.Button | None = None
        self.parent_view = parent_view
        self.create_view()

    def create_view(self):
        if self.expansion_select:
            self.remove_item(self.expansion_select)
        if self.short_mode_button:
            self.remove_item(self.short_mode_button)
        self.expansion_select = discord.ui.Select(
            options=[
                discord.SelectOption(
                    value=name,
                    label=expansion["name"],
                    emoji=replace_emojis(expansion["emoji"]),
                    default=name in self.game.config.get("expansions", []),
                )
                for name, expansion in EXPANSIONS.items()
            ],
            placeholder="Eggspansions",
            min_values=0,
            max_values=len(EXPANSIONS),
        )
        self.expansion_select.callback = self.expansion_callback
        self.add_item(self.expansion_select)
        short = self.game.config.get("short", None)
        self.short_mode_button = discord.ui.Button(
            label="Short mode: "
            + ("Auto" if short is None else "On" if short else "Off"),
            style=(
                discord.ButtonStyle.green
                if self.game.config.get("short", False)
                else discord.ButtonStyle.grey
            ),
            emoji="⚡",
        )
        self.short_mode_button.callback = self.short_mode_callback
        self.add_item(self.short_mode_button)

    async def expansion_callback(self, interaction: discord.Interaction):
        if not self.expansion_select:
            return
        self.game.config["expansions"] = self.expansion_select.values
        await interaction.respond(
            get_message("expansions_updated"), ephemeral=True, delete_after=5
        )
        self.game.log.actions = []
        await self.game.log(
            self.parent_view.generate_game_start_message(),
            view=self.parent_view,
        )

    async def short_mode_callback(self, interaction: discord.Interaction):
        self.game.config["short"] = not self.game.config.get("short", False)
        self.create_view()
        await interaction.edit(view=self)

    @discord.ui.button(
        label="Advanced Settings", style=discord.ButtonStyle.grey, emoji="⚙️"
    )
    async def advanced_settings(self, _, interaction: discord.Interaction):
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
                url="https://iqnite.github.io/",
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
