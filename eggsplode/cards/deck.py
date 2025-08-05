"""
Contains effects for cards and actions affecting the deck.
"""

from typing import TYPE_CHECKING
from eggsplode.strings import format_message
from eggsplode.ui import TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


async def shuffle(game: "Game", _):
    game.shuffle_deck()
    await game.send(view=TextView("shuffled", game.current_player_id))
    await game.events.action_end()


async def swap_top_bottom(game: "Game", _):
    game.deck[-1], game.deck[0] = game.deck[0], game.deck[-1]
    await game.send(view=TextView("swapped_top_bottom", game.current_player_id))
    await game.events.action_end()


def deck_count(game: "Game") -> str:
    return format_message(
        "turn_warning",
        len(game.deck),
        game.deck.count("eggsplode"),
    )


def radioeggtive_warning(game: "Game") -> str:
    radioeggtive_countdown = game.card_comes_in("radioeggtive_face_up")
    return (
        format_message("play_prompt_radioeggtive_now")
        if radioeggtive_countdown == 0
        else ""
    )
