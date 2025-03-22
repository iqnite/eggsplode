"""
Contains the StartGameView class which handles the start game view in the Discord bot.
"""

import discord
from ..strings import EMOJIS, EXPANSIONS, MESSAGES
from ..ctx import ActionContext
from .base import BaseView
from .action import TurnView


class StartGameView(BaseView):
    """
    A view that allows users to join and start a game.

    Attributes:
        ctx (ActionContext): The context of the action.
    """

    def __init__(self, ctx: ActionContext):
        """
        Initializes the StartGameView with the given context.

        Args:
            ctx (ActionContext): The context of the action.
        """
        super().__init__(ctx, timeout=600)

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Exits the context manager.
        """
        if self.message is None:
            del self.ctx.games[self.ctx.game_id]
            self.on_timeout = super().on_timeout
            self.disable_all_items()

    async def on_timeout(self):
        """
        Handles the timeout event by deleting the game from the context.
        """
        del self.ctx.games[self.ctx.game_id]
        await super().on_timeout()

    @discord.ui.button(label="Join", style=discord.ButtonStyle.blurple, emoji="👋")
    async def join_game(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the join game button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if not interaction.user:
            return
        game_cancelled = False
        if interaction.user.id in self.ctx.game.config["players"]:
            self.ctx.game.config["players"].remove(interaction.user.id)
            if not (interaction.message and interaction.message.content):
                return
            if not self.ctx.game.config["players"]:
                game_cancelled = True
                del self.ctx.games[self.ctx.game_id]
                self.on_timeout = super().on_timeout
                self.disable_all_items()
            await interaction.edit(
                content="\n".join(
                    line
                    for line in interaction.message.content.split("\n")
                    if not line.endswith(f"<@{interaction.user.id}>")
                )
                + "\n"
                + (MESSAGES["game_cancelled"] if game_cancelled else ""),
                view=self,
            )
            return
        self.ctx.game.config["players"].append(interaction.user.id)
        await interaction.edit(
            content=self.generate_game_start_message(),
            view=self,
        )

    def generate_game_start_message(self):
        """
        Generates the game start message.
        """
        return "\n".join(
            (
                MESSAGES["start"].format(self.ctx.game.config["players"][0]),
                MESSAGES["players"],
                *(
                    MESSAGES["players_list_item"].format(player)
                    for player in self.ctx.game.config["players"]
                ),
                *(
                    (
                        MESSAGES["expansions"]
                        + " "
                        + EMOJIS.get("new1", "🆕")
                        + EMOJIS.get("new2", ""),
                        *(
                            MESSAGES["bold_list_item"].format(
                                EXPANSIONS[expansion]["emoji"],
                                EXPANSIONS[expansion]["name"],
                            )
                            for expansion in self.ctx.game.config.get("expansions", [])
                        ),
                    )
                ),
                (
                    ""
                    if self.ctx.game.config.get("expansions", [])
                    else MESSAGES["no_expansions"]
                ),
            )
        )

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, emoji="🚀")
    async def start_game(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the start game button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if not (interaction.user and self.message):
            return
        if interaction.user.id != self.ctx.game.config["players"][0]:
            await interaction.respond(
                MESSAGES["not_game_creator_start"], ephemeral=True
            )
            return
        if len(self.ctx.game.config["players"]) < 2:
            await interaction.respond(
                MESSAGES["not_enough_players_to_start"], ephemeral=True
            )
            return
        self.on_timeout = super().on_timeout
        self.ctx.game.start()
        self.disable_all_items()
        await interaction.edit(view=self)
        await interaction.respond(MESSAGES["game_started"], ephemeral=True)
        async with TurnView(self.ctx.copy(), parent_interaction=interaction) as view:
            view.message = await interaction.respond(
                MESSAGES["next_turn"].format(self.ctx.game.current_player_id), view=view
            )

    @discord.ui.button(label="Settings", style=discord.ButtonStyle.grey, emoji="⚙️")
    async def settings(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the settings button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if not (interaction.user and self.message):
            return
        if interaction.user.id != self.ctx.game.config["players"][0]:
            await interaction.respond(
                MESSAGES["not_game_creator_edit_settings"], ephemeral=True
            )
            return
        await interaction.respond(
            view=SettingsView(self.ctx.copy(), self), ephemeral=True
        )

    @discord.ui.button(label="Help", style=discord.ButtonStyle.grey, emoji="❓")
    async def help(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the help button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if not (interaction.user and self.message):
            return
        await self.ctx.app.show_help(interaction, ephemeral=True)


class SettingsView(BaseView):
    """
    A view for the settings command in the game.
    """

    def __init__(
        self,
        ctx: ActionContext,
        parent_view: StartGameView,
    ):
        """
        Initializes the SettingsView.
        """
        super().__init__(ctx)
        self.parent_view = parent_view
        self.expansion_select = discord.ui.Select(
            options=[
                discord.SelectOption(
                    value=name,
                    label=expansion["name"],
                    emoji=expansion["emoji"],
                    default=name in self.ctx.game.config.get("expansions", []),
                )
                for name, expansion in EXPANSIONS.items()
            ],
            placeholder="Eggspansions",
            min_values=0,
            max_values=len(EXPANSIONS),
        )
        self.expansion_select.callback = self.expansion_callback
        self.add_item(self.expansion_select)

    async def expansion_callback(self, interaction: discord.Interaction):
        """
        Handles the expansion select interaction.

        Args:
            select (discord.ui.Select): The select interaction.
            interaction (discord.Interaction): The interaction object.
        """
        self.ctx.game.config["expansions"] = self.expansion_select.values
        await interaction.respond(MESSAGES["expansions_updated"], ephemeral=True)
        assert self.parent_view.message
        await self.parent_view.message.edit(
            content=self.parent_view.generate_game_start_message(),
            view=self.parent_view,
        )

    @discord.ui.button(
        label="Advanced Settings", style=discord.ButtonStyle.grey, emoji="⚙️"
    )
    async def advanced_settings(
        self, _: discord.ui.Button, interaction: discord.Interaction
    ):
        """
        Handles the advanced settings button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.send_modal(
            SettingsModal(ctx=self.ctx, title="Advanced Settings")
        )


class SettingsModal(discord.ui.Modal):
    """
    A modal for the Advanced Settings command.
    """

    def __init__(self, ctx: ActionContext, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ctx = ctx
        self.inputs = {
            "deck_eggsplode_cards": {
                "input": discord.ui.InputText(
                    label="Eggsplode cards in deck",
                    placeholder=str(len(self.ctx.game.config["players"]) - 1),
                    value=self.ctx.game.config.get("deck_eggsplode_cards", None),
                    required=False,
                ),
                "min": 1,
            },
            "deck_defuse_cards": {
                "input": discord.ui.InputText(
                    label="Defuse cards in deck",
                    placeholder="0",
                    value=self.ctx.game.config.get("deck_defuse_cards", None),
                    required=False,
                ),
            },
            "turn_timeout": {
                "input": discord.ui.InputText(
                    label="Turn timer (in seconds; 40-600)",
                    placeholder="60",
                    value=self.ctx.game.config.get("turn_timeout", None),
                    required=False,
                ),
                "min": 40,
                "max": 600,
            },
        }
        for _, i in self.inputs.items():
            self.add_item(i["input"])

    async def callback(self, interaction: discord.Interaction):
        if self.ctx.game_id not in self.ctx.games:
            return
        response = MESSAGES["settings_updated"]
        for input_name, item in self.inputs.items():
            item_input = item["input"]
            if item_input.value == "":
                self.ctx.game.config.pop(input_name, None)
                response += "\n" + MESSAGES["settings_updated_success"].format(
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
                response += "\n" + MESSAGES["settings_updated_error"].format(
                    item_input.label, item_input.value, validation[1]
                )
                continue
            self.ctx.game.config[input_name] = item_input.value
            response += "\n" + MESSAGES["settings_updated_success"].format(
                item_input.label, item_input.value
            )
        await interaction.respond(response, ephemeral=True)

    @staticmethod
    def validate(value, required_type=None, min_value=None, max_value=None):
        """
        Validates the given value.

        Args:
            value: The value to validate.
            required_type: The required type of the value.
            min_value: The minimum value of the value.
            max_value: The maximum value of the value.

        Returns:
            tuple: A boolean indicating if the value is valid and an error message
        """

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
    """
    A view for the help command in the game.
    """

    def __init__(self):
        """
        Initializes the HelpView.
        """
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Website",
                url="https://iqnite.github.io/eggsplode",
                style=discord.ButtonStyle.link,
                emoji=EMOJIS.get("iqbit", "🌐"),
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Support & Community server",
                url="https://discord.gg/UGm36FkGDF",
                style=discord.ButtonStyle.link,
                emoji=EMOJIS.get("discord", "💬")
            )
        )
        self.add_item(
            discord.ui.Button(
                label="GitHub",
                url="https://github.com/iqnite/eggsplode",
                style=discord.ButtonStyle.link,
                emoji=EMOJIS.get("github", "🐙"),
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
        """
        Handles the section select interaction.

        Args:
            select (discord.ui.Select): The select interaction.
            interaction (discord.Interaction): The interaction object.
        """
        assert isinstance(select.values[0], str)
        await interaction.edit(
            content="\n".join(MESSAGES["help"][int(select.values[0])])
        )
