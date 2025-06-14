"""
Contains card effects for the base game.
"""

import random
from typing import TYPE_CHECKING
import discord
from eggsplode.ui import NopeView, ChoosePlayerView, DefuseView
from eggsplode.strings import CARDS, format_message, replace_emojis, tooltip
from eggsplode.ui.base import TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


async def attegg(game: "Game", _):
    view = NopeView(
        game=game,
        message=format_message(
            "before_attegg",
            game.current_player_id,
            game.next_player_id,
            game.remaining_turns + 2,
        ),
        target_player_id=game.next_player_id,
        ok_callback_action=lambda _: attegg_finish(game),
    )
    await game.send(view=view)


async def shuffle(game: "Game", _):
    game.shuffle_deck()
    await game.send(view=TextView("shuffled", game.current_player_id))
    await game.events.action_end()


async def predict(game: "Game", interaction: discord.Interaction):
    next_cards = "\n".join(
        format_message(
            "list_item_2", replace_emojis(CARDS[card]["emoji"]), tooltip(card)
        )
        for card in game.deck[-1:-4:-1]
    )
    await game.send(view=TextView("predicted", game.current_player_id))
    await interaction.respond(
        view=TextView(
            "\n".join((format_message("next_cards"), next_cards)), verbatim=True
        ),
        ephemeral=True,
    )
    await game.events.action_end()


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
            replace_emojis(CARDS[food_card]["emoji"]),
            game.current_player_id,
            target_player_id,
        ),
        target_player_id=target_player_id,
        ok_callback_action=lambda target_interaction: food_combo_finish(
            game, interaction, target_interaction, target_player_id
        ),
    )
    await game.send(view=view)


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
                replace_emojis(CARDS[stolen_card]["emoji"]),
                tooltip(stolen_card),
            ),
            ephemeral=True,
        )
        if target_interaction:
            await target_interaction.respond(
                view=TextView(
                    "stolen_card_them",
                    game.current_player_id,
                    replace_emojis(CARDS[stolen_card]["emoji"]),
                    tooltip(stolen_card),
                ),
                ephemeral=True,
            )
    finally:
        await game.events.action_end()


async def defuse_finish(game: "Game"):
    await game.send(view=TextView("defused", game.current_player_id))
    await game.events.turn_end()


async def attegg_finish(game: "Game", target_player_id=None):
    target_player_id = target_player_id or game.next_player_id
    prev_to_draw_in_turn = game.remaining_turns
    game.remaining_turns = 0
    game.current_player_id = target_player_id
    game.remaining_turns = prev_to_draw_in_turn + 3
    await game.events.turn_end()


async def skip(game: "Game", _):
    await game.send(view=TextView("skipped", game.current_player_id))
    await game.events.turn_end()


async def eggsplode(
    game: "Game", interaction: discord.Interaction, timed_out: bool = False
):
    if "defuse" in game.hands[game.current_player_id]:
        game.hands[game.current_player_id].remove("defuse")
        if timed_out:
            game.deck.insert(random.randint(0, len(game.deck)), "eggsplode")
            await game.send(view=TextView("defused", game.current_player_id))
        else:
            view = DefuseView(
                game,
                lambda: defuse_finish(game),
                card="eggsplode",
            )
            await interaction.respond(view=view, ephemeral=True)
        return
    prev_player = game.current_player_id
    game.remove_player(prev_player)
    game.remaining_turns = 0
    await game.send(view=TextView("eggsploded", prev_player))
    if len(game.players) == 1:
        await game_over(game, interaction)
        return
    await game.events.turn_end()


async def game_over(game: "Game", _):
    await game.send(view=TextView("game_over", game.players[0]))
    await game.events.game_end()


def deck_count(game: "Game") -> str:
    return format_message(
        "turn_warning",
        len(game.deck),
        game.deck.count("eggsplode"),
    )


def setup(game: "Game"):
    for hand in game.hands.values():
        hand.append("defuse")
    game.deck += ["defuse"] * int(game.config.get("deck_defuse_cards", 0))
    game.deck += ["eggsplode"] * max(
        int(
            game.config.get(
                "deck_eggsplode_cards",
                max(len(game.players) - 1, 2),
            )
        ),
        len(game.players) - 1,
    )


PLAY_ACTIONS = {
    "attegg": attegg,
    "skip": skip,
    "shuffle": shuffle,
    "predict": predict,
} | {
    f"food{i}": lambda game, interaction, i=i: food_combo(game, interaction, f"food{i}")
    for i in range(5)
}

DRAW_ACTIONS = {
    "eggsplode": eggsplode,
}

TURN_WARNINGS = [
    deck_count,
]

SETUP_ACTIONS = [
    setup,
]
