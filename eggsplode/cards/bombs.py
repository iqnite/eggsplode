"""
Contains effects for cards that directly kill players, such as Eggsplode.
Also contains defuse-like actions.
"""

import random
from typing import TYPE_CHECKING
import discord
from eggsplode.strings import format_message
from eggsplode.ui import ChoosePlayerView, DefuseView, TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


class GameOverView(discord.ui.DesignerView):
    def __init__(self, winner):
        super().__init__(timeout=None)
        self.add_item(discord.ui.TextDisplay(format_message("game_over", winner)))
        self.funding_container = discord.ui.Container(color=discord.Color.yellow())
        self.add_item(self.funding_container)
        self.funding_container.add_section(
            discord.ui.TextDisplay(format_message("funding_title")),
            accessory=discord.ui.Button(
                label="Support the development",
                url="https://buymeacoffee.com/phorb",
                emoji="♥️",
            ),
        )


async def game_over(game: "Game", interaction: discord.Interaction | None):
    await game.send(GameOverView(game.players[0]), interaction)
    await game.events.game_end()


async def eggsplode(
    game: "Game", interaction: discord.Interaction, timed_out: bool = False
):
    if "defuse" in game.current_player_hand:
        game.current_player_hand.remove("defuse")
        if timed_out:
            game.deck.insert(random.randint(0, len(game.deck)), "eggsplode")
            await game.send(TextView("defused", game.current_player_id), interaction)
            return
        view = DefuseView(
            game,
            lambda: defuse_finish(game),
            card="eggsplode",
        )
        if await view.skip_if_deck_empty():
            return
        await interaction.respond(view=view, ephemeral=True)
        return
    prev_player = game.current_player_id
    game.remove_player(prev_player)
    game.remaining_turns = 0
    await game.send(
        TextView(
            "eggsploded",
            prev_player,
            format_message("death_messages", random_from_list=True),
        ),
        interaction,
    )
    if len(game.players) == 1:
        await game_over(game, interaction)
        return
    if not timed_out:
        await game.events.turn_end()


async def defuse_finish(game: "Game"):
    await game.send(TextView("defused", game.current_player_id), None)
    await game.events.turn_end()


async def radioeggtive_finish(game: "Game"):
    await game.send(TextView("radioeggtive", game.current_player_id), None)
    await game.events.turn_end()


async def radioeggtive(
    game: "Game", interaction: discord.Interaction, timed_out: bool = False
):
    if timed_out:
        game.deck.insert(random.randint(0, len(game.deck)), "radioeggtive_face_up")
        await game.send(TextView("radioeggtive", game.current_player_id), interaction)
    else:
        view = DefuseView(
            game,
            lambda: radioeggtive_finish(game),
            card="radioeggtive_face_up",
            prev_card="radioeggtive",
        )
        if await view.skip_if_deck_empty():
            return
        await interaction.respond(view=view, ephemeral=True)


async def radioeggtive_face_up(
    game: "Game", interaction: discord.Interaction, timed_out: bool | None = False
):
    prev_player = game.current_player_id
    game.remove_player(prev_player)
    game.remaining_turns = 0
    await game.send(
        TextView(
            "radioeggtive_face_up",
            prev_player,
            format_message("death_messages", random_from_list=True),
        ),
        interaction,
    )
    if len(game.players) == 1:
        await game_over(game, interaction)
        return
    if not timed_out:
        await game.events.turn_end()


async def eggsperiment_finish(
    game: "Game",
    interaction: discord.Interaction | None,
    target_player_id: int,
    pair=False,
):
    if "defuse" in game.hands[target_player_id]:
        game.hands[target_player_id].remove("defuse")
        await game.send(
            TextView(
                "eggsperiment_pair_defused" if pair else "eggsperiment_defused",
                game.current_player_id,
                target_player_id,
            ),
            interaction,
        )
    else:
        await game.send(
            TextView(
                "eggsperiment_pair_eggsploded" if pair else "eggsperiment_eggsploded",
                game.current_player_id,
                target_player_id,
                format_message("death_messages", random_from_list=True),
            ),
            interaction,
        )
        del game.players[game.players.index(target_player_id)]
        del game.hands[target_player_id]
        game.current_player = game.players.index(game.current_player_id)
        if len(game.players) == 1:
            await game_over(game, interaction)
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
        if await view.skip_if_single_option():
            return
        await view.create_user_selection()
        await interaction.respond(view=view, ephemeral=True)
        return
    players_with_eggsperiment = game.players_with_cards("eggsperiment")
    if players_with_eggsperiment:
        game.hands[players_with_eggsperiment[0]].remove("eggsperiment")
        await eggsperiment_finish(game, interaction, players_with_eggsperiment[0])
        return
    game.current_player_hand.append("eggsperiment")
    await game.send(
        TextView("eggsperiment_exposed", game.current_player_id), interaction
    )
    await game.events.action_end()
