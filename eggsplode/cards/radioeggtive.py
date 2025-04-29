"""
Contains card effects for the Radioeggtive expansion.
"""

from collections.abc import Callable, Coroutine
import discord

from ..action import draw_card
from ..cards.base import attegg_finish, skip_finish
from ..ctx import ActionContext
from ..strings import CARDS, get_message, replace_emojis
from ..views.nope import ExplicitNopeView
from ..views.selections import ChoosePlayerView


async def draw_from_bottom(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    target_player_id = (
        ctx.game.next_player_id if ctx.game.draw_in_turn == 0 else interaction.user.id
    )
    async with ExplicitNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: draw_card(ctx, interaction, index=0),
    ) as view:
        await ctx.log(
            get_message("before_draw_from_bottom").format(
                interaction.user.id, target_player_id
            ),
            view=view,
        )


def radioeggtive_warning(ctx: ActionContext) -> str:
    radioeggtive_countdown = ctx.game.card_comes_in("radioeggtive_face_up")
    return (
        ""
        if radioeggtive_countdown is None
        else (
            get_message("play_prompt_radioeggtive").format(radioeggtive_countdown)
            if radioeggtive_countdown > 0
            else get_message("play_prompt_radioeggtive_now")
        )
    )


async def reverse(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    ctx.game.reverse()
    target_player_id = (
        ctx.game.next_player_id if ctx.game.draw_in_turn == 0 else interaction.user.id
    )
    async with ExplicitNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        nope_callback_action=ctx.game.reverse,
        ok_callback_action=lambda _: skip_finish(ctx),
    ) as view:
        await ctx.log(
            get_message("before_reverse").format(interaction.user.id, target_player_id),
            view=view,
        )


async def alter_future_finish(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    await ctx.log(get_message("altered_future").format(interaction.user.id))
    await ctx.events.action_end()


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
    async def confirm(self, _, interaction: discord.Interaction):
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


async def alter_future(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    view = AlterFutureView(ctx.copy(), lambda: alter_future_finish(ctx, interaction), 3)
    await interaction.respond(view=view, ephemeral=True)


async def targeted_attegg_begin(
    ctx: ActionContext, interaction: discord.Interaction, target_player_id: int
):
    if not interaction.user:
        return
    async with ExplicitNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: attegg_finish(ctx, target_player_id),
    ) as view:
        await ctx.log(
            get_message("before_targeted_attegg").format(
                interaction.user.id,
                target_player_id,
                ctx.game.draw_in_turn + 2,
            ),
            view=view,
        )


async def targeted_attegg(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    view = ChoosePlayerView(
        ctx.copy(),
        lambda target_player_id: targeted_attegg_begin(
            ctx, interaction, target_player_id
        ),
    )
    await view.create_user_selection()
    await interaction.respond(
        get_message("targeted_attegg_prompt"),
        view=view,
        ephemeral=True,
        delete_after=30,
    )


async def radioeggtive_finish(ctx: ActionContext):
    await ctx.log(get_message("radioeggtive").format(ctx.game.current_player_id))
    ctx.game.next_turn()
    await ctx.events.turn_end()


CARD_ACTIONS = {
    "draw_from_bottom": draw_from_bottom,
    "targeted_attegg": targeted_attegg,
    "alter_future": alter_future,
    "reverse": reverse,
}
