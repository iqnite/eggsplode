"""
Contains the views for the short interactions in the game, such as "Defuse".
"""

from typing import Callable, Coroutine, TYPE_CHECKING
import discord

from eggsplode.nope import NopeView
from eggsplode.strings import CARDS, MAX_COMPONENTS, get_message

if TYPE_CHECKING:
    from eggsplode.core import Game


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
        self.stop()
        await self.finish()


class ChoosePlayerView(discord.ui.View):
    def __init__(
        self,
        game: "Game",
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
        game: "Game",
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
            self.generate_move_prompt(), view=self, ephemeral=True
        )


class PlayView(discord.ui.View):
    MAX_SECTIONS = (MAX_COMPONENTS - 3) // 3

    def __init__(self, game: "Game", user_id: int):
        super().__init__(timeout=60)
        self.game = game
        self.user_id = user_id
        self.action_id = game.action_id
        self.card_selects = []
        if self.playable:
            self.play_prompt = discord.ui.TextDisplay(get_message("play_prompt"))
            self.add_item(self.play_prompt)
        self.back_button: discord.ui.Button | None = None
        self.forward_button: discord.ui.Button | None = None
        self.page_number = 0
        self.update_sections()

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
                    get_message("play_section").format(
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
            self.page_number : self.page_number + self.MAX_SECTIONS - 1
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
        if not interaction.user:
            raise TypeError("interaction.user is None")
        if not self.playable:
            await interaction.edit(
                view=discord.ui.View(
                    discord.ui.TextDisplay(get_message("not_your_turn"))
                ),
                delete_after=5,
            )
            return
        if self.action_id != self.game.action_id:
            await interaction.edit(
                view=discord.ui.View(
                    discord.ui.TextDisplay(get_message("invalid_turn"))
                ),
                delete_after=10,
            )
            return
        self.game.action_id += 1
        self.action_id = self.game.action_id
        self.stop()
        await interaction.edit(view=self, delete_after=0)
        await self.game.events.action_start()
        self.game.current_player_hand.remove(card)
        if CARDS[card].get("explicit", False):
            await self.game.play(interaction, card)
        else:
            view = NopeView(
                self.game,
                ok_callback_action=lambda _: self.game.play(interaction, card),
                message=get_message("play_card").format(
                    interaction.user.id,
                    CARDS[card]["emoji"],
                    CARDS[card]["title"],
                ),
            )
            await self.game.send(view=view)
