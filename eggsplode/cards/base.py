"""
Contains card effects for the base game.
"""

import random
import discord

from ..base_views import BaseView
from ..game_logic import Game
from ..nope import ExplicitNopeView
from ..selections import ChoosePlayerView, DefuseView
from ..strings import CARDS, get_message, replace_emojis


async def draw_card(game: Game, interaction: discord.Interaction, index=-1):
    if not interaction.user:
        return
    card, hold = await game.draw_from(interaction, index=index)
    if hold:
        await game.log(get_message("user_drew_card").format(interaction.user.id))
        await interaction.respond(
            get_message("you_drew_card").format(
                replace_emojis(CARDS[card]["emoji"]), CARDS[card]["title"]
            ),
            ephemeral=True,
            delete_after=10,
        )
        await game.events.turn_end()


async def attegg(game: Game, interaction: discord.Interaction):
    if not interaction.user:
        return
    async with ExplicitNopeView(
        game=game,
        target_player_id=game.next_player_id,
        ok_callback_action=lambda _: attegg_finish(game),
    ) as view:
        await game.log(
            get_message("before_attegg").format(
                interaction.user.id,
                game.next_player_id,
                game.draw_in_turn + 2,
            ),
            view=view,
        )


async def shuffle(game: Game, interaction: discord.Interaction):
    if not interaction.user:
        return
    game.shuffle_deck()
    await game.log(get_message("shuffled").format(interaction.user.id))
    await game.events.action_end()


async def predict(game: Game, interaction: discord.Interaction):
    if not interaction.user:
        return
    next_cards = "\n".join(
        get_message("bold_list_item").format(
            replace_emojis(CARDS[card]["emoji"]), CARDS[card]["title"]
        )
        for card in game.deck[-1:-4:-1]
    )
    await game.log(
        get_message("predicted").format(interaction.user.id),
    )
    await interaction.respond(
        "\n".join((get_message("next_cards"), next_cards)),
        ephemeral=True,
        delete_after=20,
    )
    await game.events.action_end()


async def food_combo(game: Game, interaction: discord.Interaction, selected: str):
    if not interaction.user:
        return
    if not game.any_player_has_cards():
        await interaction.respond(
            get_message("no_players_have_cards"), ephemeral=True, delete_after=10
        )
        return
    assert game.current_player_hand.count(selected) >= 2
    for _ in range(2):
        game.current_player_hand.remove(selected)
    view = ChoosePlayerView(
        game,
        lambda target_player_id: food_combo_begin(
            game, interaction, target_player_id, selected
        ),
        condition=lambda user_id: user_id != game.current_player_id
        and len(game.hands[user_id]) > 0,
    )
    await view.create_user_selection()
    await interaction.respond(
        get_message("steal_prompt"), view=view, ephemeral=True, delete_after=30
    )


async def food_combo_begin(
    game: Game, interaction: discord.Interaction, target_player_id: int, food_card: str
):
    if not interaction.user:
        return
    async with ExplicitNopeView(
        game,
        target_player_id,
        lambda target_interaction: food_combo_finish(
            game, interaction, target_interaction, target_player_id
        ),
    ) as view:
        await game.log(
            get_message("before_steal").format(
                replace_emojis(CARDS[food_card]["emoji"]),
                interaction.user.id,
                target_player_id,
            ),
            view=view,
        )


async def food_combo_finish(
    game: Game,
    interaction: discord.Interaction,
    target_interaction: discord.Interaction | None,
    target_player_id: int,
):
    if not interaction.user:
        return
    target_hand = game.hands[target_player_id]
    if not target_hand:
        await game.log(
            get_message("no_cards_to_steal").format(
                game.current_player_id, target_player_id
            )
        )
        await game.events.action_end()
        return
    stolen_card = random.choice(target_hand)
    game.hands[target_player_id].remove(stolen_card)
    game.current_player_hand.append(stolen_card)
    await game.log(
        get_message("stolen_card_public").format(
            game.current_player_id, target_player_id
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
                    game.current_player_id,
                    replace_emojis(CARDS[stolen_card]["emoji"]),
                    CARDS[stolen_card]["title"],
                ),
                ephemeral=True,
                delete_after=10,
            )
    finally:
        await game.events.action_end()


async def defuse_finish(game: Game):
    await game.log(get_message("defused").format(game.current_player_id))
    await game.events.turn_end()


async def attegg_finish(game: Game, target_player_id=None):
    target_player_id = target_player_id or game.next_player_id
    prev_to_draw_in_turn = game.draw_in_turn
    game.draw_in_turn = 0
    game.current_player_id = target_player_id
    game.draw_in_turn = prev_to_draw_in_turn + 3
    await game.events.turn_end()


async def skip(game: Game, _):
    await game.log(get_message("skipped").format(game.current_player_id))
    await game.events.turn_end()


async def eggsplode(
    game: Game, interaction: discord.Interaction, timed_out: bool = False
):
    if "defuse" in game.hands[game.current_player_id]:
        game.hands[game.current_player_id].remove("defuse")
        if timed_out:
            game.deck.insert(random.randint(1, len(game.deck)), "eggsplode")
            await game.log(get_message("defused").format(game.current_player_id))
        else:
            view = DefuseView(
                game,
                lambda: defuse_finish(game),
                card="eggsplode",
            )
            await view.send(interaction)
        return
    prev_player = game.current_player_id
    game.remove_player(prev_player)
    game.draw_in_turn = 0
    await game.log(get_message("eggsploded").format(prev_player))
    if len(game.players) == 1:
        await game_over(game, interaction)


async def game_over(game: Game, interaction: discord.Interaction):
    if not interaction.user:
        return
    await game.log(
        get_message("game_over").format(game.players[0]),
        view=BaseView(game),
    )
    await game.events.game_end()


def deck_count(game: Game) -> str:
    return get_message("turn_warning").format(
        len(game.deck),
        game.deck.count("eggsplode"),
    )


PLAY_ACTIONS = {
    "attegg": attegg,
    "skip": skip,
    "shuffle": shuffle,
    "predict": predict,
}

DRAW_ACTIONS = {
    "eggsplode": eggsplode,
}

TURN_WARNINGS = [
    deck_count,
]
