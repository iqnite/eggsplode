"""
Contains card effects for the base game.
"""

import random
import discord

from .ctx import PlayActionContext
from .views.short import (
    BlockingNopeView,
    NopeView,
    ChoosePlayerView,
    AlterFutureView,
    DefuseView,
)
from .strings import CARDS, MESSAGES


async def draw_card(ctx: PlayActionContext, interaction: discord.Interaction, index=-1):
    """
    Draw a card from the deck.

    Args:
        interaction (discord.Interaction): The interaction that triggered the draw.
        index (int): The index of the card to draw.
    """
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
                MESSAGES["eggsploded"].format(interaction.user.id)
            )
        case "gameover":
            await interaction.respond(
                MESSAGES["eggsploded"].format(interaction.user.id)
                + "\n"
                + MESSAGES["game_over"].format(ctx.game.players[0])
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
                MESSAGES["radioeggtive_face_up"].format(interaction.user.id)
            )
        case _:
            await interaction.respond(
                MESSAGES["user_drew_card"].format(interaction.user.id)
            )
            await interaction.respond(
                MESSAGES["you_drew_card"].format(
                    CARDS[card]["emoji"], CARDS[card]["title"]
                ),
                ephemeral=True,
            )
    await ctx.end_turn(interaction)


async def attegg(ctx: PlayActionContext, interaction: discord.Interaction):
    """
    Handle the 'attegg' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        return
    async with BlockingNopeView(
        ctx=ctx.copy(),
        target_player_id=ctx.game.next_player_id,
        ok_callback_action=lambda _: attegg_finish(ctx, interaction),
    ) as view:
        await interaction.respond(
            MESSAGES["before_attegg"].format(
                interaction.user.id,
                ctx.game.next_player_id,
                ctx.game.draw_in_turn + 2,
            ),
            view=view,
        )


async def skip(ctx: PlayActionContext, interaction: discord.Interaction):
    """
    Handle the 'skip' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        return
    target_player_id = (
        ctx.game.next_player_id if ctx.game.draw_in_turn == 0 else interaction.user.id
    )
    async with BlockingNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: skip_finish(ctx, interaction),
    ) as view:
        await interaction.respond(
            MESSAGES["before_skip"].format(interaction.user.id, target_player_id),
            view=view,
        )


async def shuffle(ctx: PlayActionContext, interaction: discord.Interaction):
    """
    Handle the 'shuffle' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    prev_deck = ctx.game.deck.copy()
    random.shuffle(ctx.game.deck)
    if not interaction.user:
        return
    async with NopeView(
        ctx=ctx.copy(),
        nope_callback_action=lambda: undo_shuffle(ctx, prev_deck),
    ) as view:
        await interaction.respond(
            MESSAGES["shuffled"].format(interaction.user.id),
            view=view,
        )


def undo_shuffle(ctx, prev_deck):
    """
    Undoes the 'shuffle' action.
    """
    ctx.game.deck = prev_deck


async def predict(ctx: PlayActionContext, interaction: discord.Interaction):
    """
    Handle the 'predict' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        return
    next_cards = "\n".join(
        MESSAGES["bold_list_item"].format(CARDS[card]["emoji"], CARDS[card]["title"])
        for card in ctx.game.deck[-1:-4:-1]
    )
    await interaction.respond(
        MESSAGES["predicted"].format(interaction.user.id),
    )
    await interaction.respond(
        "\n".join((MESSAGES["next_cards"], next_cards)),
        ephemeral=True,
    )


async def food_combo(
    ctx: PlayActionContext, interaction: discord.Interaction, selected: str
):
    """
    Handle the 'food combo' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
        selected (str): The selected card.
    """
    if not interaction.user:
        return
    if not ctx.game.any_player_has_cards():
        await interaction.respond(MESSAGES["no_players_have_cards"])
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
        await interaction.respond(MESSAGES["steal_prompt"], view=view, ephemeral=True)


async def food_combo_begin(
    ctx: PlayActionContext,
    interaction: discord.Interaction,
    target_player_id: int,
    food_card: str,
):
    """
    Begin the 'steal' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
        target_player_id (int): The ID of the target player.
        food_card (str): The food card used for stealing.
    """
    if not interaction.user:
        return
    async with BlockingNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda target_interaction: food_combo_finish(
            ctx, interaction, target_interaction, target_player_id
        ),
    ) as view:
        await interaction.respond(
            MESSAGES["before_steal"].format(
                CARDS[food_card]["emoji"], interaction.user.id, target_player_id
            ),
            view=view,
        )


async def food_combo_finish(
    ctx: PlayActionContext,
    interaction: discord.Interaction,
    target_interaction: discord.Interaction | None,
    target_player_id: int,
):
    """
    Finalize the 'steal' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
        target_interaction (discord.Interaction | None): The interaction of the target player.
        target_player_id (int): The ID of the target player.
    """
    if not interaction.user:
        return
    target_hand = ctx.game.hands[target_player_id]
    if not target_hand:
        await interaction.respond(
            MESSAGES["no_cards_to_steal"].format(
                ctx.game.current_player_id, target_player_id
            )
        )
        return
    stolen_card = random.choice(target_hand)
    ctx.game.hands[target_player_id].remove(stolen_card)
    ctx.game.current_player_hand.append(stolen_card)
    await ctx.update_view(interaction)
    await interaction.respond(
        MESSAGES["stolen_card_public"].format(
            ctx.game.current_player_id, target_player_id
        )
    )
    await interaction.respond(
        MESSAGES["stolen_card_you"].format(
            CARDS[stolen_card]["emoji"], CARDS[stolen_card]["title"]
        ),
        ephemeral=True,
    )
    if target_interaction:
        await target_interaction.respond(
            MESSAGES["stolen_card_them"].format(
                ctx.game.current_player_id,
                CARDS[stolen_card]["emoji"],
                CARDS[stolen_card]["title"],
            ),
            ephemeral=True,
        )


async def defuse_finish(ctx: PlayActionContext, interaction: discord.Interaction):
    """
    Finalize the 'defuse' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        raise TypeError("interaction.user is None")
    await interaction.respond(MESSAGES["defused"].format(interaction.user.id))
    await ctx.end_turn(interaction)


async def radioeggtive_finish(self, interaction: discord.Interaction):
    """
    Finalize the 'radioeggtive' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        raise TypeError("interaction.user is None")
    await interaction.respond(MESSAGES["radioeggtive"].format(interaction.user.id))
    await self.end_turn(interaction)


async def attegg_finish(
    ctx: PlayActionContext, interaction: discord.Interaction, target_player_id=None
):
    """
    Finalize the 'attegg' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
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
    """
    Finalize the 'skip' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.message:
        return
    await ctx.disable_view(interaction)
    ctx.game.next_turn()
    await ctx.end_turn(interaction)


async def draw_from_bottom(ctx: PlayActionContext, interaction: discord.Interaction):
    """
    Handle the 'draw from bottom' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        return
    target_player_id = (
        ctx.game.next_player_id if ctx.game.draw_in_turn == 0 else interaction.user.id
    )
    async with BlockingNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: draw_card(ctx, interaction, index=0),
    ) as view:
        await interaction.respond(
            MESSAGES["before_draw_from_bottom"].format(
                interaction.user.id, target_player_id
            ),
            view=view,
        )


async def targeted_attegg(ctx: PlayActionContext, interaction: discord.Interaction):
    """
    Handle the 'targeted attegg' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        return
    async with ChoosePlayerView(
        ctx.copy(),
        lambda target_player_id: targeted_attegg_begin(
            ctx, interaction, target_player_id
        ),
    ) as view:
        await interaction.respond(
            MESSAGES["targeted_attegg_prompt"], view=view, ephemeral=True
        )


async def targeted_attegg_begin(
    ctx: PlayActionContext, interaction: discord.Interaction, target_player_id: int
):
    """
    Begin the 'targeted attegg' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        return
    async with BlockingNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: attegg_finish(ctx, interaction, target_player_id),
    ) as view:
        await interaction.respond(
            MESSAGES["before_targeted_attegg"].format(
                interaction.user.id,
                target_player_id,
                ctx.game.draw_in_turn + 2,
            ),
            view=view,
        )


async def alter_future(ctx: PlayActionContext, interaction: discord.Interaction):
    """
    Handle the 'alter future' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        return
    prev_deck = ctx.game.deck.copy()
    async with AlterFutureView(
        ctx.copy(), lambda: alter_future_finish(ctx, interaction, prev_deck), 3
    ) as view:
        await interaction.respond(view=view, ephemeral=True)


async def alter_future_finish(
    ctx: PlayActionContext, interaction: discord.Interaction, prev_deck
):
    """
    Finalize the 'alter future' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
        prev_deck (list): The previous deck.
    """
    if not interaction.user:
        return
    async with NopeView(ctx.copy(), lambda: undo_alter_future(ctx, prev_deck)) as view:
        await interaction.respond(
            MESSAGES["altered_future"].format(interaction.user.id),
            view=view,
        )


def undo_alter_future(ctx: PlayActionContext, prev_deck):
    """
    Undo the 'alter future' action.
    """
    ctx.game.deck = prev_deck


async def reverse(ctx: PlayActionContext, interaction: discord.Interaction):
    """
    Handle the 'reverse' action.

    Args:
        interaction (discord.Interaction): The interaction that triggered the action.
    """
    if not interaction.user:
        return
    ctx.game.reverse()
    target_player_id = (
        ctx.game.next_player_id if ctx.game.draw_in_turn == 0 else interaction.user.id
    )
    async with BlockingNopeView(
        ctx=ctx.copy(),
        target_player_id=target_player_id,
        nope_callback_action=ctx.game.reverse,
        ok_callback_action=lambda _: skip_finish(ctx, interaction),
    ) as view:
        await interaction.respond(
            MESSAGES["before_reverse"].format(interaction.user.id, target_player_id),
            view=view,
        )
