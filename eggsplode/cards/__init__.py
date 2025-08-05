"""
Contains the string to function mappings for card actions.
"""

from .skip import bury, dig_deeper, draw_from_bottom, reverse, skip, super_skip
from .bombs import eggsplode, radioeggtive, radioeggtive_face_up, eggsperiment
from .deck import deck_count, radioeggtive_warning, shuffle, swap_top_bottom
from .steal import food_combo
from .future import alter_future, see_future, share_future
from .attegg import attegg, self_attegg, targeted_attegg

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
} | {
    f"food{i}": lambda game, interaction, i=i: food_combo(game, interaction, f"food{i}")
    for i in range(5)
}

DRAW_ACTIONS = {
    "eggsplode": eggsplode,
    "radioeggtive": radioeggtive,
    "radioeggtive_face_up": radioeggtive_face_up,
}

TURN_WARNINGS = [
    deck_count,
    radioeggtive_warning,
]
