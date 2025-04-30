"""
Contains the Nope views for the game.
"""

from typing import Callable, Coroutine
import discord
from .game_logic import Game
from .strings import get_message
from .base_views import BaseView


class NopeView(BaseView):
    def __init__(
        self,
        game: Game,
        ok_callback_action: (
            Callable[[discord.Interaction | None], Coroutine] | None
        ) = None,
        nope_callback_action: Callable[[], None] | None = None,
        timeout=5,
    ):
        super().__init__(game, timeout=timeout)
        self.ok_callback_action = ok_callback_action
        self.nope_callback_action = nope_callback_action
        self.nope_count = 0
        self.disabled = False

    async def on_timeout(self):
        if not self.disabled:
            self.disabled = True
            if not self.nope_count % 2 and self.ok_callback_action:
                await self.ok_callback_action(None)
            else:
                await self.game.events.action_end()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        base_check = await super().interaction_check(interaction)
        return (
            base_check
            and interaction.user is not None
            and interaction.user.id in self.game.players
            and not self.disabled
        )

    @discord.ui.button(label="Nope!", style=discord.ButtonStyle.red, emoji="🛑")
    async def nope_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if not interaction.user:
            return
        if (
            not self.nope_count % 2
            and self.game.current_player_id == interaction.user.id
        ):
            await interaction.respond(
                get_message("no_self_nope"), ephemeral=True, delete_after=5
            )
            return
        try:
            self.game.hands[interaction.user.id].remove("nope")
        except ValueError:
            await interaction.respond(
                get_message("no_nope_cards"), ephemeral=True, delete_after=5
            )
            return
        self.nope_count += 1
        button.label = "Nope!" if not self.nope_count % 2 else "Yup!"
        for i in range(len(self.game.log) - self.nope_count, len(self.game.log)):
            self.game.log[i] = (
                self.game.log[i].strip("~~")
                if self.game.log[i].startswith("~~")
                else "~~" + self.game.log[i] + "~~"
            )
        await self.game.log(
            (
                get_message("message_edit_on_nope").format(interaction.user.id)
                if self.nope_count % 2
                else get_message("message_edit_on_yup").format(interaction.user.id)
            ),
            view=self,
            anchor=interaction,
        )


class ExplicitNopeView(NopeView):
    def __init__(
        self,
        game: Game,
        target_player_id: int,
        ok_callback_action: Callable[[discord.Interaction | None], Coroutine],
        nope_callback_action: Callable[[], None] | None = None,
        timeout=10,
    ):
        super().__init__(
            game, ok_callback_action, nope_callback_action, timeout=timeout
        )
        self.target_player_id = target_player_id

    @discord.ui.button(label="OK!", style=discord.ButtonStyle.green, emoji="✅")
    async def ok_callback(self, _, interaction: discord.Interaction):
        if not interaction.user:
            return
        if interaction.user.id != self.target_player_id:
            await interaction.respond(
                get_message("not_your_turn"), ephemeral=True, delete_after=5
            )
            return
        if self.nope_count % 2:
            await interaction.respond(
                get_message("action_noped"), ephemeral=True, delete_after=5
            )
            return
        self.game.log.anchor_interaction = interaction
        self.disabled = True
        if self.ok_callback_action:
            await self.ok_callback_action(interaction)
