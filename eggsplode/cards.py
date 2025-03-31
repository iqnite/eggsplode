"""
Contains card effects for the base game.
"""

import random
import discord

from .ctx import ActionContext, PlayActionContext
from .views.short import (
    ExplicitNopeView,
    ChoosePlayerView,
    AlterFutureView,
    DefuseView,
)
from .strings import CARDS, get_message, replace_emojis


async def draw_card(ctx: PlayActionContext, interaction: discord.Interaction, index=-1):
    if not interaction.user:
        return
    await ctx.disable_view(interaction)
    card: str = ctx.game.draw_card(index)
    match card:
        case "defused":
            async with DefuseView(
                ctx.copy(),
                lambda: defuse_finish(ctx, interaction),
                card="eggsplode",
            ) as view:
                await interaction.respond(
                    view.generate_move_prompt(),
                    view=view,
                    ephemeral=True,
                )
            return
        case "eggsplode":
            await interaction.respond(
                get_message("eggsploded").format(interaction.user.id)
            )
        case "gameover":
            await interaction.respond(
                get_message("eggsploded").format(interaction.user.id)
                + "\n"
                + get_message("game_over").format(ctx.game.players[0])
            )
            ctx.on_game_over()
            del ctx.games[ctx.game_id]
            return
        case "radioeggtive":
            async with DefuseView(
                ctx.copy(),
                lambda: radioeggtive_finish(ctx, interaction),
                card="radioeggtive_face_up",
                prev_card="radioeggtive",
            ) as view:
                await interaction.respond(
                    view.generate_move_prompt(),
                    view=view,
                    ephemeral=True,
                )
            return
        case "radioeggtive_face_up":
            await interaction.respond(
                get_message("radioeggtive_face_up").format(interaction.user.id)
            )
        case _:
            await interaction.respond(
                get_message("user_drew_card").format(interaction.user.id)
            )
            await interaction.respond(
                get_message("you_drew_card").format(
                    replace_emojis(CARDS[card]["emoji"]), CARDS[card]["title"]
                ),
                ephemeral=True,
            )
    await ctx.end_turn(interaction)


async def attegg(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    async with ExplicitNopeView(
        ctx=ctx.copy(),
        target_player_id=ctx.game.next_player_id,
        ok_callback_action=lambda _: attegg_finish(ctx, interaction),
    ) as view:
        await interaction.respond(
            get_message("before_attegg").format(
                interaction.user.id,
                ctx.game.next_player_id,
                ctx.game.draw_in_turn + 2,
            ),
            view=view,
        )


async def skip(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    target_player_id = (
        ctx.game.next_player_id if ctx.game.draw_in_turn == 0 else interaction.user.id
    )
    async with ExplicitNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: skip_finish(ctx, interaction),
    ) as view:
        await interaction.respond(
            get_message("before_skip").format(interaction.user.id, target_player_id),
            view=view,
        )


async def shuffle(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    random.shuffle(ctx.game.deck)
    await interaction.respond(
        get_message("shuffled").format(interaction.user.id)
        + " "
        + radioeggtive_warning(ctx)
    )


async def predict(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    next_cards = "\n".join(
        get_message("bold_list_item").format(
            replace_emojis(CARDS[card]["emoji"]), CARDS[card]["title"]
        )
        for card in ctx.game.deck[-1:-4:-1]
    )
    await interaction.respond(
        get_message("predicted").format(interaction.user.id),
    )
    await interaction.respond(
        "\n".join((get_message("next_cards"), next_cards)),
        ephemeral=True,
    )


async def food_combo(
    ctx: PlayActionContext, interaction: discord.Interaction, selected: str
):
    if not interaction.user:
        return
    if not ctx.game.any_player_has_cards():
        await interaction.respond(get_message("no_players_have_cards"))
        return
    assert ctx.game.current_player_hand.count(selected) >= 2
    for _ in range(2):
        ctx.game.current_player_hand.remove(selected)
    async with ChoosePlayerView(
        ctx.copy(),
        lambda target_player_id: food_combo_begin(
            ctx, interaction, target_player_id, selected
        ),
        condition=lambda user_id: user_id != ctx.game.current_player_id
        and len(ctx.game.hands[user_id]) > 0,
    ) as view:
        await interaction.respond(
            get_message("steal_prompt"), view=view, ephemeral=True
        )


async def food_combo_begin(
    ctx: PlayActionContext,
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
        await interaction.respond(
            get_message("before_steal").format(
                replace_emojis(CARDS[food_card]["emoji"]),
                interaction.user.id,
                target_player_id,
            ),
            view=view,
        )


async def food_combo_finish(
    ctx: PlayActionContext,
    interaction: discord.Interaction,
    target_interaction: discord.Interaction | None,
    target_player_id: int,
):
    if not interaction.user:
        return
    target_hand = ctx.game.hands[target_player_id]
    if not target_hand:
        await interaction.respond(
            get_message("no_cards_to_steal").format(
                ctx.game.current_player_id, target_player_id
            )
        )
        return
    stolen_card = random.choice(target_hand)
    ctx.game.hands[target_player_id].remove(stolen_card)
    ctx.game.current_player_hand.append(stolen_card)
    await ctx.update_view(interaction)
    await interaction.respond(
        get_message("stolen_card_public").format(
            ctx.game.current_player_id, target_player_id
        )
    )
    await interaction.respond(
        get_message("stolen_card_you").format(
            replace_emojis(CARDS[stolen_card]["emoji"]), CARDS[stolen_card]["title"]
        ),
        ephemeral=True,
    )
    if target_interaction:
        await target_interaction.respond(
            get_message("stolen_card_them").format(
                ctx.game.current_player_id,
                replace_emojis(CARDS[stolen_card]["emoji"]),
                CARDS[stolen_card]["title"],
            ),
            ephemeral=True,
        )


async def defuse_finish(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.user:
        raise TypeError("interaction.user is None")
    await interaction.respond(get_message("defused").format(interaction.user.id))
    await ctx.end_turn(interaction)


async def radioeggtive_finish(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.user:
        raise TypeError("interaction.user is None")
    await interaction.respond(get_message("radioeggtive").format(interaction.user.id))
    await ctx.end_turn(interaction)


async def attegg_finish(
    ctx: PlayActionContext, interaction: discord.Interaction, target_player_id=None
):
    target_player_id = target_player_id or ctx.game.next_player_id
    if not interaction.message:
        return
    await ctx.disable_view(interaction)
    prev_to_draw_in_turn = ctx.game.draw_in_turn
    ctx.game.draw_in_turn = 0
    while ctx.game.current_player_id != target_player_id:
        ctx.game.next_turn()
    ctx.game.draw_in_turn = prev_to_draw_in_turn + 2
    await ctx.end_turn(interaction)


async def skip_finish(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.message:
        return
    await ctx.disable_view(interaction)
    ctx.game.next_turn()
    await ctx.end_turn(interaction)


async def draw_from_bottom(ctx: PlayActionContext, interaction: discord.Interaction):
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
        await interaction.respond(
            get_message("before_draw_from_bottom").format(
                interaction.user.id, target_player_id
            ),
            view=view,
        )


async def targeted_attegg(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    async with ChoosePlayerView(
        ctx.copy(),
        lambda target_player_id: targeted_attegg_begin(
            ctx, interaction, target_player_id
        ),
    ) as view:
        await interaction.respond(
            get_message("targeted_attegg_prompt"), view=view, ephemeral=True
        )


async def targeted_attegg_begin(
    ctx: PlayActionContext, interaction: discord.Interaction, target_player_id: int
):
    if not interaction.user:
        return
    async with ExplicitNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: attegg_finish(ctx, interaction, target_player_id),
    ) as view:
        await interaction.respond(
            get_message("before_targeted_attegg").format(
                interaction.user.id,
                target_player_id,
                ctx.game.draw_in_turn + 2,
            ),
            view=view,
        )


async def alter_future(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    async with AlterFutureView(
        ctx.copy(), lambda: alter_future_finish(ctx, interaction), 3
    ) as view:
        await interaction.respond(view=view, ephemeral=True)


async def alter_future_finish(ctx: PlayActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    await interaction.respond(
        get_message("altered_future").format(interaction.user.id)
        + " "
        + radioeggtive_warning(ctx),
    )


async def reverse(ctx: PlayActionContext, interaction: discord.Interaction):
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
        ok_callback_action=lambda _: skip_finish(ctx, interaction),
    ) as view:
        await interaction.respond(
            get_message("before_reverse").format(interaction.user.id, target_player_id),
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
