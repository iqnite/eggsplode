"""
Contains card effects for the Radioeggtive expansion.
"""

from typing import Callable, Coroutine, TYPE_CHECKING
import random
import discord

from eggsplode.cards.base import attegg_finish, game_over
from eggsplode.strings import CARDS, get_message, replace_emojis
from eggsplode.nope import ExplicitNopeView
from eggsplode.selections import ChoosePlayerView, DefuseView, SelectionView

if TYPE_CHECKING:
    from eggsplode.core import Game


async def draw_from_bottom(game: "Game", interaction: discord.Interaction):
    if not interaction.user:
        return
    await game.draw_from(interaction, index=0)
    await game.events.turn_end()


def radioeggtive_warning(game: "Game") -> str:
    radioeggtive_countdown = game.card_comes_in("radioeggtive_face_up")
    return (
        ""
        if radioeggtive_countdown is None
        else (
            get_message("play_prompt_radioeggtive").format(radioeggtive_countdown)
            if radioeggtive_countdown > 0
            else get_message("play_prompt_radioeggtive_now")
        )
    )


async def reverse(game: "Game", interaction: discord.Interaction):
    if not interaction.user:
        return
    game.reverse()
    await game.send(get_message("reversed").format(interaction.user.id))
    await game.events.turn_end()


async def alter_future_finish(game: "Game", interaction: discord.Interaction):
    if not interaction.user:
        return
    await game.send(get_message("altered_future").format(interaction.user.id))
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
        self.create_selections()

    def create_selections(self):
        card_options = [
            discord.SelectOption(
                value=f"{i}:{card}",
                label=CARDS[card]["title"],
                description=CARDS[card]["description"],
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
                placeholder=f"{i + 1}. card: {CARDS[self.game.deck[-i - 1]]['title']}",
                min_values=1,
                max_values=1,
                options=card_options,
            )
            select.callback = self.selection_callback
            self.selects.append(select)
            self.add_item(select)

    async def finish(self):
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
    if not interaction.user:
        return
    view = AlterFutureView(game, lambda: alter_future_finish(game, interaction), 3)
    await interaction.respond(view=view, ephemeral=True)


async def targeted_attegg_begin(
    game: "Game", interaction: discord.Interaction, target_player_id: int
):
    if not interaction.user:
        return
    view = ExplicitNopeView(
        game, target_player_id, lambda _: attegg_finish(game, target_player_id)
    )
    await game.send(
        get_message("before_targeted_attegg").format(
            interaction.user.id,
            target_player_id,
            game.draw_in_turn + 2,
        ),
        view=view,
    )


async def targeted_attegg(game: "Game", interaction: discord.Interaction):
    if not interaction.user:
        return
    view = ChoosePlayerView(
        game,
        lambda target_player_id: targeted_attegg_begin(
            game, interaction, target_player_id
        ),
    )
    await view.create_user_selection()
    await interaction.respond(
        get_message("targeted_attegg_prompt"),
        view=view,
        ephemeral=True,
        delete_after=30,
    )


async def radioeggtive_finish(game: "Game"):
    await game.send(get_message("radioeggtive").format(game.current_player_id))
    await game.events.turn_end()


async def radioeggtive(
    game: "Game", interaction: discord.Interaction, timed_out: bool = False
):
    if timed_out:
        game.deck.insert(random.randint(0, len(game.deck)), "radioeggtive_face_up")
        await game.send(get_message("radioeggtive").format(game.current_player_id))
    else:
        view = DefuseView(
            game,
            lambda: radioeggtive_finish(game),
            card="radioeggtive_face_up",
            prev_card="radioeggtive",
        )
        await view.send(interaction)


async def radioeggtive_face_up(game: "Game", interaction: discord.Interaction, _):
    prev_player = game.current_player_id
    game.remove_player(prev_player)
    game.draw_in_turn = 0
    await game.send(get_message("radioeggtive_face_up").format(prev_player))
    if len(game.players) == 1:
        await game_over(game, interaction)


PLAY_ACTIONS = {
    "draw_from_bottom": draw_from_bottom,
    "targeted_attegg": targeted_attegg,
    "alter_future": alter_future,
    "reverse": reverse,
}

DRAW_ACTIONS = {
    "radioeggtive": radioeggtive,
    "radioeggtive_face_up": radioeggtive_face_up,
}

TURN_WARNINGS = [
    radioeggtive_warning,
]
