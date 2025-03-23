"""
Contains the views for the short interactions in the game, such as "Nope" and "Defuse".
"""

from collections.abc import Callable, Coroutine
import discord
from ..strings import CARDS, MESSAGES
from ..ctx import ActionContext
from .base import BaseView


class NopeView(BaseView):
    def __init__(
        self,
        ctx: ActionContext,
        nope_callback_action: Callable[[], None] | None = None,
    ):
        super().__init__(ctx, timeout=10)
        self.nope_callback_action = nope_callback_action
        self.nope_count = 0
        self.ctx.game.active_nope_views.append(self)

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    async def finish(self):
        self.on_timeout = super().on_timeout
        self.ctx.game.active_nope_views.remove(self)
        try:
            await super().on_timeout()
        finally:
            if self.nope_callback_action and self.nope_count % 2:
                self.nope_callback_action()

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
            await interaction.respond(MESSAGES["no_self_nope"], ephemeral=True)
            return
        if interaction.user.id not in self.ctx.game.players:
            await interaction.respond(MESSAGES["user_not_in_game"], ephemeral=True)
            return
        try:
            self.ctx.game.hands[interaction.user.id].remove("nope")
        except ValueError:
            await interaction.respond(MESSAGES["no_nope_cards"], ephemeral=True)
            return
        if not interaction.message:
            return
        self.nope_count += 1
        button.label = "Nope!" if not self.nope_count % 2 else "Yup!"
        new_message_content = "".join(
            (line.strip("~~") + "\n" if line.startswith("~~") else "~~" + line + "~~\n")
            for line in interaction.message.content.split("\n")
        ) + (
            MESSAGES["message_edit_on_nope"].format(interaction.user.id)
            if self.nope_count % 2
            else MESSAGES["message_edit_on_yup"].format(interaction.user.id)
        )
        await interaction.edit(content=new_message_content, view=self)


class BlockingNopeView(NopeView):
    def __init__(
        self,
        ctx: ActionContext,
        target_player_id: int,
        ok_callback_action: Callable[[discord.Interaction | None], Coroutine],
        nope_callback_action: Callable[[], None] | None = None,
    ):
        super().__init__(ctx, nope_callback_action=nope_callback_action)
        self.ctx.game.awaiting_prompt = True
        self.target_player_id = target_player_id
        self.ok_callback_action = ok_callback_action

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            if self.ctx.action_id == self.ctx.game.action_id:
                self.ctx.game.awaiting_prompt = False
                if not self.nope_count % 2:
                    await self.ok_callback_action(None)

    @discord.ui.button(label="OK!", style=discord.ButtonStyle.green, emoji="✅")
    async def ok_callback(self, _: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user:
            return
        if interaction.user.id != self.target_player_id:
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return
        if self.nope_count % 2:
            await interaction.respond(MESSAGES["action_noped"], ephemeral=True)
            return
        await super().on_timeout()
        self.ctx.game.awaiting_prompt = False
        await self.ok_callback_action(interaction)


class DefuseView(BaseView):
    def __init__(
        self,
        ctx: ActionContext,
        callback_action: Callable[[], Coroutine],
        card="eggsplode",
        prev_card=None,
    ):
        super().__init__(ctx, timeout=10)
        self.ctx.game.awaiting_prompt = True
        self.callback_action = callback_action
        self.card = card
        self.prev_card = prev_card if prev_card else card
        self.card_position = 0
        self.generate_move_prompt()

    async def finish(self):
        self.ctx.game.deck.insert(self.card_position, self.card)
        self.ctx.game.awaiting_prompt = False
        await self.callback_action()

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, _: discord.ui.Button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.edit(view=self)
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
        return MESSAGES["move_prompt"].format(
            CARDS[self.prev_card]["title"],
            self.card_position,
            len(self.ctx.game.deck),
            "\n".join(
                MESSAGES["players_list_item"].format(player)
                for player in self.ctx.game.players
            ),
        )


class ChoosePlayerView(BaseView):
    def __init__(
        self,
        ctx: ActionContext,
        callback_action: Callable[[int], Coroutine],
        condition: Callable[[int], bool] = lambda _: True,
    ):
        super().__init__(ctx, timeout=10)
        self.ctx.game.awaiting_prompt = True
        self.eligible_players = [
            user_id for user_id in self.ctx.game.players if condition(user_id)
        ]
        self.callback_action = callback_action
        self.user_select = None

    async def __aenter__(self):
        await self.create_user_selection()
        return self

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
        await interaction.edit(view=self)
        if not isinstance(self.user_select.values[0], str):
            raise TypeError("user_select.values[0] is not a str")
        await self.callback_action(int(self.user_select.values[0]))


class AlterFutureView(BaseView):
    def __init__(
        self,
        ctx: ActionContext,
        callback_action: Callable[[], Coroutine],
        amount_of_cards: int,
    ):
        super().__init__(ctx, timeout=10)
        self.ctx.game.awaiting_prompt = True
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
                emoji=CARDS[card]["emoji"],
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
        self.ctx.game.awaiting_prompt = False
        await self.callback_action()

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, _: discord.ui.Button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.edit(view=self)
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
