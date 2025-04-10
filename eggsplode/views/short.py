"""
Contains the views for the short interactions in the game, such as "Defuse".
"""

from collections.abc import Callable, Coroutine
import discord

from ..strings import CARDS, get_message, replace_emojis
from ..ctx import ActionContext


class DefuseView(discord.ui.View):
    def __init__(
        self,
        ctx: ActionContext,
        callback_action: Callable[[], Coroutine],
        card="eggsplode",
        prev_card=None,
    ):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.callback_action = callback_action
        self.card = card
        self.prev_card = prev_card if prev_card else card
        self.card_position = 0
        self.generate_move_prompt()

    async def finish(self):
        self.ctx.game.deck.insert(self.card_position, self.card)
        await self.callback_action()

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, _: discord.ui.Button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        self.on_timeout = super().on_timeout
        await self.finish()

    @discord.ui.button(label="Top", style=discord.ButtonStyle.blurple, emoji="⏫")
    async def top(self, _: discord.ui.Button, interaction: discord.Interaction):
        self.card_position = len(self.ctx.game.deck)
        await self.update_view(interaction)

    @discord.ui.button(label="Move up", style=discord.ButtonStyle.blurple, emoji="⬆️")
    async def move_up(self, _: discord.ui.Button, interaction: discord.Interaction):
        if self.card_position < len(self.ctx.game.deck):
            self.card_position += 1
        else:
            self.card_position = 0
        await self.update_view(interaction)

    @discord.ui.button(label="Move down", style=discord.ButtonStyle.blurple, emoji="⬇️")
    async def move_down(self, _: discord.ui.Button, interaction: discord.Interaction):
        if self.card_position > 0:
            self.card_position -= 1
        else:
            self.card_position = len(self.ctx.game.deck)
        await self.update_view(interaction)

    @discord.ui.button(label="Bottom", style=discord.ButtonStyle.blurple, emoji="⏬")
    async def bottom(self, _: discord.ui.Button, interaction: discord.Interaction):
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
            len(self.ctx.game.deck),
            "\n".join(
                get_message("players_list_item").format(player)
                for player in self.ctx.game.players
            ),
        )


class ChoosePlayerView(discord.ui.View):
    def __init__(
        self,
        ctx: ActionContext,
        callback_action: Callable[[int], Coroutine],
        condition: Callable[[int], bool] = lambda _: True,
    ):
        super().__init__(timeout=20)
        self.ctx = ctx
        self.eligible_players = [
            user_id for user_id in self.ctx.game.players if condition(user_id)
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
                label=f"{user.display_name} ({len(self.ctx.game.hands[user_id])} cards)",
            )
            for user_id in self.eligible_players
            if (user := await self.ctx.app.get_or_fetch_user(user_id))
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


class AlterFutureView(discord.ui.View):
    def __init__(
        self,
        ctx: ActionContext,
        callback_action: Callable[[], Coroutine],
        amount_of_cards: int,
    ):
        super().__init__(timeout=20)
        self.ctx = ctx
        self.amount_of_cards = min(amount_of_cards, len(self.ctx.game.deck))
        self.callback_action = callback_action
        self.selects: list[discord.ui.Select] = []
        self.create_selections()

    def create_selections(self):
        card_options = [
            discord.SelectOption(
                value=f"{i}:{card}",
                label=CARDS[card]["title"],
                description=CARDS[card]["description"],
                emoji=replace_emojis(CARDS[card]["emoji"]),
            )
            for i, card in enumerate(
                self.ctx.game.deck[-1 : -self.amount_of_cards - 1 : -1]
            )
        ]
        for select in self.selects:
            self.remove_item(select)
        self.selects = []
        for i in range(self.amount_of_cards):
            select = discord.ui.Select(
                placeholder=f"{i + 1}. card: {CARDS[self.ctx.game.deck[-i - 1]]['title']}",
                min_values=1,
                max_values=1,
                options=card_options,
            )
            select.callback = self.selection_callback
            self.selects.append(select)
            self.add_item(select)

    async def finish(self):
        await self.callback_action()

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, _: discord.ui.Button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        self.on_timeout = super().on_timeout
        await self.finish()

    async def selection_callback(self, interaction: discord.Interaction):
        if not interaction:
            return
        for i, select in enumerate(self.selects):
            if select.values is None:
                continue
            if not isinstance(select.values[0], str):
                raise TypeError("select.values[0] is not a str")
            prev_card_position = -i - 1
            new_card_position = -int(select.values[0].partition(":")[0]) - 1
            prev_card = self.ctx.game.deck[prev_card_position]
            new_card = select.values[0].partition(":")[2]
            self.ctx.game.deck[prev_card_position] = new_card
            self.ctx.game.deck[new_card_position] = prev_card
            break
        self.create_selections()
        await interaction.edit(view=self)
