"""
Contains the BaseView class which is used to create a Discord UI view for the game.
"""

import discord

from .cards.radioeggtive import radioeggtive_warning
from .game_logic import Game
from .strings import get_message


class BaseView(discord.ui.View):
    def __init__(self, game: Game, timeout=None):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.game = game
        self.ephemeral_full_log = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        await interaction.response.defer(invisible=True)
        return True

    @discord.ui.button(
        label="Full game log", style=discord.ButtonStyle.gray, emoji="📜", row=4
    )
    async def full_log(self, _, interaction: discord.Interaction):
        view = UpDownView(
            lambda interaction, index: None,  # Placeholder lambda
            len(self.game.log.pages),
        )
        view.callback = lambda interaction, index: interaction.edit(
            content=self.get_page_with_count(index),
            view=view,
        )
        await interaction.respond(
            self.get_page_with_count(len(self.game.log.pages) - 1),
            view=view,
            ephemeral=self.ephemeral_full_log,
        )

    def get_page_with_count(self, index):
        return self.game.log.pages[index] + get_message("page_count").format(
            index + 1, len(self.game.log.pages)
        )

    def create_turn_prompt_message(self) -> str:
        return (
            get_message("next_turn").format(
                self.game.current_player_id,
            )
            + "\n"
            + get_message("turn_warning").format(
                len(self.game.deck),
                self.game.deck.count("eggsplode"),
            )
            + ("\n" + radioeggtive_warning(self.game))
        )


class UpDownView(discord.ui.View):
    def __init__(self, callback, amount):
        super().__init__(timeout=60, disable_on_timeout=True)
        self.callback = callback
        self.amount = amount
        self.index = amount - 1

    @discord.ui.button(label="⬆️", style=discord.ButtonStyle.grey)
    async def up(self, _, interaction: discord.Interaction):
        if self.index > 0:
            self.index -= 1
        else:
            self.index = self.amount - 1
        await self.callback(interaction, self.index)

    @discord.ui.button(label="⬇️", style=discord.ButtonStyle.grey)
    async def down(self, _, interaction: discord.Interaction):
        if self.index < self.amount - 1:
            self.index += 1
        else:
            self.index = 0
        await self.callback(interaction, self.index)
