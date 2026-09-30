"""
Contains the string to function mappings for card actions.
"""

from typing import TYPE_CHECKING

import discord

from .atteggs import attegg, self_attegg, targeted_attegg
from .bombs import eggsperiment, eggsplode, radioeggtive, radioeggtive_face_up
from .deck import deck_count, radioeggtive_warning, shuffle, swap_top_bottom
from .future import alter_future, see_future, share_future
from .skips import bury, dig_deeper, draw_from_bottom, reverse, skip, super_skip
from .steal import begg, food_combo, raid, trade

if TYPE_CHECKING:
    from eggsplode.core import Game

PLAY_ACTIONS = {
    "attegg": attegg,
    "skip": skip,
    "shuffle": shuffle,
    "see_future": see_future,
    "draw_from_bottom": draw_from_bottom,
    "swap_top_bottom": swap_top_bottom,
    "targeted_attegg": targeted_attegg,
    "alter_future": alter_future,
    "alter_future_now": alter_future,
    "reverse": reverse,
    "eggsperiment": eggsperiment,
    "super_skip": super_skip,
    "self_attegg": self_attegg,
    "bury": bury,
    "share_future": share_future,
    "dig_deeper": dig_deeper,
    "begg": begg,
    "steal": food_combo,
    "trade": trade,
    "raid": raid,
}


for i in range(5):

    def create_food_combo_function(i: int):
        def food_combo_function(
            game: "Game", interaction: discord.Interaction, i: int = i
        ):
            return food_combo(game, interaction, f"food{i}")

        return food_combo_function

    PLAY_ACTIONS[f"food{i}"] = create_food_combo_function(i)

DRAW_ACTIONS = {
    "eggsplode": eggsplode,
    "radioeggtive": radioeggtive,
    "radioeggtive_face_up": radioeggtive_face_up,
}

TURN_WARNINGS = [
    deck_count,
    radioeggtive_warning,
]
