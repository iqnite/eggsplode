"""
Contains card effects for the Wise-Cracker expansion.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.cards.base import game_over, show_next_cards, skip, attegg_finish
from eggsplode.cards.radioeggtive import AlterFutureView
from eggsplode.ui import ChoosePlayerView, DefuseView
from eggsplode.ui.base import TextView
from eggsplode.strings import format_message

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
        await interaction.respond(view=view, ephemeral=True)
        return
    players_with_wisecracker = game.players_with_cards("wisecracker")
    if players_with_wisecracker:
        game.hands[players_with_wisecracker[0]].remove("wisecracker")
        await wisecracker_finish(game, interaction, players_with_wisecracker[0])
        return
    game.current_player_hand.append("wisecracker")
    await game.send(view=TextView("wisecracker_exposed", game.current_player_id))
    await game.events.action_end()


async def wisecracker_finish(game: "Game", _, target_player_id: int):
    if "defuse" in game.hands[target_player_id]:
        game.hands[target_player_id].remove("defuse")
        await game.send(
            view=TextView(
                "wisecracker_defused", game.current_player_id, target_player_id
            ),
        )
    else:
        await game.send(
            view=TextView(
                "wisecracker_eggsploded", game.current_player_id, target_player_id
            ),
        )
        del game.players[game.players.index(target_player_id)]
        del game.hands[target_player_id]
        if len(game.players) == 1:
            await game_over(game, _)
            return
    await game.events.action_end()


async def super_skip(game: "Game", _):
    game.remaining_turns = 0
    await skip(game, _)


async def self_attegg(game: "Game", _):
    await attegg_finish(game, game.current_player_id, turns=4)


async def bury(game: "Game", interaction: discord.Interaction):
    view = DefuseView(
        game,
        lambda: bury_finish(game),
        card=game.deck.pop(),
    )
    await interaction.respond(view=view, ephemeral=True)


async def bury_finish(game: "Game"):
    await game.send(view=TextView("buried", game.current_player_id))
    await game.events.turn_end()


async def share_future(game: "Game", interaction: discord.Interaction):
    view = AlterFutureView(
        game,
        lambda: share_future_finish(game),
        amount_of_cards=3,
    )
    await interaction.respond(view=view, ephemeral=True)


async def share_future_finish(game: "Game"):
    await game.send(
        view=ShareFutureView(
            game.deck.copy(),
            game.current_player_id,
            game.next_player_id,
        )
    )
    await game.events.action_end()


class ShareFutureView(discord.ui.View):
    def __init__(self, deck: list[str], *player_ids: int):
        super().__init__(timeout=None)
        self.player_ids = player_ids
        self.deck = deck
        self.add_item(
            discord.ui.TextDisplay(format_message("shared_future", *self.player_ids))
        )
        self.view_button = discord.ui.Button(
            label="View next cards", style=discord.ButtonStyle.primary, emoji="🔮"
        )
        self.view_button.callback = self.view_cards
        self.add_item(self.view_button)

    async def view_cards(self, interaction: discord.Interaction):
        if not interaction.user:
            return
        if interaction.user.id not in self.player_ids:
            await interaction.respond(
                view=TextView("not_allowed_to_view_cards"), ephemeral=True
            )
            return
        await show_next_cards(interaction, deck=self.deck, amount=3)


def setup(game: "Game"):
    game.deck += ["wisecracker"] * 2


PLAY_ACTIONS = {
    "wisecracker": wisecracker,
    "super_skip": super_skip,
    "self_attegg": self_attegg,
    "bury": bury,
    "share_future": share_future,
}

SETUP_ACTIONS = [
    setup,
]
