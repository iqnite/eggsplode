"""
Contains the PlayView class, which is used to display the play interface for a game.
"""

from typing import TYPE_CHECKING

import discord

from eggsplode.strings import available_cards, format_message, replace_emojis
from eggsplode.ui.base import TextView
from eggsplode.ui.paginator import PaginatedView

if TYPE_CHECKING:
    from eggsplode.core import Game


class PlayView(PaginatedView):
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
        self.update_sections()
        self.game.events.game_end += self.ignore_interactions

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
            card_properties = available_cards[card]
            min_cards_others = card_properties.get("min_cards_others", 0)
            min_cards_self = card_properties.get("min_cards_self", 0)
            card_playable = (
                not self.game.paused
                and card_properties.get("usable", False)
                and (count >= card_properties.get("combo", 0))
                and (
                    card_properties.get("now", False)
                    or self.game.current_player_id == self.user_id
                )
                and (
                    (min_cards_others < 1)
                    or self.game.any_player_has_cards(
                        exclude_player_id=self.user_id, min_cards=min_cards_others
                    )
                )
                and (
                    (min_cards_self < 1)
                    or len(self.game.hands[self.user_id]) >= min_cards_self
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
                    emoji=replace_emojis(available_cards[card]["emoji"]),
                    disabled=not card_playable,
                ),
            )

            assert isinstance(section.accessory, discord.ui.Button)
            section.accessory.callback = self.make_callback(card)
            self.card_selects.append(section)
        self.update_pagination(self.card_selects)

    def make_callback(self, card_value):
        async def callback(interaction: discord.Interaction):
            await self.play_card(card_value, interaction)

        return callback

    async def play_card(self, card: str, interaction: discord.Interaction):
        if self.game.paused:
            await interaction.edit(view=TextView("not_your_turn"), delete_after=5)
            return
        if self.action_id != self.game.action_id:
            await interaction.edit(view=TextView("invalid_turn"), delete_after=10)
            return
        self.game.action_id += 1
        self.action_id = self.game.action_id
        self.ignore_interactions()
        await interaction.edit(view=self, delete_after=0)
        await self.game.play_callback(interaction, card)
