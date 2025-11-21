"""
Contains the PlayView class, which is used to display the play interface for a game.
"""

from typing import TYPE_CHECKING
import discord
from eggsplode.strings import available_cards, MAX_COMPONENTS, format_message
from eggsplode.ui.base import TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


class PlayView(discord.ui.DesignerView):
    MAX_SECTIONS = (MAX_COMPONENTS - 5) // 3

    def __init__(self, game: "Game", user_id: int):
        super().__init__(timeout=60)
        self.game = game
        self.user_id = user_id
        self.action_id = game.action_id
        self.card_selects = []
        self.play_prompt = discord.ui.TextDisplay(
            format_message(
                "user_has_no_cards"
                if not self.game.hands[self.user_id]
                else "your_cards" if not self.playable else "play_prompt"
            )
        )
        self.add_item(self.play_prompt)
        self.card_container = discord.ui.Container()
        self.back_forward_row = discord.ui.ActionRow()
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
                not self.game.paused
                and available_cards[card].get("usable", False)
                and (available_cards[card].get("combo", 0) == 0 or count > 1)
                and (
                    available_cards[card].get("now", False)
                    or self.game.current_player_id == self.user_id
                )
            )
            section = discord.ui.Section(
                discord.ui.TextDisplay(
                    format_message(
                        "play_section",
                        available_cards[card]["emoji"],
                        available_cards[card]["title"],
                        available_cards[card]["description"],
                    )
                ),
                accessory=discord.ui.Button(
                    label=("Play " if card_playable else "") + f"({count}x)",
                    style=discord.ButtonStyle.secondary,
                    emoji=available_cards[card]["emoji"],
                    disabled=not card_playable,
                ),
            )

            assert isinstance(section.accessory, discord.ui.Button)
            section.accessory.callback = self.make_callback(card)
            self.card_selects.append(section)

        if self.card_container in self.children:
            self.remove_item(self.card_container)
        self.card_container = discord.ui.Container()
        for item in self.card_selects[
            self.page_number
            * self.MAX_SECTIONS : (self.page_number + 1)
            * self.MAX_SECTIONS
        ]:
            self.card_container.add_item(item)

        if len(self.card_selects) > 0:
            self.add_item(self.card_container)

        if self.back_forward_row in self.children:
            self.remove_item(self.back_forward_row)
        self.back_forward_row = discord.ui.ActionRow()
        if self.page_count > 1:
            if self.page_count > 2 or self.page_number == 0:
                self.forward_button = self.create_button(1)
            if self.page_count > 2 or self.page_number == 1:
                self.back_button = self.create_button(-1)
            if self.back_forward_row not in self.children:
                self.add_item(self.back_forward_row)

    def make_callback(self, card_value):
        async def callback(interaction: discord.Interaction):
            await self.play_card(card_value, interaction)

        return callback

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
        self.back_forward_row.add_item(button)
        return button

    async def play_card(self, card: str, interaction: discord.Interaction):
        if self.game.paused:
            await interaction.edit(view=TextView("not_your_turn"), delete_after=5)
            return
        if self.action_id != self.game.action_id:
            await interaction.edit(view=TextView("invalid_turn"), delete_after=10)
            return
        self.game.action_id += 1
        self.action_id = self.game.action_id
        self.stop()
        await interaction.edit(view=self, delete_after=0)
        await self.game.play_callback(interaction, card)
