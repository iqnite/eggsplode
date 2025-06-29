"""
Contains card effects for the Radioeggtive expansion.
"""

from typing import Callable, Coroutine, TYPE_CHECKING
import random
import discord

from eggsplode.cards.base import attegg_finish, game_over
from eggsplode.strings import CARDS, format_message, replace_emojis
from eggsplode.ui import NopeView, ChoosePlayerView, DefuseView, SelectionView
from eggsplode.ui.base import TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


async def draw_from_bottom(game: "Game", interaction: discord.Interaction):
    _, hold = await game.draw_from(interaction, index=0)
    if hold:
        await game.events.turn_end()


def radioeggtive_warning(game: "Game") -> str:
    radioeggtive_countdown = game.card_comes_in("radioeggtive_face_up")
    return (
        format_message("play_prompt_radioeggtive_now")
        if radioeggtive_countdown == 0
        else ""
    )


async def reverse(game: "Game", _):
    game.reverse()
    await game.send(view=TextView("reversed", game.current_player_id))
    await game.events.turn_end()


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


async def targeted_attegg_begin(game: "Game", _, target_player_id: int):
    view = NopeView(
        game,
        message=format_message(
            "before_targeted_attegg",
            game.current_player_id,
            target_player_id,
            game.remaining_turns + 2,
        ),
        target_player_id=target_player_id,
        ok_callback_action=lambda _: attegg_finish(game, target_player_id),
    )
    await game.send(view=view)


async def targeted_attegg(game: "Game", interaction: discord.Interaction):
    view = ChoosePlayerView(
        game,
        lambda target_player_id: targeted_attegg_begin(
            game, interaction, target_player_id
        ),
    )
    await view.create_user_selection()
    await interaction.respond(view=view, ephemeral=True)


async def radioeggtive_finish(game: "Game"):
    await game.send(view=TextView("radioeggtive", game.current_player_id))
    await game.events.turn_end()


async def radioeggtive(
    game: "Game", interaction: discord.Interaction, timed_out: bool = False
):
    if timed_out:
        game.deck.insert(random.randint(0, len(game.deck)), "radioeggtive_face_up")
        await game.send(view=TextView("radioeggtive", game.current_player_id))
    else:
        view = DefuseView(
            game,
            lambda: radioeggtive_finish(game),
            card="radioeggtive_face_up",
            prev_card="radioeggtive",
        )
        await interaction.respond(view=view, ephemeral=True)


async def radioeggtive_face_up(game: "Game", interaction: discord.Interaction, _):
    prev_player = game.current_player_id
    game.remove_player(prev_player)
    game.remaining_turns = 0
    await game.send(view=TextView("radioeggtive_face_up", prev_player))
    if len(game.players) == 1:
        await game_over(game, interaction)
        return
    await game.events.turn_end()


def setup(game: "Game"):
    game.deck += ["radioeggtive"] * (
        "radioeggtive" in game.config.get("expansions", [])
    )


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

SETUP_ACTIONS = [
    setup,
]
