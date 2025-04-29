"""
Contains card effects for the base game.
"""

import random
import discord

from ..ctx import ActionContext, EventController
from ..views.nope import ExplicitNopeView
from ..views.selections import ChoosePlayerView
from ..strings import CARDS, get_message, replace_emojis


async def attegg(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    async with ExplicitNopeView(
        ctx=ctx.copy(),
        target_player_id=ctx.game.next_player_id,
        ok_callback_action=lambda _: attegg_finish(ctx),
    ) as view:
        await ctx.log(
            get_message("before_attegg").format(
                interaction.user.id,
                ctx.game.next_player_id,
                ctx.game.draw_in_turn + 2,
            ),
            view=view,
        )


async def skip(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    target_player_id = (
        ctx.game.next_player_id if ctx.game.draw_in_turn == 0 else interaction.user.id
    )
    async with ExplicitNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: skip_finish(ctx),
    ) as view:
        await ctx.log(
            get_message("before_skip").format(interaction.user.id, target_player_id),
            view=view,
        )


async def shuffle(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    random.shuffle(ctx.game.deck)
    await ctx.log(get_message("shuffled").format(interaction.user.id))
    await ctx.events.notify(EventController.ACTION_END)


async def predict(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    next_cards = "\n".join(
        get_message("bold_list_item").format(
            replace_emojis(CARDS[card]["emoji"]), CARDS[card]["title"]
        )
        for card in ctx.game.deck[-1:-4:-1]
    )
    await ctx.log(
        get_message("predicted").format(interaction.user.id),
    )
    await interaction.respond(
        "\n".join((get_message("next_cards"), next_cards)),
        ephemeral=True,
        delete_after=20,
    )
    await ctx.events.notify(EventController.ACTION_END)


async def food_combo(
    ctx: ActionContext, interaction: discord.Interaction, selected: str
):
    if not interaction.user:
        return
    if not ctx.game.any_player_has_cards():
        await interaction.respond(
            get_message("no_players_have_cards"), ephemeral=True, delete_after=10
        )
        return
    assert ctx.game.current_player_hand.count(selected) >= 2
    for _ in range(2):
        ctx.game.current_player_hand.remove(selected)
    view = ChoosePlayerView(
        ctx.copy(),
        lambda target_player_id: food_combo_begin(
            ctx, interaction, target_player_id, selected
        ),
        condition=lambda user_id: user_id != ctx.game.current_player_id
        and len(ctx.game.hands[user_id]) > 0,
    )
    await view.create_user_selection()
    await interaction.respond(
        get_message("steal_prompt"), view=view, ephemeral=True, delete_after=30
    )


async def food_combo_begin(
    ctx: ActionContext,
    interaction: discord.Interaction,
    target_player_id: int,
    food_card: str,
):
    if not interaction.user:
        return
    async with ExplicitNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda target_interaction: food_combo_finish(
            ctx, interaction, target_interaction, target_player_id
        ),
    ) as view:
        await ctx.log(
            get_message("before_steal").format(
                replace_emojis(CARDS[food_card]["emoji"]),
                interaction.user.id,
                target_player_id,
            ),
            view=view,
        )


async def food_combo_finish(
    ctx: ActionContext,
    interaction: discord.Interaction,
    target_interaction: discord.Interaction | None,
    target_player_id: int,
):
    if not interaction.user:
        return
    target_hand = ctx.game.hands[target_player_id]
    if not target_hand:
        await ctx.log(
            get_message("no_cards_to_steal").format(
                ctx.game.current_player_id, target_player_id
            )
        )
        await ctx.events.notify(EventController.ACTION_END)
        return
    stolen_card = random.choice(target_hand)
    ctx.game.hands[target_player_id].remove(stolen_card)
    ctx.game.current_player_hand.append(stolen_card)
    await ctx.log(
        get_message("stolen_card_public").format(
            ctx.game.current_player_id, target_player_id
        )
    )
    try:
        await interaction.respond(
            get_message("stolen_card_you").format(
                replace_emojis(CARDS[stolen_card]["emoji"]), CARDS[stolen_card]["title"]
            ),
            ephemeral=True,
            delete_after=10,
        )
        if target_interaction:
            await target_interaction.respond(
                get_message("stolen_card_them").format(
                    ctx.game.current_player_id,
                    replace_emojis(CARDS[stolen_card]["emoji"]),
                    CARDS[stolen_card]["title"],
                ),
                ephemeral=True,
                delete_after=10,
            )
    finally:
        await ctx.events.notify(EventController.ACTION_END)


async def defuse_finish(ctx: ActionContext):
    await ctx.log(get_message("_defused_").format(ctx.game.current_player_id))
    ctx.game.next_turn()
    await ctx.events.notify(EventController.TURN_END)


async def attegg_finish(ctx: ActionContext, target_player_id=None):
    target_player_id = target_player_id or ctx.game.next_player_id
    prev_to_draw_in_turn = ctx.game.draw_in_turn
    ctx.game.draw_in_turn = 0
    while ctx.game.current_player_id != target_player_id:
        ctx.game.next_turn()
    ctx.game.draw_in_turn = prev_to_draw_in_turn + 2
    await ctx.events.notify(EventController.TURN_END)


async def skip_finish(ctx: ActionContext):
    ctx.game.next_turn()
    await ctx.events.notify(EventController.TURN_END)


CARD_ACTIONS = {
    "attegg": attegg,
    "skip": skip,
    "shuffle": shuffle,
    "predict": predict,
}
