"""
Contains the Nope views for the game.
"""

from datetime import datetime, timedelta
from typing import Callable, Coroutine, TYPE_CHECKING
import discord
from eggsplode.strings import get_message
from eggsplode.base_views import BaseView

if TYPE_CHECKING:
    from eggsplode.core import Game


class NopeView(BaseView):
    def __init__(
        self,
        game: "Game",
        message: str,
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
        self.disabled = False
        self.action_text_display = discord.ui.TextDisplay(message)
        self.add_item(self.action_text_display)
        self.button_container = discord.ui.Container()
        self.nope_button = discord.ui.Button(
            label="Nope!", style=discord.ButtonStyle.red, emoji="🛑"
        )
        self.nope_button.callback = self.nope_callback
        self.button_container.add_item(self.nope_button)
        self.add_item(self.button_container)
        self.timer_display = discord.ui.TextDisplay(self.timer_text)
        self.add_item(self.timer_display)

    @property
    def timer_text(self) -> str:
        return (
            get_message("timer").format(
                int((datetime.now() + timedelta(seconds=self.timeout)).timestamp()),
            )
            if self.timeout
            else ""
        )

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            if not self.disabled:
                self.disabled = True
                self.stop()
                if not self.nope_count % 2 and self.ok_callback_action:
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
        else:
            self.nope_count += 1
            self.nope_button.label = "Nope!" if not self.nope_count % 2 else "Yup!"
            self.toggle_strike_through()
            self.action_messages.append(
                get_message("message_edit_on_nope").format(interaction.user.id)
                if self.nope_count % 2
                else get_message("message_edit_on_yup").format(interaction.user.id)
            )
            self.action_text_display.content = "\n".join(self.action_messages)
        self.timer_display.content = self.timer_text
        self.game.anchor_interaction = interaction
        await interaction.edit(view=self)


class ExplicitNopeView(NopeView):
    def __init__(
        self,
        game: "Game",
        message: str,
        target_player_id: int,
        ok_callback_action: Callable[[discord.Interaction | None], Coroutine],
        nope_callback_action: Callable[[], None] | None = None,
        timeout=10,
    ):
        super().__init__(
            game, message, ok_callback_action, nope_callback_action, timeout=timeout
        )
        self.target_player_id = target_player_id
        self.ok_button = discord.ui.Button(
            label="OK!", style=discord.ButtonStyle.green, emoji="✅"
        )
        self.ok_button.callback = self.ok_callback
        self.button_container.add_item(self.ok_button)

    async def ok_callback(self, interaction: discord.Interaction):
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
        self.game.anchor_interaction = interaction
        self.disabled = True
        self.stop()
        self.disable_all_items()
        self.remove_item(self.nope_button)
        self.remove_item(self.ok_button)
        await interaction.edit(view=self)
        if self.ok_callback_action:
            await self.ok_callback_action(interaction)
