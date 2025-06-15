"""
Contains card effects for the Wise-Cracker expansion.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.cards.base import game_over, show_next_cards, skip, attegg_finish
from eggsplode.cards.radioeggtive import AlterFutureView
from eggsplode.ui import ChoosePlayerView, DefuseView, TextView, SelectionView
from eggsplode.strings import CARDS, format_message, replace_emojis, tooltip

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
    current_player_id = game.current_player_id
    if "defuse" in game.hands[target_player_id]:
        game.hands[target_player_id].remove("defuse")
        await game.send(
            view=TextView(
                "wisecracker_defused", current_player_id, target_player_id
            ),
        )
    else:
        await game.send(
            view=TextView(
                "wisecracker_eggsploded", current_player_id, target_player_id
            ),
        )
        del game.players[game.players.index(target_player_id)]
        del game.hands[target_player_id]
        game.current_player = game.players.index(current_player_id)
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
            label="View next cards", style=discord.ButtonStyle.primary, emoji="👀"
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


async def dig_deeper(game: "Game", interaction: discord.Interaction):
    if len(game.deck) < 2:
        await interaction.respond(
            view=TextView("not_enough_cards_to_dig_deeper"), ephemeral=True
        )
        game.current_player_hand.append("dig_deeper")
        return
    game.anchor_interaction = interaction
    await interaction.respond(view=DigDeeperView(game), ephemeral=True)


class DigDeeperView(SelectionView):
    def __init__(self, game: "Game"):
        super().__init__(timeout=20)
        self.game = game
        self.next_card = game.deck[-1]
        self.keep_section = discord.ui.Section(
            discord.ui.TextDisplay(
                format_message(
                    "next_card",
                    replace_emojis(CARDS[self.next_card]["emoji"]),
                    tooltip(self.next_card),
                )
            ),
            accessory=self.confirm_button,
        )
        self.confirm_button.label = "Keep"
        self.add_item(self.keep_section)
        self.dig_deeper_button = discord.ui.Button(
            label="Draw next", style=discord.ButtonStyle.secondary, emoji="⛏️"
        )
        self.dig_deeper_button.callback = self.dig_deeper
        self.dig_deeper_section = discord.ui.Section(
            discord.ui.TextDisplay(format_message("dig_deeper_prompt")),
            accessory=self.dig_deeper_button,
        )
        self.add_item(self.dig_deeper_section)

    async def finish(self, interaction: discord.Interaction | None = None):
        if not interaction:
            interaction = self.game.anchor_interaction
            if not interaction:
                raise ValueError("No anchor interaction set for the game.")
        _, hold = await self.game.draw_from(interaction)
        self.stop()
        if hold:
            await self.game.events.turn_end()

    async def dig_deeper(self, interaction: discord.Interaction):
        self.stop()
        self.disable_all_items()
        await interaction.edit(view=self)
        await self.game.send(view=TextView("dug_deeper", self.game.current_player_id))
        _, hold = await self.game.draw_from(interaction, index=-2)
        if hold:
            await self.game.events.turn_end()


def setup(game: "Game"):
    game.deck += ["wisecracker"] * 2


PLAY_ACTIONS = {
    "wisecracker": wisecracker,
    "super_skip": super_skip,
    "self_attegg": self_attegg,
    "bury": bury,
    "share_future": share_future,
    "dig_deeper": dig_deeper,
}

SETUP_ACTIONS = [
    setup,
]
