"""
Contains the StartGameView class which handles the start game view in the Discord bot.
"""

import discord
from strings import MESSAGES
from game_logic import ActionContext
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
        if interaction.user.id in self.ctx.game.players:
            self.ctx.game.players.remove(interaction.user.id)
            if not (interaction.message and interaction.message.content):
                return
            if not self.ctx.game.players:
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
        self.ctx.game.players.append(interaction.user.id)
        if not (interaction.message and interaction.message.content):
            return
        await interaction.edit(
            content=interaction.message.content
            + "\n"
            + MESSAGES["players_list_item"].format(interaction.user.id),
            view=self,
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
        if interaction.user.id != self.ctx.game.players[0]:
            await interaction.respond(
                MESSAGES["not_game_creator_start"], ephemeral=True
            )
            return
        if len(self.ctx.game.players) < 2:
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
        if interaction.user.id != self.ctx.game.players[0]:
            await interaction.respond(
                MESSAGES["not_game_creator_edit_settings"], ephemeral=True
            )
            return

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
                emoji="🌐",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Support & Community server",
                url="https://discord.gg/UGm36FkGDF",
                style=discord.ButtonStyle.link,
                emoji="💬",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="GitHub",
                url="https://github.com/iqnite/eggsplode",
                style=discord.ButtonStyle.link,
                emoji="🐙",
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
