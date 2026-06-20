"""
Contains the Nope views for the game.
"""

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Callable, Coroutine

import discord

from eggsplode import strings
from eggsplode.strings import format_message
from eggsplode.ui.base import BaseGameView, TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


class NopeView(BaseGameView):
    def __init__(
        self,
        game: "Game",
        message: str,
        target_player_id: int | None = None,
        ok_callback_action: (
            Callable[[discord.Interaction | None], Coroutine] | None
        ) = None,
        nope_callback_action: Callable[[], None] | None = None,
        timeout: float | None = None,
    ):
        super().__init__(game, timeout=None)
        if timeout is None:
            timeout = (
                strings.NOPE_TIMEOUT
                if target_player_id is None
                else strings.EXPLICIT_NOPE_TIMEOUT
            )
        self.nope_timeout = timeout
        self._is_timer_awaiting_reset = False
        self.game = game
        self.action_messages = [message]
        self.target_player_id = target_player_id
        self.ok_callback_action = ok_callback_action
        self.nope_callback_action = nope_callback_action
        self.nope_count = 0
        self.players_confirmed = set()
        self._timer_task: asyncio.Task[None] | None = None
        self.action_text_display = discord.ui.TextDisplay(message)
        self.add_item(self.action_text_display)
        self.timer_display = discord.ui.TextDisplay(self.get_timer_text())
        self.add_item(self.timer_display)
        self.nope_button = discord.ui.Button(
            label=format_message("nope_button"),
            style=discord.ButtonStyle.red,
            emoji="🛑",
        )
        self.nope_button.callback = self.nope_callback
        self.ok_button = discord.ui.Button(
            label=self.ok_label,
            style=discord.ButtonStyle.green,
            emoji="✅",
        )
        self.ok_button.callback = self.ok_callback
        self.action_row = discord.ui.ActionRow(self.nope_button, self.ok_button)
        self.add_item(self.action_row)

    async def start_timer(self):
        if self._timer_task is not None and not self._timer_task.done():
            self._timer_task.cancel()
        self._timer_task = asyncio.create_task(self._run_timer())

    async def _run_timer(self):
        try:
            start_time = datetime.now()
            while True:
                if self._is_timer_awaiting_reset:
                    self._is_timer_awaiting_reset = False
                    start_time = datetime.now()
                if datetime.now() - start_time >= timedelta(seconds=self.nope_timeout):
                    break
                await asyncio.sleep(0.1)
            await self.on_nope_timeout()
        except asyncio.CancelledError:
            pass

    async def edit(self, interaction: discord.Interaction | None = None):
        if self.message is None:
            if interaction is None:
                raise ValueError(
                    "Cannot edit NopeView if both message and interaction are None."
                )
            await interaction.edit(view=self)
        else:
            await self.message.edit(view=self)

    def reset_timeout(self):
        self._is_timer_awaiting_reset = True

    @property
    def ok_label(self) -> str:
        return format_message("ok_button") + (
            f" ({len(self.players_confirmed)}/{len(self.game.players) - 1})"
            if self.target_player_id is None
            else ""
        )

    def get_timer_text(self, timeout=None) -> str:
        if timeout is None:
            timeout = self.nope_timeout
        return (
            format_message(
                "timer",
                int((datetime.now() + timedelta(seconds=timeout)).timestamp()),
            )
            if self.nope_timeout
            else ""
        )

    @property
    def is_noped(self) -> bool:
        return self.nope_count % 2 == 1

    async def on_nope_timeout(self):
        if not self.is_ignoring_interactions:
            self.ignore_interactions()
            if not self.is_noped and self.ok_callback_action:
                await self.ok_callback_action(None)
            else:
                await self.game.events.action_end()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return (
            await super().interaction_check(interaction)
            and interaction.user is not None
            and interaction.user.id in self.game.players
            and not self.is_ignoring_interactions
        )

    def toggle_strike_through(self):
        for i, line in enumerate(self.action_messages):
            self.action_messages[i] = (
                line.strip("~~") if line.startswith("~~") else "~~" + line + "~~"
            )

    async def nope_callback(self, interaction: discord.Interaction):
        if not interaction.user:
            await interaction.edit(view=self)
            return
        if not self.is_noped and self.game.action_player_id == interaction.user.id:
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
            return
        self.reset_timeout()
        self.timer_display.content = self.get_timer_text()
        self.nope_count += 1
        self.nope_button.label = (
            format_message("nope_button")
            if not self.is_noped
            else format_message("yup_button")
        )
        self.toggle_strike_through()
        self.action_messages.append(
            format_message("message_edit_on_nope", interaction.user.id)
            if self.is_noped
            else format_message("message_edit_on_yup", interaction.user.id)
        )
        self.action_text_display.content = "\n".join(self.action_messages)
        if self.is_noped:
            self.action_row.remove_item(self.ok_button)
        else:
            self.action_row.add_item(self.ok_button)
        await interaction.edit(view=self)

    async def ok_callback(self, interaction: discord.Interaction):
        if not interaction.user:
            await interaction.edit(view=self)
            return
        if self.is_noped:
            await interaction.edit(view=self)
            await interaction.respond(
                view=TextView("action_noped"), ephemeral=True, delete_after=5
            )
            return
        if self.target_player_id is None:
            if self.game.action_player_id == interaction.user.id:
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
            if len(self.players_confirmed) == len(self.game.players) - 1:
                await self.finish_confirmation(interaction)
                return
            await interaction.edit(view=self)
            return
        if interaction.user.id != self.target_player_id:
            await interaction.respond(
                view=TextView("not_your_turn"), ephemeral=True, delete_after=5
            )
            await interaction.edit(view=self)
            return
        await self.finish_confirmation(interaction)

    async def finish_confirmation(self, interaction: discord.Interaction):
        self.game.last_interaction = interaction
        self.ignore_interactions()
        if self._timer_task is not None and not self._timer_task.done():
            self._timer_task.cancel()
        try:
            self.disable_all_items()
            await interaction.edit(view=self)
        finally:
            if self.ok_callback_action:
                await self.ok_callback_action(interaction)
