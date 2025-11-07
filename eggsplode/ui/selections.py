"""
Contains the views for the short interactions in the game, such as "Defuse".
"""

from typing import Callable, Coroutine, TYPE_CHECKING
import discord

from eggsplode.strings import format_message, tooltip

if TYPE_CHECKING:
    from eggsplode.core import Game


class SelectionView(discord.ui.View):
    def __init__(self, timeout: int = 20):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.confirm_button = discord.ui.Button(
            label="Confirm", style=discord.ButtonStyle.green, emoji="✅"
        )
        self.confirm_button.callback = self.confirm

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    async def finish(self, interaction: discord.Interaction | None = None):
        pass

    async def confirm(self, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.edit(view=self)
        self.stop()
        await self.finish(interaction)


class ChoosePlayerView(discord.ui.DesignerView):
    def __init__(
        self,
        game: "Game",
        callback_action: Callable[[int], Coroutine],
        condition: Callable[[int], bool] = lambda _: True,
    ):
        super().__init__(timeout=20, disable_on_timeout=True)
        self.game = game
        self.eligible_players = [
            user_id for user_id in self.game.players if condition(user_id)
        ]
        self.callback_action = callback_action
        self.user_select = None
        self.game.events.game_end += self.stop

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.callback_action(self.eligible_players[0])

    async def create_user_selection(self):
        options = [
            discord.SelectOption(
                value=str(user_id),
                label=f"{user.display_name} ({len(self.game.hands[user_id])} cards)",
            )
            for user_id in self.eligible_players
            if (user := await self.game.app.get_or_fetch_user(user_id))  # type: ignore
        ]
        self.user_select = discord.ui.Select(
            placeholder="Select a player",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user_select.callback = self.selection_callback
        self.action_row = discord.ui.ActionRow(self.user_select)
        self.add_item(self.action_row)

    async def selection_callback(self, interaction: discord.Interaction):
        if not (interaction and self.user_select):
            return
        self.stop()
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        if not isinstance(self.user_select.values[0], str):
            raise TypeError("user_select.values[0] is not a str")
        await self.callback_action(int(self.user_select.values[0]))


class DefuseView(SelectionView):
    def __init__(
        self,
        game: "Game",
        callback_action: Callable[[], Coroutine],
        card="eggsplode",
        prev_card=None,
    ):
        super().__init__(timeout=20)
        self.game = game
        self.callback_action = callback_action
        self.card = card
        self.prev_card = prev_card if prev_card else card
        self.card_position = 0
        self.move_prompt_display = discord.ui.TextDisplay(self.move_prompt)
        self.add_item(self.move_prompt_display)
        self.top_button = discord.ui.Button(
            label="Top", style=discord.ButtonStyle.blurple, emoji="⏫"
        )
        self.top_button.callback = self.top
        self.add_item(self.top_button)
        self.move_up_button = discord.ui.Button(
            label="Move up", style=discord.ButtonStyle.blurple, emoji="⬆️"
        )
        self.move_up_button.callback = self.move_up
        self.add_item(self.move_up_button)
        self.move_down_button = discord.ui.Button(
            label="Move down", style=discord.ButtonStyle.blurple, emoji="⬇️"
        )
        self.move_down_button.callback = self.move_down
        self.add_item(self.move_down_button)
        self.bottom_button = discord.ui.Button(
            label="Bottom", style=discord.ButtonStyle.blurple, emoji="⏬"
        )
        self.bottom_button.callback = self.bottom
        self.add_item(self.bottom_button)
        self.add_item(self.confirm_button)
        self.game.events.game_end += self.stop

    async def finish(self, interaction=None):
        self.game.deck.insert(self.card_position, self.card)
        await self.callback_action()

    async def top(self, interaction: discord.Interaction):
        self.card_position = len(self.game.deck)
        await self.update_view(interaction)

    async def move_up(self, interaction: discord.Interaction):
        if self.card_position < len(self.game.deck):
            self.card_position += 1
        else:
            self.card_position = 0
        await self.update_view(interaction)

    async def move_down(self, interaction: discord.Interaction):
        if self.card_position > 0:
            self.card_position -= 1
        else:
            self.card_position = len(self.game.deck)
        await self.update_view(interaction)

    async def bottom(self, interaction: discord.Interaction):
        self.card_position = 0
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        self.move_prompt_display.content = self.move_prompt
        await interaction.edit(view=self)

    @property
    def move_prompt(self) -> str:
        return format_message(
            "move_prompt",
            tooltip(self.prev_card),
            self.card_position,
            len(self.game.deck),
            "\n".join(
                format_message("players_list_item", player)
                for player in self.game.players
            ),
        )
