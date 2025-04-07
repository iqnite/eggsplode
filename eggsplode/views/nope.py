"""
Contains the Nope views for the game.
"""

from collections.abc import Callable, Coroutine
import discord
from ..ctx import ActionContext, EventController
from ..strings import get_message
from .base import BaseView


class NopeView(BaseView):
    def __init__(
        self,
        ctx: ActionContext,
        ok_callback_action: (
            Callable[[discord.Interaction | None], Coroutine] | None
        ) = None,
        nope_callback_action: Callable[[], None] | None = None,
        timeout=5,
    ):
        super().__init__(ctx, timeout=timeout)
        self.ok_callback_action = ok_callback_action
        self.nope_callback_action = nope_callback_action
        self.nope_count = 0
        self.disabled = False

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            if not self.disabled:
                self.disabled = True
                self.on_timeout = super().on_timeout
                if self.ctx.action_id == self.ctx.game.action_id:
                    if not self.nope_count % 2 and self.ok_callback_action:
                        await self.ok_callback_action(None)
                    else:
                        await self.ctx.events.notify(EventController.ACTION_END)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        base_check = await super().interaction_check(interaction)
        return (
            base_check
            and interaction.user is not None
            and interaction.user.id in self.ctx.game.players
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
            and self.ctx.game.current_player_id == interaction.user.id
        ):
            await interaction.respond(
                get_message("no_self_nope"), ephemeral=True, delete_after=5
            )
            return
        try:
            self.ctx.game.hands[interaction.user.id].remove("nope")
        except ValueError:
            await interaction.respond(
                get_message("no_nope_cards"), ephemeral=True, delete_after=5
            )
            return
        self.nope_count += 1
        button.label = "Nope!" if not self.nope_count % 2 else "Yup!"
        for i in range(len(self.ctx.log) - self.nope_count, len(self.ctx.log)):
            self.ctx.log[i] = (
                self.ctx.log[i].strip("~~")
                if self.ctx.log[i].startswith("~~")
                else "~~" + self.ctx.log[i] + "~~"
            )
        self.ctx.log.anchor_interaction = interaction
        await self.ctx.log(
            (
                get_message("message_edit_on_nope").format(interaction.user.id)
                if self.nope_count % 2
                else get_message("message_edit_on_yup").format(interaction.user.id)
            ),
            view=self,
        )


class ExplicitNopeView(NopeView):
    def __init__(
        self,
        ctx: ActionContext,
        target_player_id: int,
        ok_callback_action: Callable[[discord.Interaction | None], Coroutine],
        nope_callback_action: Callable[[], None] | None = None,
        timeout=10,
    ):
        super().__init__(ctx, ok_callback_action, nope_callback_action, timeout=timeout)
        self.target_player_id = target_player_id

    @discord.ui.button(label="OK!", style=discord.ButtonStyle.green, emoji="✅")
    async def ok_callback(self, _: discord.ui.Button, interaction: discord.Interaction):
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
        self.ctx.log.anchor_interaction = interaction
        self.disabled = True
        self.disable_all_items()
        if self.ok_callback_action:
            await self.ok_callback_action(interaction)
