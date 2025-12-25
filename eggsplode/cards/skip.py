"""
Contains effects for cards that modify a turn's end.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.strings import format_message, tooltip
from eggsplode.ui import DefuseView, SelectionView, TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


async def skip(game: "Game", interaction: discord.Interaction):
    await game.send(
        view=TextView("skipped", game.current_player_id), interaction=interaction
    )
    await game.events.turn_end()


async def draw_from_bottom(game: "Game", interaction: discord.Interaction):
    _, hold = await game.draw_from(interaction, index=0)
    if hold:
        await game.events.turn_end()


async def reverse(game: "Game", interaction: discord.Interaction):
    game.reverse()
    await game.send(
        view=TextView("reversed", game.current_player_id), interaction=interaction
    )
    await game.events.turn_end()


async def super_skip(game: "Game", interaction: discord.Interaction):
    game.remaining_turns = 0
    await skip(game, interaction)


async def bury_finish(game: "Game", interaction: discord.Interaction):
    await game.send(
        view=TextView("buried", game.current_player_id), interaction=interaction
    )
    await game.events.turn_end()


async def bury(game: "Game", interaction: discord.Interaction):
    view = DefuseView(
        game,
        lambda: bury_finish(game, interaction),
        card=game.deck.pop(),
    )
    await interaction.respond(view=view, ephemeral=True)


class DigDeeperView(SelectionView):
    def __init__(self, game: "Game"):
        super().__init__(timeout=20)
        self.game = game
        self.next_card = game.deck[-1]
        self.keep_section = discord.ui.Section(
            discord.ui.TextDisplay(
                format_message(
                    "about_to_draw",
                    tooltip(self.next_card),
                )
            ),
            accessory=self.confirm_button,
        )
        self.confirm_button.emoji = "🤚"
        self.confirm_button.label = "Keep"
        self.confirm_button.style = discord.ButtonStyle.primary
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
            interaction = self.game.last_interaction
            if not interaction:
                raise ValueError("No last interaction set for the game.")
        _, hold = await self.game.draw_from(interaction)
        self.ignore_interactions()
        if hold:
            await self.game.events.turn_end()

    async def dig_deeper(self, interaction: discord.Interaction):
        self.ignore_interactions()
        self.disable_all_items()
        await interaction.edit(view=self)
        await self.game.send(
            view=TextView("dug_deeper", self.game.current_player_id),
            interaction=interaction,
        )
        _, hold = await self.game.draw_from(interaction, index=-2)
        if hold:
            await self.game.events.turn_end()


async def dig_deeper(game: "Game", interaction: discord.Interaction):
    if len(game.deck) < 2:
        await interaction.respond(
            view=TextView("not_enough_cards_to_dig_deeper"), ephemeral=True
        )
        game.current_player_hand.append("dig_deeper")
        await game.events.action_end()
        return
    game.last_interaction = interaction
    await interaction.respond(view=DigDeeperView(game), ephemeral=True)
