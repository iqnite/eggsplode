"""
Contains the views for the short interactions in the game, such as "Defuse".
"""

from typing import Callable, Coroutine, TYPE_CHECKING
import discord

from eggsplode.strings import format_message, tooltip, available_cards
from eggsplode.ui.base import BaseView

if TYPE_CHECKING:
    from eggsplode.core import Game


class SelectionView(BaseView):
    def __init__(self, timeout: int = 20):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.confirm_button = discord.ui.Button(
            label="Confirm", style=discord.ButtonStyle.green, emoji="✅"
        )
        self.confirm_button.callback = self.confirm

    async def on_timeout(self):
        if not self.is_ignoring_interactions:
            await self.finish()

    async def finish(self):
        self.ignore_interactions()

    async def confirm(self, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.edit(view=self)
        if not self.is_ignoring_interactions:
            await self.finish()


class ChoosePlayerView(BaseView):
    def __init__(
        self,
        game: "Game",
        callback_action: Callable[[int], Coroutine],
        condition: Callable[[int], bool] = lambda _: True,
    ):
        super().__init__(timeout=20, disable_on_timeout=True)
        self.game = game
        self.eligible_players = [
            user_id for user_id in self.game.players if condition(user_id)
        ]
        self.callback_action = callback_action
        self.user_select = None
        self.action_row = None
        self.game.events.game_end += self.ignore_interactions

    async def on_timeout(self):
        if not self.is_ignoring_interactions:
            self.ignore_interactions()
            await self.callback_action(self.eligible_players[0])

    async def skip_if_single_option(self) -> bool:
        if len(self.eligible_players) == 1:
            await self.callback_action(self.eligible_players[0])
            return True
        return False

    async def create_user_selection(self):
        options = [
            discord.SelectOption(
                value=str(user_id),
                label=f"{user.display_name} ({len(self.game.hands[user_id])} cards)",
            )
            for user_id in self.eligible_players
            if (user := await self.game.app.get_or_fetch(discord.User, user_id))
        ]
        self.user_select = discord.ui.Select(
            placeholder="Select a player",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user_select.callback = self.selection_callback
        self.action_row = discord.ui.ActionRow(self.user_select)
        self.add_item(self.action_row)

    async def selection_callback(self, interaction: discord.Interaction):
        if not (interaction and self.user_select):
            return
        self.ignore_interactions()
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        if not isinstance(self.user_select.values[0], str):
            raise TypeError("user_select.values[0] is not a str")
        await self.callback_action(int(self.user_select.values[0]))


class ChooseCardView(BaseView):
    def __init__(
        self,
        game: "Game",
        target_player_id: int,
        callback_action: Callable[[list[str]], Coroutine],
        text: str | None = None,
        min_cards: int = 1,
        max_cards: int = 1,
    ):
        super().__init__(timeout=20, disable_on_timeout=True)
        self.game = game
        self.target_player_id = target_player_id
        self.target_hand: dict[str, int] = self.game.group_hand(target_player_id)
        self.callback_action = callback_action
        self.card_select = None
        self.action_row = None
        self.text = text
        self.min_cards = min_cards
        self.max_cards = max_cards
        self.game.events.game_end += self.ignore_interactions
        self.target_hand_size = sum(self.target_hand.values())
        if self.min_cards > self.target_hand_size:
            raise ValueError("Player does not have enough cards to select")

    def _auto_select_cards(self) -> list[str]:
        selected_cards: list[str] = []
        for card, count in sorted(
            self.target_hand.items(), key=lambda item: (-item[1], item[0])
        ):
            remaining = self.min_cards - len(selected_cards)
            if remaining <= 0:
                break
            selected_cards.extend([card] * min(count, remaining))
        if len(selected_cards) < self.min_cards:
            raise ValueError("Player does not have enough cards to select")
        return selected_cards

    async def on_timeout(self):
        if not self.is_ignoring_interactions:
            self.ignore_interactions()
            await self.callback_action(self._auto_select_cards())

    async def skip_if_single_option(self) -> bool:
        if self.target_hand_size == self.min_cards:
            await self.callback_action(self._auto_select_cards())
            return True
        return False

    async def create_user_selection(self):
        options = [
            discord.SelectOption(
                value=card,
                label=format_message("card_with_count", card, count),
                emoji=available_cards[card].get("emoji", None),
                description=available_cards[card].get("description", None),
            )
            for card, count in self.target_hand.items()
        ]
        self.card_select = discord.ui.Select(
            placeholder=self.text or "Select a card",
            min_values=self.min_cards,
            max_values=min(self.max_cards, self.target_hand_size),
            options=options,
        )
        self.card_select.callback = self.selection_callback
        self.action_row = discord.ui.ActionRow(self.card_select)
        self.add_item(self.action_row)

    async def selection_callback(self, interaction: discord.Interaction):
        if not (interaction and self.card_select):
            return
        self.ignore_interactions()
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        await self.callback_action(self.card_select.values)


class DefuseView(SelectionView):
    def __init__(
        self,
        game: "Game",
        callback_action: Callable[[], Coroutine],
        card="eggsplode",
        prev_card=None,
    ):
        super().__init__(timeout=20)
        self.game = game
        self.callback_action = callback_action
        self.card = card
        self.prev_card = prev_card if prev_card else card
        self.card_position = 0
        self.move_prompt_display = discord.ui.TextDisplay(self.move_prompt)
        self.add_item(self.move_prompt_display)
        self.top_button = discord.ui.Button(label="Top", emoji="⏫")
        self.top_button.callback = self.top
        self.move_up_button = discord.ui.Button(label="Move up", emoji="🔼")
        self.move_up_button.callback = self.move_up
        self.move_down_button = discord.ui.Button(label="Move down", emoji="🔽")
        self.move_down_button.callback = self.move_down
        self.bottom_button = discord.ui.Button(label="Bottom", emoji="⏬")
        self.bottom_button.callback = self.bottom
        self.move_action_row = discord.ui.ActionRow(
            self.top_button,
            self.move_up_button,
            self.move_down_button,
            self.bottom_button,
            self.confirm_button,
        )
        self.add_item(self.move_action_row)
        self.game.events.game_end += self.ignore_interactions

    async def skip_if_deck_empty(self) -> bool:
        if len(self.game.deck) == 0:
            await self.finish()
            return True
        return False

    async def finish(self):
        await super().finish()
        self.game.deck.insert(self.card_position, self.card)
        await self.callback_action()

    async def top(self, interaction: discord.Interaction):
        self.card_position = len(self.game.deck)
        await self.update_view(interaction)

    async def move_up(self, interaction: discord.Interaction):
        if self.card_position < len(self.game.deck):
            self.card_position += 1
        else:
            self.card_position = 0
        await self.update_view(interaction)

    async def move_down(self, interaction: discord.Interaction):
        if self.card_position > 0:
            self.card_position -= 1
        else:
            self.card_position = len(self.game.deck)
        await self.update_view(interaction)

    async def bottom(self, interaction: discord.Interaction):
        self.card_position = 0
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        self.move_prompt_display.content = self.move_prompt
        await interaction.edit(view=self)

    @property
    def move_prompt(self) -> str:
        return format_message(
            "move_prompt",
            tooltip(self.prev_card),
            self.card_position,
            len(self.game.deck),
            "\n".join(
                format_message("players_list_item", player)
                for player in self.game.players
            ),
        )
