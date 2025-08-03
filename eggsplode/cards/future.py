"""
Contains effects for cards that view or alter the next cards.
"""

from typing import TYPE_CHECKING, Callable, Coroutine
import discord
from eggsplode.strings import CARDS, format_message, replace_emojis, tooltip
from eggsplode.ui import SelectionView, TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


async def see_future(game: "Game", interaction: discord.Interaction):
    await game.send(view=TextView("predicted", game.current_player_id))
    await show_next_cards(interaction, game.deck)
    await game.events.action_end()


async def show_next_cards(
    interaction: discord.Interaction,
    deck: list[str],
    amount: int = 3,
):
    next_cards = "\n".join(
        format_message(
            "list_item_2", replace_emojis(CARDS[card]["emoji"]), tooltip(card)
        )
        for card in deck[-1 : -amount - 1 : -1]
    )
    await interaction.respond(
        view=TextView(
            "\n".join((format_message("next_cards"), next_cards)), verbatim=True
        ),
        ephemeral=True,
    )


async def alter_future_finish(game: "Game", _):
    await game.send(view=TextView("altered_future", game.current_player_id))
    await game.events.action_end()


class AlterFutureView(SelectionView):
    def __init__(
        self,
        game: "Game",
        callback_action: Callable[[], Coroutine],
        amount_of_cards: int,
    ):
        super().__init__(timeout=20)
        self.game = game
        self.amount_of_cards = min(amount_of_cards, len(self.game.deck))
        self.callback_action = callback_action
        self.selects: list[discord.ui.Select] = []
        self.add_item(self.confirm_button)
        self.create_selections()

    def create_selections(self):
        card_options = [
            discord.SelectOption(
                value=f"{i}:{card}",
                label=CARDS[card]["title"],
                description=CARDS[card]["description"][:99],
                emoji=replace_emojis(CARDS[card]["emoji"]),
            )
            for i, card in enumerate(
                self.game.deck[-1 : -self.amount_of_cards - 1 : -1]
            )
        ]
        for select in self.selects:
            self.remove_item(select)
        self.selects = []
        for i in range(self.amount_of_cards):
            select = discord.ui.Select(
                placeholder=format_message(
                    "alter_future_placeholder",
                    i + 1,
                    CARDS[self.game.deck[-i - 1]]["title"],
                ),
                min_values=1,
                max_values=1,
                options=card_options,
            )
            select.callback = self.selection_callback
            self.selects.append(select)
            self.add_item(select)

    async def finish(self, interaction=None):
        await self.callback_action()

    async def selection_callback(self, interaction: discord.Interaction):
        if not interaction:
            return
        for i, select in enumerate(self.selects):
            if select.values is None:
                continue
            if not isinstance(select.values[0], str):
                raise TypeError("select.values[0] is not a str")
            prev_card_position = -i - 1
            new_card_position = -int(select.values[0].partition(":")[0]) - 1
            prev_card = self.game.deck[prev_card_position]
            new_card = select.values[0].partition(":")[2]
            self.game.deck[prev_card_position] = new_card
            self.game.deck[new_card_position] = prev_card
            break
        self.create_selections()
        await interaction.edit(view=self)


async def alter_future(game: "Game", interaction: discord.Interaction):
    view = AlterFutureView(game, lambda: alter_future_finish(game, interaction), 3)
    await interaction.respond(view=view, ephemeral=True)


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


async def share_future_finish(game: "Game"):
    await game.send(
        view=ShareFutureView(
            game.deck.copy(),
            game.current_player_id,
            game.next_player_id,
        )
    )
    await game.events.action_end()


async def share_future(game: "Game", interaction: discord.Interaction):
    view = AlterFutureView(
        game,
        lambda: share_future_finish(game),
        amount_of_cards=3,
    )
    await interaction.respond(view=view, ephemeral=True)
