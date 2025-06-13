"""
Contains the PlayView class, which is used to display the play interface for a game.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.strings import CARDS, MAX_COMPONENTS, format_message
from eggsplode.ui.base import TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


class PlayView(discord.ui.View):
    MAX_SECTIONS = (MAX_COMPONENTS - 3) // 3

    def __init__(self, game: "Game", user_id: int):
        super().__init__(timeout=60)
        self.game = game
        self.user_id = user_id
        self.action_id = game.action_id
        self.card_selects = []
        if self.playable:
            self.play_prompt = discord.ui.TextDisplay(format_message("play_prompt"))
            self.add_item(self.play_prompt)
        self.back_button: discord.ui.Button | None = None
        self.forward_button: discord.ui.Button | None = None
        self.page_number = 0
        self.update_sections()
        self.game.events.game_end += self.stop

    @property
    def playable(self) -> bool:
        return self.game.current_player_id == self.user_id and not self.game.paused

    @property
    def page_count(self) -> int:
        return (len(self.card_selects) + self.MAX_SECTIONS - 1) // self.MAX_SECTIONS

    def update_sections(self):
        self.card_selects = []
        user_cards = self.game.group_hand(self.user_id, usable_only=False)
        if not user_cards:
            return
        for card, count in user_cards.items():
            card_playable = (
                self.playable
                and CARDS[card].get("usable", False)
                and (CARDS[card].get("combo", 0) == 0 or count > 1)
            )
            section = discord.ui.Section(
                discord.ui.TextDisplay(
                    format_message(
                        "play_section",
                        CARDS[card]["emoji"],
                        CARDS[card]["title"],
                        CARDS[card]["description"],
                    )
                ),
                accessory=discord.ui.Button(
                    label=("Play " if card_playable else "") + f"({count}x)",
                    style=discord.ButtonStyle.secondary,
                    emoji=CARDS[card]["emoji"],
                    disabled=not card_playable,
                ),
            )

            def make_callback(card_value):
                return lambda interaction: self.play_card(card_value, interaction)

            assert isinstance(section.accessory, discord.ui.Button)
            section.accessory.callback = make_callback(card)
            self.card_selects.append(section)

        for item in self.children[1:]:
            self.remove_item(item)
        for item in self.card_selects[
            self.page_number
            * self.MAX_SECTIONS : (self.page_number + 1)
            * self.MAX_SECTIONS
        ]:
            self.add_item(item)

        if self.page_count > 1:
            if self.page_count > 2 or self.page_number == 0:
                self.forward_button = self.create_button(1)
            if self.page_count > 2 or self.page_number == 1:
                self.back_button = self.create_button(-1)

    def create_button(self, step: int) -> discord.ui.Button:
        to_page = self.page_number + step
        if to_page < 0:
            to_page = self.page_count - 1
        elif to_page >= self.page_count:
            to_page = 0

        async def button_callback(interaction: discord.Interaction):
            self.page_number = to_page
            self.update_sections()
            await interaction.edit(view=self)

        button = discord.ui.Button(
            label="Page " + str(to_page + 1),
            style=discord.ButtonStyle.secondary,
            emoji="◀️" if step < 0 else "▶️",
        )
        button.callback = button_callback
        self.add_item(button)
        return button

    async def play_card(self, card: str, interaction: discord.Interaction):
        if not self.playable:
            await interaction.edit(view=TextView("not_your_turn"), delete_after=5)
            return
        if self.action_id != self.game.action_id:
            await interaction.edit(
                view=TextView(format_message("invalid_turn")), delete_after=10
            )
            return
        self.game.action_id += 1
        self.action_id = self.game.action_id
        self.stop()
        await interaction.edit(view=self, delete_after=0)
        await self.game.play_callback(interaction, card)
