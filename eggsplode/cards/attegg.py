"""
Contains effects for Attegg cards.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.strings import format_message
from eggsplode.ui import ChoosePlayerView, NopeView

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


async def attegg_finish(game: "Game", target_player_id=None, turns: int = 3):
    target_player_id = target_player_id or game.next_player_id
    prev_to_draw_in_turn = game.remaining_turns
    game.remaining_turns = 0
    game.current_player_id = target_player_id
    game.remaining_turns = prev_to_draw_in_turn + turns
    await game.events.turn_end()


async def targeted_attegg_begin(game: "Game", _, target_player_id: int):
    view = NopeView(
        game,
        message=format_message(
            "before_targeted_attegg",
            game.current_player_id,
            target_player_id,
            game.remaining_turns + 2,
        ),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: attegg_finish(game, target_player_id),
    )
    await game.send(view=view)


async def targeted_attegg(game: "Game", interaction: discord.Interaction):
    view = ChoosePlayerView(
        game,
        lambda target_player_id: targeted_attegg_begin(
            game, interaction, target_player_id
        ),
    )
    await view.create_user_selection()
    await interaction.respond(view=view, ephemeral=True)


async def self_attegg(game: "Game", _):
    await attegg_finish(game, game.current_player_id, turns=4)
