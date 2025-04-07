"""
Contains card effects for the base game.
"""

import random
import discord
from .ctx import ActionContext, EventController
from .views.nope import ExplicitNopeView
from .views.game_ended import GameEndedView
from .views.short import ChoosePlayerView, AlterFutureView, DefuseView
from .strings import CARDS, get_message, replace_emojis


async def draw_card(ctx: ActionContext, interaction: discord.Interaction, index=-1):
    if not interaction.user:
        return
    card: str = ctx.game.draw_card(index)
    match card:
        case "defused":
            view = DefuseView(
                ctx.copy(),
                lambda: defuse_finish(ctx),
                card="eggsplode",
            )
            await interaction.respond(
                view.generate_move_prompt(),
                view=view,
                ephemeral=True,
                delete_after=60,
            )
            return
        case "eggsplode":
            await ctx.log(get_message("eggsploded").format(interaction.user.id))
        case "gameover":
            await ctx.log(
                get_message("eggsploded").format(interaction.user.id)
                + "\n"
                + get_message("game_over").format(ctx.game.players[0]),
                view=GameEndedView(ctx.copy()),
            )
            await ctx.events.notify(EventController.GAME_END)
            del ctx.games[ctx.game_id]
            return
        case "radioeggtive":
            view = DefuseView(
                ctx.copy(),
                lambda: radioeggtive_finish(ctx),
                card="radioeggtive_face_up",
                prev_card="radioeggtive",
            )
            await interaction.respond(
                view.generate_move_prompt(),
                view=view,
                ephemeral=True,
                delete_after=60,
            )
            return
        case "radioeggtive_face_up":
            await ctx.log(
                get_message("radioeggtive_face_up").format(interaction.user.id)
            )
        case _:
            await ctx.log(get_message("user_drew_card").format(interaction.user.id))
            await interaction.respond(
                get_message("you_drew_card").format(
                    replace_emojis(CARDS[card]["emoji"]), CARDS[card]["title"]
                ),
                ephemeral=True,
                delete_after=10,
            )
    ctx.game.next_turn()
    await ctx.events.notify(EventController.ACTION_END)
    await ctx.events.notify(EventController.TURN_END)


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
    await ctx.events.notify(EventController.ACTION_END)


async def defuse_finish(ctx: ActionContext):
    await ctx.log(get_message("defused").format(ctx.game.current_player_id))
    ctx.game.next_turn()
    await ctx.events.notify(EventController.TURN_END)


async def radioeggtive_finish(ctx: ActionContext):
    await ctx.log(get_message("radioeggtive").format(ctx.game.current_player_id))
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


async def alter_future(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    view = AlterFutureView(ctx.copy(), lambda: alter_future_finish(ctx, interaction), 3)
    await interaction.respond(view=view, ephemeral=True)


async def alter_future_finish(ctx: ActionContext, interaction: discord.Interaction):
    if not interaction.user:
        return
    await ctx.log(get_message("altered_future").format(interaction.user.id))
    await ctx.events.notify(EventController.ACTION_END)


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


CARD_ACTIONS = {
    "attegg": attegg,
    "skip": skip,
    "shuffle": shuffle,
    "predict": predict,
    "draw_from_bottom": draw_from_bottom,
    "targeted_attegg": targeted_attegg,
    "alter_future": alter_future,
    "reverse": reverse,
}
