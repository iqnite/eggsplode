"""
Contains effects for cards that directly kill players, such as Eggsplode.
Also contains defuse-like actions.
"""

import random
from typing import TYPE_CHECKING
import discord
from eggsplode.ui import ChoosePlayerView, DefuseView, TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


async def game_over(game: "Game", _):
    await game.send(view=TextView("game_over", game.players[0]))
    await game.events.game_end()


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


async def defuse_finish(game: "Game"):
    await game.send(view=TextView("defused", game.current_player_id))
    await game.events.turn_end()


async def radioeggtive_finish(game: "Game"):
    await game.send(view=TextView("radioeggtive", game.current_player_id))
    await game.events.turn_end()


async def radioeggtive(
    game: "Game", interaction: discord.Interaction, timed_out: bool = False
):
    if timed_out:
        game.deck.insert(random.randint(0, len(game.deck)), "radioeggtive_face_up")
        await game.send(view=TextView("radioeggtive", game.current_player_id))
    else:
        view = DefuseView(
            game,
            lambda: radioeggtive_finish(game),
            card="radioeggtive_face_up",
            prev_card="radioeggtive",
        )
        await interaction.respond(view=view, ephemeral=True)


async def radioeggtive_face_up(game: "Game", interaction: discord.Interaction, _):
    prev_player = game.current_player_id
    game.remove_player(prev_player)
    game.remaining_turns = 0
    await game.send(view=TextView("radioeggtive_face_up", prev_player))
    if len(game.players) == 1:
        await game_over(game, interaction)
        return
    await game.events.turn_end()


async def eggsperiment_finish(game: "Game", _, target_player_id: int, pair=False):
    current_player_id = game.current_player_id
    if "defuse" in game.hands[target_player_id]:
        game.hands[target_player_id].remove("defuse")
        await game.send(
            view=TextView(
                "eggsperiment_pair_defused" if pair else "eggsperiment_defused",
                current_player_id,
                target_player_id,
            ),
        )
    else:
        await game.send(
            view=TextView(
                "eggsperiment_pair_eggsploded" if pair else "eggsperiment_eggsploded",
                current_player_id,
                target_player_id,
            ),
        )
        del game.players[game.players.index(target_player_id)]
        del game.hands[target_player_id]
        game.current_player = game.players.index(current_player_id)
        if len(game.players) == 1:
            await game_over(game, _)
            return
    await game.events.action_end()


async def eggsperiment(game: "Game", interaction: discord.Interaction):
    if game.current_player_hand.count("eggsperiment") == 1:
        game.current_player_hand.remove("eggsperiment")
        view = ChoosePlayerView(
            game,
            lambda target_player_id: eggsperiment_finish(
                game, interaction, target_player_id, pair=True
            ),
            condition=lambda user_id: user_id != game.current_player_id,
        )
        await view.create_user_selection()
        await interaction.respond(view=view, ephemeral=True)
        return
    players_with_eggsperiment = game.players_with_cards("eggsperiment")
    if players_with_eggsperiment:
        game.hands[players_with_eggsperiment[0]].remove("eggsperiment")
        await eggsperiment_finish(game, interaction, players_with_eggsperiment[0])
        return
    game.current_player_hand.append("eggsperiment")
    await game.send(view=TextView("eggsperiment_exposed", game.current_player_id))
    await game.events.action_end()
