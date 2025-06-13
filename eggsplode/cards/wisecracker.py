"""
Contains card effects for the Wise-Cracker expansion.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.cards.base import game_over
from eggsplode.ui import ChoosePlayerView
from eggsplode.strings import get_message

if TYPE_CHECKING:
    from eggsplode.core import Game


async def wisecracker(game: "Game", interaction: discord.Interaction):
    if game.current_player_hand.count("wisecracker") == 1:
        game.current_player_hand.remove("wisecracker")
        view = ChoosePlayerView(
            game,
            lambda target_player_id: wisecracker_finish(
                game, interaction, target_player_id
            ),
            condition=lambda user_id: user_id != game.current_player_id,
        )
        await view.create_user_selection()
        await interaction.respond(
            get_message("targeted_attegg_prompt"), view=view, ephemeral=True
        )
        return
    players_with_wisecracker = game.players_with_cards("wisecracker")
    if players_with_wisecracker:
        await wisecracker_finish(game, interaction, players_with_wisecracker[0])
        game.hands[players_with_wisecracker[0]].remove("wisecracker")
        return
    game.current_player_hand.append("wisecracker")
    await game.send(get_message("wisecracker_exposed").format(game.current_player_id), anchor=interaction)
    await game.events.action_end()


async def wisecracker_finish(
    game: "Game", interaction: discord.Interaction, target_player_id: int
):
    if "defuse" in game.hands[target_player_id]:
        game.hands[target_player_id].remove("defuse")
        await game.send(
            get_message("wisecracker_defused").format(
                game.current_player_id, target_player_id
            ),
            anchor=interaction,
        )
    else:
        del game.players[game.players.index(target_player_id)]
        del game.hands[target_player_id]
        await game.send(
            get_message("wisecracker_eggsploded").format(
                game.current_player_id, target_player_id
            ),
            anchor=interaction,
        )
        if len(game.players) == 1:
            await game_over(game, interaction)
            return
    await game.events.action_end()


def setup(game: "Game"):
    game.deck += ["wisecracker"] * 2


PLAY_ACTIONS = {
    "wisecracker": wisecracker,
}

SETUP_ACTIONS = [
    setup,
]
