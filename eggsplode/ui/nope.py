"""
Contains the Nope views for the game.
"""

from datetime import datetime, timedelta
from typing import Callable, Coroutine, TYPE_CHECKING
import discord
from eggsplode.strings import format_message
from eggsplode.ui.base import BaseView, TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


class NopeView(BaseView):
    def __init__(
        self,
        game: "Game",
        message: str,
        target_player_id: int | None = None,
        ok_callback_action: (
            Callable[[discord.Interaction | None], Coroutine] | None
        ) = None,
        nope_callback_action: Callable[[], None] | None = None,
        timeout=10,
    ):
        super().__init__(game, timeout=timeout)
        self.game = game
        self.action_messages = [message]
        self.ok_callback_action = ok_callback_action
        self.nope_callback_action = nope_callback_action
        self.nope_count = 0
        self.players_confirmed = set()
        self.disabled = False
        self.action_text_display = discord.ui.TextDisplay(message)
        self.add_item(self.action_text_display)
        self.timer_display = discord.ui.TextDisplay(self.timer_text)
        self.add_item(self.timer_display)
        self.nope_button = discord.ui.Button(
            label="Nope!", style=discord.ButtonStyle.red, emoji="🛑"
        )
        self.nope_button.callback = self.nope_callback
        self.add_item(self.nope_button)
        self.target_player_id = target_player_id
        self.ok_button = discord.ui.Button(
            label=self.ok_label,
            style=discord.ButtonStyle.green,
            emoji="✅",
        )
        self.ok_button.callback = self.ok_callback
        self.add_item(self.ok_button)

    @property
    def ok_label(self) -> str:
        return "OK!" + (
            f" ({len(self.players_confirmed)}/{len(self.game.players) - 1})"
            if self.target_player_id is None
            else ""
        )

    @property
    def timer_text(self) -> str:
        return (
            format_message(
                "timer",
                int((datetime.now() + timedelta(seconds=self.timeout)).timestamp()),
            )
            if self.timeout
            else ""
        )

    @property
    def noped(self) -> bool:
        return self.nope_count % 2 == 1

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            if not self.disabled:
                self.disabled = True
                self.stop()
                if not self.noped and self.ok_callback_action:
                    await self.ok_callback_action(None)
                else:
                    await self.game.events.action_end()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return (
            await super().interaction_check(interaction)
            and interaction.user is not None
            and interaction.user.id in self.game.players
            and not self.disabled
        )

    def toggle_strike_through(self):
        for i, line in enumerate(self.action_messages):
            self.action_messages[i] = (
                line.strip("~~") if line.startswith("~~") else "~~" + line + "~~"
            )

    async def nope_callback(self, interaction: discord.Interaction):
        self.timer_display.content = self.timer_text
        if not interaction.user:
            await interaction.edit(view=self)
            raise ValueError("Interaction user is None")
        if not self.noped and self.game.current_player_id == interaction.user.id:
            await interaction.respond(
                view=TextView("no_self_nope"), ephemeral=True, delete_after=5
            )
            await interaction.edit(view=self)
            return
        try:
            self.game.hands[interaction.user.id].remove("nope")
        except (ValueError, KeyError):
            await interaction.edit(view=self)
            await interaction.respond(
                view=TextView("no_nope_cards"), ephemeral=True, delete_after=5
            )
        else:
            self.nope_count += 1
            self.nope_button.label = "Nope!" if not self.noped else "Yup!"
            self.toggle_strike_through()
            self.action_messages.append(
                format_message("message_edit_on_nope", interaction.user.id)
                if self.noped
                else format_message("message_edit_on_yup", interaction.user.id)
            )
            self.action_text_display.content = "\n".join(self.action_messages)
            if self.noped:
                self.remove_item(self.ok_button)
            else:
                self.add_item(self.ok_button)
        await interaction.edit(view=self)

    async def ok_callback(self, interaction: discord.Interaction):
        self.timer_display.content = self.timer_text
        if not interaction.user:
            await interaction.edit(view=self)
            return
        if self.noped:
            await interaction.edit(view=self)
            await interaction.respond(
                view=TextView("action_noped"), ephemeral=True, delete_after=5
            )
            return
        if self.target_player_id is None:
            if self.game.current_player_id == interaction.user.id:
                await interaction.respond(
                    view=TextView("no_self_ok"), ephemeral=True, delete_after=5
                )
                await interaction.edit(view=self)
                return
            if interaction.user.id in self.players_confirmed:
                self.players_confirmed.remove(interaction.user.id)
            else:
                self.players_confirmed.add(interaction.user.id)
            self.ok_button.label = self.ok_label
            await interaction.edit(view=self)
            if len(self.players_confirmed) == len(self.game.players) - 1:
                await self.finish_confirmation(interaction)
            return
        if interaction.user.id != self.target_player_id:
            await interaction.respond(
                view=TextView("not_your_turn"), ephemeral=True, delete_after=5
            )
            await interaction.edit(view=self)
            return
        await self.finish_confirmation(interaction)

    async def finish_confirmation(self, interaction: discord.Interaction):
        self.game.anchor_interaction = interaction
        self.disabled = True
        self.stop()
        self.disable_all_items()
        self.remove_item(self.nope_button)
        self.remove_item(self.ok_button)
        await interaction.edit(view=self)
        if self.ok_callback_action:
            await self.ok_callback_action(interaction)
