"""
Contains the views for the short interactions in the game, such as "Defuse".
"""

from datetime import datetime, timedelta
from typing import Callable, Coroutine
import discord

from eggsplode.nope import NopeContainer
from eggsplode.strings import CARDS, get_message, replace_emojis


class SelectionView(discord.ui.View):
    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    async def finish(self):
        pass

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, _, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        self.on_timeout = super().on_timeout
        self.stop()
        await self.finish()


class ChoosePlayerView(discord.ui.View):
    def __init__(
        self,
        game,
        callback_action: Callable[[int], Coroutine],
        condition: Callable[[int], bool] = lambda _: True,
    ):
        super().__init__(timeout=20)
        self.game = game
        self.eligible_players = [
            user_id for user_id in self.game.players if condition(user_id)
        ]
        self.callback_action = callback_action
        self.user_select = None

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.callback_action(self.eligible_players[0])

    async def create_user_selection(self):
        options = [
            discord.SelectOption(
                value=str(user_id),
                label=f"{user.display_name} ({len(self.game.hands[user_id])} cards)",
            )
            for user_id in self.eligible_players
            if (user := await self.game.app.get_or_fetch_user(user_id))
        ]
        self.user_select = discord.ui.Select(
            placeholder="Select another player",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user_select.callback = self.selection_callback
        self.add_item(self.user_select)

    async def selection_callback(self, interaction: discord.Interaction):
        if not (interaction and self.user_select):
            return
        self.on_timeout = super().on_timeout
        self.stop()
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        if not isinstance(self.user_select.values[0], str):
            raise TypeError("user_select.values[0] is not a str")
        await self.callback_action(int(self.user_select.values[0]))


class DefuseView(SelectionView):
    def __init__(
        self,
        game,
        callback_action: Callable[[], Coroutine],
        card="eggsplode",
        prev_card=None,
    ):
        super().__init__(timeout=30)
        self.game = game
        self.callback_action = callback_action
        self.card = card
        self.prev_card = prev_card if prev_card else card
        self.card_position = 0
        self.generate_move_prompt()

    async def finish(self):
        self.game.deck.insert(self.card_position, self.card)
        await self.callback_action()

    @discord.ui.button(label="Top", style=discord.ButtonStyle.blurple, emoji="⏫")
    async def top(self, _, interaction: discord.Interaction):
        self.card_position = len(self.game.deck)
        await self.update_view(interaction)

    @discord.ui.button(label="Move up", style=discord.ButtonStyle.blurple, emoji="⬆️")
    async def move_up(self, _, interaction: discord.Interaction):
        if self.card_position < len(self.game.deck):
            self.card_position += 1
        else:
            self.card_position = 0
        await self.update_view(interaction)

    @discord.ui.button(label="Move down", style=discord.ButtonStyle.blurple, emoji="⬇️")
    async def move_down(self, _, interaction: discord.Interaction):
        if self.card_position > 0:
            self.card_position -= 1
        else:
            self.card_position = len(self.game.deck)
        await self.update_view(interaction)

    @discord.ui.button(label="Bottom", style=discord.ButtonStyle.blurple, emoji="⏬")
    async def bottom(self, _, interaction: discord.Interaction):
        self.card_position = 0
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        await interaction.edit(
            content=self.generate_move_prompt(),
            view=self,
        )

    def generate_move_prompt(self):
        return get_message("move_prompt").format(
            CARDS[self.prev_card]["title"],
            self.card_position,
            len(self.game.deck),
            "\n".join(
                get_message("players_list_item").format(player)
                for player in self.game.players
            ),
        )

    async def send(self, interaction: discord.Interaction):
        await interaction.respond(
            self.generate_move_prompt(),
            view=self,
            ephemeral=True,
            delete_after=60,
        )


class PlayView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=60)
        self.game = game
        self.action_id = game.action_id
        self.play_card_select = None
        self.create_card_selection()

    async def update(self, interaction: discord.Interaction):
        if not interaction.user:
            return
        self.create_card_selection()
        await interaction.edit(
            content=self.create_play_prompt_message(interaction.user.id),
            view=self,
        )

    def create_play_prompt_message(self, user_id: int) -> str:
        return get_message("play_prompt").format(
            self.game.cards_help(user_id, template=get_message("hand_list"))
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user:
            raise TypeError("interaction.user is None")
        if interaction.user.id != self.game.current_player_id:
            await interaction.edit(
                content=get_message("not_your_turn"), view=None, delete_after=5
            )
            return False
        if self.action_id != self.game.action_id:
            await interaction.edit(
                content=get_message("invalid_turn"), view=None, delete_after=10
            )
            return False
        self.game.action_id += 1
        self.action_id = self.game.action_id
        await self.game.events.action_start()
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        return True

    def create_card_selection(self):
        if self.play_card_select:
            self.remove_item(self.play_card_select)
        user_cards: dict = self.game.group_hand(
            self.game.current_player_id, usable_only=True
        )
        if not user_cards:
            return
        self.play_card_select = discord.ui.Select(
            placeholder="Select a card to play",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    value=card,
                    label=f"{CARDS[card]['title']} ({user_cards[card]}x)",
                    description=CARDS[card]["description"],
                    emoji=replace_emojis(CARDS[card]["emoji"]),
                )
                for card in user_cards
            ],
        )
        self.play_card_select.callback = lambda interaction: self.play_card(
            None, interaction
        )
        self.add_item(self.play_card_select)

    async def play_card(self, _, interaction: discord.Interaction):
        if not (interaction.message and interaction.user and self.play_card_select):
            return
        selected = self.play_card_select.values[0]
        if not isinstance(selected, str):
            raise TypeError("selected is not a str")
        await self.game.events.action_start()
        if CARDS[selected].get("combo", 0) == 1:
            await self.game.play(interaction, "food_combo")
        else:
            self.game.current_player_hand.remove(selected)
            if CARDS[selected].get("explicit", False):
                await self.game.play(interaction, selected)
            else:
                view = NopeContainer(
                    self.game,
                    ok_callback_action=lambda _: self.game.play(interaction, selected),
                )
                await self.game.log(
                    get_message("play_card").format(
                        interaction.user.id,
                        CARDS[selected]["emoji"],
                        CARDS[selected]["title"],
                        int((datetime.now() + timedelta(seconds=10)).timestamp()),
                    ),
                )
