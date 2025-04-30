"""
Contains the views for the short interactions in the game, such as "Defuse".
"""

from typing import Callable, Coroutine
import discord

from .strings import CARDS, get_message
from .game_logic import Game


class SelectionView(discord.ui.View):
    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    async def finish(self):
        pass

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, _, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        self.on_timeout = super().on_timeout
        await self.finish()


class ChoosePlayerView(discord.ui.View):
    def __init__(
        self,
        game: Game,
        callback_action: Callable[[int], Coroutine],
        condition: Callable[[int], bool] = lambda _: True,
    ):
        super().__init__(timeout=20)
        self.game = game
        self.eligible_players = [
            user_id for user_id in self.game.players if condition(user_id)
        ]
        self.callback_action = callback_action
        self.user_select = None

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
            if (user := await self.game.app.get_or_fetch_user(user_id))
        ]
        self.user_select = discord.ui.Select(
            placeholder="Select another player",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user_select.callback = self.selection_callback
        self.add_item(self.user_select)

    async def selection_callback(self, interaction: discord.Interaction):
        if not (interaction and self.user_select):
            return
        self.on_timeout = super().on_timeout
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        if not isinstance(self.user_select.values[0], str):
            raise TypeError("user_select.values[0] is not a str")
        await self.callback_action(int(self.user_select.values[0]))


class DefuseView(SelectionView):
    def __init__(
        self,
        game: Game,
        callback_action: Callable[[], Coroutine],
        card="eggsplode",
        prev_card=None,
    ):
        super().__init__(timeout=30)
        self.game = game
        self.callback_action = callback_action
        self.card = card
        self.prev_card = prev_card if prev_card else card
        self.card_position = 0
        self.generate_move_prompt()

    async def finish(self):
        self.game.deck.insert(self.card_position, self.card)
        await self.callback_action()

    @discord.ui.button(label="Top", style=discord.ButtonStyle.blurple, emoji="⏫")
    async def top(self, _, interaction: discord.Interaction):
        self.card_position = len(self.game.deck)
        await self.update_view(interaction)

    @discord.ui.button(label="Move up", style=discord.ButtonStyle.blurple, emoji="⬆️")
    async def move_up(self, _, interaction: discord.Interaction):
        if self.card_position < len(self.game.deck):
            self.card_position += 1
        else:
            self.card_position = 0
        await self.update_view(interaction)

    @discord.ui.button(label="Move down", style=discord.ButtonStyle.blurple, emoji="⬇️")
    async def move_down(self, _, interaction: discord.Interaction):
        if self.card_position > 0:
            self.card_position -= 1
        else:
            self.card_position = len(self.game.deck)
        await self.update_view(interaction)

    @discord.ui.button(label="Bottom", style=discord.ButtonStyle.blurple, emoji="⏬")
    async def bottom(self, _, interaction: discord.Interaction):
        self.card_position = 0
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        await interaction.edit(
            content=self.generate_move_prompt(),
            view=self,
        )

    def generate_move_prompt(self):
        return get_message("move_prompt").format(
            CARDS[self.prev_card]["title"],
            self.card_position,
            len(self.game.deck),
            "\n".join(
                get_message("players_list_item").format(player)
                for player in self.game.players
            ),
        )
