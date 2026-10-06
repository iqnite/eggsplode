"""
Contains effects for cards that directly kill players, such as Eggsplode.
Also contains defuse-like actions.
"""

import random
from typing import TYPE_CHECKING

import discord

from eggsplode import database
from eggsplode.strings import achievement_unlocked_message, format_message
from eggsplode.ui import ChoosePlayerView, DefuseView, TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


class GameOverView(discord.ui.DesignerView):
    def __init__(
        self, winner: int, games_won: int, unlocked_achievement: str | None = None
    ):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.TextDisplay(
                format_message("game_over", winner)
                + (
                    "\n" + achievement_unlocked_message(f"{games_won}_wins")
                    if games_won in [1, 10, 50]
                    else ""
                )
                + (
                    ("\n" + achievement_unlocked_message(unlocked_achievement))
                    if unlocked_achievement
                    else ""
                )
            )
        )
        self.funding_container = discord.ui.Container(color=discord.Color.yellow())
        self.add_item(self.funding_container)
        self.funding_container.add_section(
            discord.ui.TextDisplay(format_message("funding_title")),
            accessory=discord.ui.Button(
                label=format_message("link_support_label"),
                url=format_message("link_support_url"),
                emoji="♥️",
            ),
        )


async def game_over(game: "Game", interaction: discord.Interaction | None):
    winner = game.players[0]
    games_won = await database.increase_games_won(winner)
    unlocked_achievement = None
    if game.config.get("recipe_id") == "classic" and game.hands.get(winner) is not None:
        winner_hand_len = len(game.hands[winner])
        if winner_hand_len == 0 and await database.set_user_won_classic_without_cards(
            winner
        ):
            unlocked_achievement = "last_blood"
        if (
            await database.set_user_most_cards_won_classic(winner, winner_hand_len)
            < 10
            <= winner_hand_len
        ):
            unlocked_achievement = "hoarder"
        if winner not in game.defusers:
            if await database.set_user_won_classic_without_defuse(winner):
                unlocked_achievement = "safe"
    if (
        await database.set_user_largest_player_count_won(
            winner, len(game.config["players"])
        )
        < 5
        <= len(game.config["players"])
    ):
        unlocked_achievement = "victory_royale"
    await game.send(
        GameOverView(winner, games_won, unlocked_achievement),
        interaction,
    )
    await game.events.game_end()


async def eggsplode(
    game: "Game", interaction: discord.Interaction | None, timed_out: bool = False
):
    if "defuse" in game.current_player_hand:
        await database.increase_user_card_usage(game.current_player_id, "defuse")
        game.defusers.add(game.current_player_id)
        game.current_player_hand.remove("defuse")
        if timed_out or interaction is None:
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
    msg = await game.send(
        TextView(
            "eggsploded",
            prev_player,
            format_message("death_messages", random_from_list=True),
        ),
        interaction,
    )
    add_death_message_id(game, msg)
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
    game: "Game", interaction: discord.Interaction | None, timed_out: bool = False
):
    if timed_out or interaction is None:
        game.deck.insert(random.randint(0, len(game.deck)), "radioeggtive_face_up")
        await game.send(TextView("radioeggtive", game.current_player_id), interaction)
        return
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
    game: "Game",
    interaction: discord.Interaction | None,
    timed_out: bool | None = False,
):
    prev_player = game.current_player_id
    game.remaining_turns = 0
    achievement_message = format_message("death_messages", random_from_list=True)
    if (
        interaction is not None
        and interaction.user is not None
        and not timed_out
        and (
            interaction.user.id
            in game.players_with_cards(
                "skip",
                "super_skip",
                "attegg",
                "targeted_attegg",
                "bury",
                "reverse",
            )
        )
    ):
        warnings_ignored = await database.increase_user_warnings_ignored(
            game.current_player_id
        )
        if warnings_ignored == 1:
            achievement_message = achievement_unlocked_message("cant_read")
    game.remove_player(prev_player)
    msg = await game.send(
        TextView(
            "radioeggtive_face_up",
            prev_player,
            achievement_message,
        ),
        interaction,
    )
    add_death_message_id(game, msg)
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
        await database.increase_user_card_usage(target_player_id, "defuse")
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
        msg = await game.send(
            TextView(
                "eggsperiment_pair_eggsploded" if pair else "eggsperiment_eggsploded",
                game.current_player_id,
                target_player_id,
                format_message("death_messages", random_from_list=True),
            ),
            interaction,
        )
        add_death_message_id(game, msg)
        game.remove_player(target_player_id)
        if len(game.players) == 1:
            await game_over(game, interaction)
            return
    await game.events.action_end()


def add_death_message_id(game: "Game", msg):
    if msg is None:
        message_id = None
    elif isinstance(msg, discord.Interaction) and msg.message:
        message_id = msg.message.id
    else:
        message_id = msg.id
    if message_id:
        game.app.death_message_ids.add(message_id)


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
