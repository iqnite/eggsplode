"""
Contains effects for cards that steal from other players.
"""

import random
from typing import TYPE_CHECKING
import discord
from eggsplode.strings import available_cards, format_message, replace_emojis, tooltip
from eggsplode.ui import ChoosePlayerView, NopeView, TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


async def food_combo_finish(
    game: "Game",
    interaction: discord.Interaction,
    target_interaction: discord.Interaction | None,
    target_player_id: int,
):
    target_hand = game.hands[target_player_id]
    if not target_hand:
        await game.send(
            view=TextView("no_cards_to_steal", game.current_player_id, target_player_id)
        )
        await game.events.action_end()
        return
    stolen_card = random.choice(target_hand)
    game.hands[target_player_id].remove(stolen_card)
    game.current_player_hand.append(stolen_card)
    await game.send(
        view=TextView("stolen_card_public", game.current_player_id, target_player_id)
    )
    try:
        await interaction.respond(
            view=TextView(
                "stolen_card_you",
                tooltip(stolen_card),
            ),
            ephemeral=True,
        )
        if target_interaction:
            await target_interaction.respond(
                view=TextView(
                    "stolen_card_them",
                    game.current_player_id,
                    tooltip(stolen_card),
                ),
                ephemeral=True,
            )
    finally:
        await game.events.action_end()


async def food_combo_begin(
    game: "Game",
    interaction: discord.Interaction,
    target_player_id: int,
    food_card: str,
):
    view = NopeView(
        game,
        message=format_message(
            "before_steal",
            replace_emojis(available_cards[food_card]["emoji"]),
            game.current_player_id,
            target_player_id,
        ),
        target_player_id=target_player_id,
        ok_callback_action=lambda target_interaction: food_combo_finish(
            game, interaction, target_interaction, target_player_id
        ),
    )
    await game.send(view=view)


async def food_combo(game: "Game", interaction: discord.Interaction, card: str):
    if not game.any_player_has_cards():
        await interaction.respond(
            view=TextView("no_players_have_cards"),
            ephemeral=True,
            delete_after=10,
        )
        return
    if card in game.current_player_hand:
        game.current_player_hand.remove(card)
    else:
        await interaction.respond(
            view=TextView("card_not_found", card),
            ephemeral=True,
            delete_after=10,
        )
        return
    view = ChoosePlayerView(
        game,
        lambda target_player_id: food_combo_begin(
            game, interaction, target_player_id, card
        ),
        condition=lambda user_id: user_id != game.current_player_id
        and len(game.hands[user_id]) > 0,
    )
    await view.create_user_selection()
    await interaction.respond(view=view, ephemeral=True)
