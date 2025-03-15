"""
Contains the PlayView and TurnView classes which handle the game actions in the Discord bot.
"""

import asyncio
from collections.abc import Callable, Coroutine
import random
import discord
from ..game_logic import ActionContext
from ..strings import CARDS, MESSAGES
from .short import ChoosePlayerView, DefuseView, BlockingNopeView, NopeView
from .base import BaseView


class TurnView(BaseView):
    """
    A view that manages the turn-based interactions in the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
        parent_interaction (discord.Interaction): The parent interaction.
        inactivity_count (int): The count of inactivity periods.
    """

    def __init__(
        self,
        ctx: ActionContext,
        parent_interaction: discord.Interaction,
        inactivity_count: int = 0,
    ):
        """
        Initializes the TurnView with the given context and parent interaction.

        Args:
            ctx (ActionContext): The context of the current action.
            parent_interaction (discord.Interaction): The parent interaction.
            inactivity_count (int, optional): The count of inactivity periods. Defaults to 0.
        """
        super().__init__(ctx, timeout=600)
        self.timer = 0
        self.inactivity_count = inactivity_count
        self.parent_interaction = parent_interaction

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Exits the context manager.

        Args:
            exc_type: The type of the exception that was raised
            exc_value: The instance of the exception that was raised
            traceback: The traceback of the exception
        """
        await self.action_timer()

    async def action_timer(self):
        """
        Starts the action timer and handles the timeout logic.
        """
        if self.timer < 0:
            return
        self.start_timer()
        while self.timer < int(self.ctx.game.config.get("turn_timeout", 60)):
            await asyncio.sleep(1)
            if self.timer < 0:
                return
            if not self.ctx.game.awaiting_prompt:
                self.timer += 1
        await self.on_action_timeout()

    def deactivate(self):
        """
        Stops the action timer and disables the view.
        """
        self.timer = -200
        self.ctx.action_id = -1

    def start_timer(self):
        """
        Starts the action timer.
        """
        self.timer = min(self.timer, 0)

    async def on_action_timeout(self):
        """
        Handles the logic when an action times out.
        """
        if not self.message:
            raise TypeError("message is None")
        self.deactivate()
        if self.inactivity_count > 5:
            await self.parent_interaction.respond(MESSAGES["game_timeout"])
            del self.ctx.games[self.ctx.game_id]
            return
        turn_player: int = self.ctx.game.current_player_id
        card: str = self.ctx.game.draw_card()
        response = MESSAGES["timeout"]
        match card:
            case "defuse":
                self.ctx.game.deck.insert(
                    random.randint(0, len(self.ctx.game.deck)), "eggsplode"
                )
                response += MESSAGES["defused"].format(turn_player)
            case "eggsplode":
                response += MESSAGES["eggsploded"].format(turn_player)
            case "gameover":
                await self.parent_interaction.respond(
                    MESSAGES["timeout"]
                    + MESSAGES["eggsploded"].format(turn_player)
                    + "\n"
                    + MESSAGES["game_over"].format(self.ctx.game.players[0])
                )
                del self.ctx.games[self.ctx.game_id]
                return
            case "radioeggtive":
                self.ctx.game.deck.insert(
                    random.randint(0, len(self.ctx.game.deck)), "radioeggtive_face_up"
                )
                response += MESSAGES["radioeggtive"].format(turn_player)
            case "radioeggtive_face_up":
                response += MESSAGES["radioeggtive_face_up"].format(turn_player)
            case _:
                response += MESSAGES["user_drew_card"].format(turn_player)
        response += "\n" + MESSAGES["next_turn"].format(self.ctx.game.current_player_id)
        async with TurnView(
            self.ctx.copy(),
            parent_interaction=self.parent_interaction,
            inactivity_count=self.inactivity_count + 1,
        ) as view:
            await self.parent_interaction.respond(response, view=view)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Checks if the interaction is valid for the current turn.

        Args:
            interaction (discord.Interaction): The interaction to check.

        Returns:
            bool: True if the interaction is valid, False otherwise.
        """
        if not interaction.user:
            return False
        if interaction.user.id != self.ctx.game.current_player_id:
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return False
        if self.timer <= 0:
            self.disable_all_items()
            await interaction.edit(view=self)
            await interaction.respond(MESSAGES["invalid_turn"], ephemeral=True)
            return False
        self.start_timer()
        return True

    @discord.ui.button(label="Play!", style=discord.ButtonStyle.blurple, emoji="🤚")
    async def play(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the play button interaction.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction that occurred.
        """
        if not interaction.user:
            return
        self.ctx.action_id = self.ctx.game.action_id
        async with PlayView(
            ActionContext(
                app=self.ctx.app,
                game_id=self.ctx.game_id,
                action_id=self.ctx.action_id,
            ),
            on_valid_interaction=lambda _: self.start_timer(),
            end_turn=self.end_turn,
            on_game_over=self.deactivate,
        ) as view:
            await interaction.respond(
                view.create_play_prompt_message(interaction.user.id),
                view=view,
                ephemeral=True,
            )

    async def end_turn(self, interaction: discord.Interaction):
        """
        Ends the current turn and starts the next one.

        Args:
            interaction (discord.Interaction): The interaction that ends the turn.
        """
        self.deactivate()
        async with TurnView(self.ctx.copy(), parent_interaction=interaction) as view:
            await interaction.respond(
                MESSAGES["next_turn"].format(self.ctx.game.current_player_id), view=view
            )


class PlayView(BaseView):
    """
    A view for handling the play actions in the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
        play_card_select (discord.ui.Select): The select menu for choosing a card to play.
        on_valid_interaction (function): Callback for valid interactions.
        end_turn (function): Callback to end the turn.
        on_game_over (function): Callback for when the game is over.
    """

    def __init__(
        self,
        ctx: ActionContext,
        *,
        on_valid_interaction: Callable[[discord.Interaction], None],
        end_turn: Callable[[discord.Interaction], Coroutine],
        on_game_over: Callable[[], None],
    ):
        """
        Initialize the PlayView.

        Args:
            ctx (ActionContext): The context of the current action.
            on_valid_interaction (function): Callback for valid interactions.
            end_turn (function): Callback to end the turn.
            on_game_over (function): Callback for when the game is over.
        """
        super().__init__(ctx)
        self.play_card_select = None
        self.on_valid_interaction = on_valid_interaction
        self.end_turn = end_turn
        self.on_game_over = on_game_over
        self.create_card_selection()

    def create_play_prompt_message(self, user_id: int) -> str:
        """
        Generates the default message to be displayed to the user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            str: The formatted message to be displayed.
        """
        radioeggtive_countdown = self.ctx.game.card_comes_in("radioeggtive_face_up")
        return MESSAGES["play_prompt"].format(
            self.ctx.game.cards_help(user_id, template=MESSAGES["hand_list"]),
            len(self.ctx.game.deck),
            self.ctx.game.deck.count("eggsplode"),
        ) + (
            "\n"
            + (
                ""
                if radioeggtive_countdown is None
                else (
                    MESSAGES["play_prompt_radioeggtive"].format(radioeggtive_countdown)
                    if radioeggtive_countdown > 1
                    else (
                        MESSAGES["play_prompt_radioeggtive_next"]
                        if radioeggtive_countdown == 1
                        else (MESSAGES["play_prompt_radioeggtive_now"])
                    )
                )
            )
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Check if the interaction is valid.

        Args:
            interaction (discord.Interaction): The interaction to check.

        Returns:
            bool: True if the interaction is valid, False otherwise.
        """
        if not interaction.user:
            raise TypeError("interaction.user is None")
        if self.ctx.game.awaiting_prompt:
            await interaction.respond(MESSAGES["awaiting_prompt"], ephemeral=True)
            return False
        if interaction.user.id != self.ctx.game.current_player_id:
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return False
        if self.ctx.action_id != self.ctx.game.action_id:
            self.disable_all_items()
            await interaction.edit(view=self)
            await interaction.respond(MESSAGES["invalid_turn"], ephemeral=True)
            return False
        self.ctx.game.action_id += 1
        self.ctx.action_id += 1
        for view in self.ctx.game.active_nope_views:
            view.finish()
        self.on_valid_interaction(interaction)
        return True

    def create_card_selection(self):
        """
        Create the card selection menu.
        """
        if self.play_card_select:
            self.remove_item(self.play_card_select)
        user_cards: dict = self.ctx.game.group_hand(
            self.ctx.game.current_player_id, usable_only=True
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
                    emoji=CARDS[card]["emoji"],
                )
                for card in user_cards
            ],
        )
        self.play_card_select.callback = lambda interaction: self.play_card(
            None, interaction
        )
        self.add_item(self.play_card_select)

    @discord.ui.button(label="Draw", style=discord.ButtonStyle.blurple, emoji="🤚")
    async def draw_callback(
        self, _: discord.ui.Button, interaction: discord.Interaction
    ):
        """
        Callback for the draw button.
        """
        await self.draw_card(interaction)

    async def draw_card(self, interaction: discord.Interaction, index=-1):
        """
        Draw a card from the deck.

        Args:
            interaction (discord.Interaction): The interaction that triggered the draw.
            index (int): The index of the card to draw.
        """
        if not interaction.user:
            return
        self.disable_all_items()
        await interaction.edit(view=self)
        card: str = self.ctx.game.draw_card(index)
        match card:
            case "defuse":
                async with DefuseView(
                    self.ctx.copy(),
                    lambda: self.defuse_finish(interaction),
                    card="eggsplode",
                ) as view:
                    await interaction.respond(
                        view.generate_move_prompt(),
                        view=view,
                        ephemeral=True,
                    )
                return
            case "eggsplode":
                await interaction.respond(
                    MESSAGES["eggsploded"].format(interaction.user.id)
                )
            case "gameover":
                await interaction.respond(
                    MESSAGES["eggsploded"].format(interaction.user.id)
                    + "\n"
                    + MESSAGES["game_over"].format(self.ctx.game.players[0])
                )
                self.on_game_over()
                del self.ctx.games[self.ctx.game_id]
                return
            case "radioeggtive":
                async with DefuseView(
                    self.ctx.copy(),
                    lambda: self.radioeggtive_finish(interaction),
                    card="radioeggtive_face_up",
                    prev_card="radioeggtive",
                ) as view:
                    await interaction.respond(
                        view.generate_move_prompt(),
                        view=view,
                        ephemeral=True,
                    )
                return
            case "radioeggtive_face_up":
                await interaction.respond(
                    MESSAGES["radioeggtive_face_up"].format(interaction.user.id)
                )
            case _:
                await interaction.respond(
                    MESSAGES["user_drew_card"].format(interaction.user.id)
                )
                await interaction.respond(
                    MESSAGES["you_drew_card"].format(
                        CARDS[card]["emoji"], CARDS[card]["title"]
                    ),
                    ephemeral=True,
                )
        await self.end_turn(interaction)

    async def play_card(self, _, interaction: discord.Interaction):
        """
        Play a selected card.

        Args:
            _ (discord.ui.Button): The button that triggered the play.
            interaction (discord.Interaction): The interaction that triggered the play.
        """
        if not (interaction.message and interaction.user and self.play_card_select):
            return
        selected = self.play_card_select.values[0]
        if not isinstance(selected, str):
            raise TypeError("selected is not a str")
        await interaction.edit(view=self)
        if CARDS[selected].get("combo", 0) == 1:
            await self.food_combo(interaction, selected)
        else:
            self.ctx.game.current_player_hand.remove(selected)
            await self.CARD_ACTIONS[selected](self, interaction)
        self.create_card_selection()
        await interaction.edit(
            content=self.create_play_prompt_message(interaction.user.id),
            view=self,
        )

    async def attegg(self, interaction: discord.Interaction):
        """
        Handle the 'attegg' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            return
        async with BlockingNopeView(
            ctx=self.ctx.copy(),
            target_player_id=self.ctx.game.next_player_id,
            ok_callback_action=lambda _: self.attegg_finish(interaction),
        ) as view:
            await interaction.respond(
                MESSAGES["before_attegg"].format(
                    interaction.user.id,
                    self.ctx.game.next_player_id,
                    self.ctx.game.draw_in_turn + 2,
                ),
                view=view,
            )

    async def skip(self, interaction: discord.Interaction):
        """
        Handle the 'skip' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            return
        target_player_id = (
            self.ctx.game.next_player_id
            if self.ctx.game.draw_in_turn == 0
            else interaction.user.id
        )
        async with BlockingNopeView(
            ctx=self.ctx.copy(),
            target_player_id=target_player_id,
            ok_callback_action=lambda _: self.skip_finish(interaction),
        ) as view:
            await interaction.respond(
                MESSAGES["before_skip"].format(interaction.user.id, target_player_id),
                view=view,
            )

    async def shuffle(self, interaction: discord.Interaction):
        """
        Handle the 'shuffle' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        prev_deck = self.ctx.game.deck.copy()
        random.shuffle(self.ctx.game.deck)
        if not interaction.user:
            return
        async with NopeView(
            ctx=self.ctx.copy(),
            nope_callback_action=lambda: self.undo_shuffle(prev_deck),
        ) as view:
            await interaction.respond(
                MESSAGES["shuffled"].format(interaction.user.id),
                view=view,
            )

    def undo_shuffle(self, prev_deck):
        """
        Undoes the 'shuffle' action.
        """
        self.ctx.game.deck = prev_deck

    async def predict(self, interaction: discord.Interaction):
        """
        Handle the 'predict' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            return
        next_cards = "\n".join(
            MESSAGES["bold_list_item"].format(
                CARDS[card]["emoji"], CARDS[card]["title"]
            )
            for card in self.ctx.game.deck[-1:-4:-1]
        )
        await interaction.respond(
            MESSAGES["predicted"].format(interaction.user.id),
        )
        await interaction.respond(
            "\n".join((MESSAGES["next_cards"], next_cards)),
            ephemeral=True,
        )

    async def food_combo(self, interaction: discord.Interaction, selected: str):
        """
        Handle the 'food combo' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
            selected (str): The selected card.
        """
        if not interaction.user:
            return
        if not self.ctx.game.any_player_has_cards():
            await interaction.respond(MESSAGES["no_players_have_cards"])
            return
        assert self.ctx.game.current_player_hand.count(selected) >= 2
        for _ in range(2):
            self.ctx.game.current_player_hand.remove(selected)
        async with ChoosePlayerView(
            self.ctx.copy(),
            lambda target_player_id: self.food_combo_begin(
                interaction, target_player_id, selected
            ),
        ) as view:
            await interaction.respond(
                MESSAGES["steal_prompt"], view=view, ephemeral=True
            )

    async def food_combo_begin(
        self, interaction: discord.Interaction, target_player_id: int, food_card: str
    ):
        """
        Begin the 'steal' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
            target_player_id (int): The ID of the target player.
            food_card (str): The food card used for stealing.
        """
        if not interaction.user:
            return
        async with BlockingNopeView(
            ctx=self.ctx.copy(),
            target_player_id=target_player_id,
            ok_callback_action=lambda target_interaction: self.food_combo_finish(
                interaction, target_interaction, target_player_id
            ),
        ) as view:
            await interaction.respond(
                MESSAGES["before_steal"].format(
                    CARDS[food_card]["emoji"], interaction.user.id, target_player_id
                ),
                view=view,
            )

    async def food_combo_finish(
        self,
        interaction: discord.Interaction,
        target_interaction: discord.Interaction | None,
        target_player_id: int,
    ):
        """
        Finalize the 'steal' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
            target_interaction (discord.Interaction | None): The interaction of the target player.
            target_player_id (int): The ID of the target player.
        """
        if not interaction.user:
            return
        target_hand = self.ctx.game.hands[target_player_id]
        if not target_hand:
            await interaction.respond(
                MESSAGES["no_cards_to_steal"].format(
                    self.ctx.game.current_player_id, target_player_id
                )
            )
            return
        stolen_card = random.choice(target_hand)
        self.ctx.game.hands[target_player_id].remove(stolen_card)
        self.ctx.game.current_player_hand.append(stolen_card)
        self.create_card_selection()
        await interaction.edit(
            content=self.create_play_prompt_message(interaction.user.id),
            view=self,
        )
        await interaction.respond(
            MESSAGES["stolen_card_public"].format(
                self.ctx.game.current_player_id, target_player_id
            )
        )
        await interaction.respond(
            MESSAGES["stolen_card_you"].format(
                CARDS[stolen_card]["emoji"], CARDS[stolen_card]["title"]
            ),
            ephemeral=True,
        )
        if target_interaction:
            await target_interaction.respond(
                MESSAGES["stolen_card_them"].format(
                    self.ctx.game.current_player_id,
                    CARDS[stolen_card]["emoji"],
                    CARDS[stolen_card]["title"],
                ),
                ephemeral=True,
            )

    async def defuse_finish(self, interaction: discord.Interaction):
        """
        Finalize the 'defuse' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            raise TypeError("interaction.user is None")
        await interaction.respond(MESSAGES["defused"].format(interaction.user.id))
        await self.end_turn(interaction)

    async def radioeggtive_finish(self, interaction: discord.Interaction):
        """
        Finalize the 'radioeggtive' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            raise TypeError("interaction.user is None")
        await interaction.respond(MESSAGES["radioeggtive"].format(interaction.user.id))
        await self.end_turn(interaction)

    async def attegg_finish(
        self, interaction: discord.Interaction, target_player_id=None
    ):
        """
        Finalize the 'attegg' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        target_player_id = target_player_id or self.ctx.game.next_player_id
        if not interaction.message:
            return
        self.disable_all_items()
        await interaction.edit(view=self)
        prev_to_draw_in_turn = self.ctx.game.draw_in_turn
        self.ctx.game.draw_in_turn = 0
        while self.ctx.game.current_player_id != target_player_id:
            self.ctx.game.next_turn()
        self.ctx.game.draw_in_turn = prev_to_draw_in_turn + 2
        await self.end_turn(interaction)

    async def skip_finish(self, interaction: discord.Interaction):
        """
        Finalize the 'skip' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.message:
            return
        self.disable_all_items()
        await interaction.edit(view=self)
        self.ctx.game.next_turn()
        await self.end_turn(interaction)

    async def draw_from_bottom(self, interaction: discord.Interaction):
        """
        Handle the 'draw from bottom' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            return
        target_player_id = (
            self.ctx.game.next_player_id
            if self.ctx.game.draw_in_turn == 0
            else interaction.user.id
        )
        async with BlockingNopeView(
            ctx=self.ctx.copy(),
            target_player_id=target_player_id,
            ok_callback_action=lambda _: self.draw_card(interaction, index=0),
        ) as view:
            await interaction.respond(
                MESSAGES["before_draw_from_bottom"].format(
                    interaction.user.id, target_player_id
                ),
                view=view,
            )

    async def targeted_attegg(self, interaction: discord.Interaction):
        """
        Handle the 'targeted attegg' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            return
        async with ChoosePlayerView(
            self.ctx.copy(),
            lambda target_player_id: self.targeted_attegg_begin(
                interaction, target_player_id
            ),
        ) as view:
            await interaction.respond(
                MESSAGES["targeted_attegg_prompt"], view=view, ephemeral=True
            )

    async def targeted_attegg_begin(
        self, interaction: discord.Interaction, target_player_id: int
    ):
        """
        Begin the 'targeted attegg' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            return
        async with BlockingNopeView(
            ctx=self.ctx.copy(),
            target_player_id=target_player_id,
            ok_callback_action=lambda _: self.attegg_finish(
                interaction, target_player_id
            ),
        ) as view:
            await interaction.respond(
                MESSAGES["before_targeted_attegg"].format(
                    interaction.user.id,
                    target_player_id,
                    self.ctx.game.draw_in_turn + 2,
                ),
                view=view,
            )

    CARD_ACTIONS = {
        "attegg": attegg,
        "skip": skip,
        "shuffle": shuffle,
        "predict": predict,
        "draw_from_bottom": draw_from_bottom,
        "targeted_attegg": targeted_attegg,
    }
