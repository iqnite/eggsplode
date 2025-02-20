"""
Contains the PlayView class for handling the play actions in the game.
"""

import random
from collections.abc import Callable, Coroutine
import discord
from strings import CARDS, MESSAGES
from game_logic import ActionContext
from .base_view import BaseView
from .nope_view import NopeView
from .choose_player_view import ChoosePlayerView
from .defuse_view import DefuseView


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

    async def __aenter__(self):
        """
        Enter the context manager.

        Returns:
            PlayView: The PlayView object.
        """
        self.create_card_selection()
        return self

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
        self.on_valid_interaction(interaction)
        return True

    def create_card_selection(self):
        """Create the card selection menu."""
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
        """Callback for the draw button."""
        await self.draw_card(interaction)

    async def draw_card(self, interaction: discord.Interaction):
        """
        Draw a card from the deck.

        Args:
            interaction (discord.Interaction): The interaction that triggered the draw.
        """
        if not interaction.user:
            return
        self.disable_all_items()
        await interaction.edit(view=self)
        card: str = self.ctx.game.draw_card(interaction.user.id)
        match card:
            case "defuse":
                await interaction.respond(
                    MESSAGES["defuse_prompt"].format(
                        0,
                        "\n".join(
                            MESSAGES["players_list_item"].format(player)
                            for player in self.ctx.game.players
                        ),
                    ),
                    view=DefuseView(
                        self.ctx.copy(),
                        lambda: self.finalize_defuse(interaction),
                    ),
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
                )
                await interaction.respond(
                    MESSAGES["game_over"].format(self.ctx.game.players[0])
                )
                self.on_game_over()
                del self.ctx.games[self.ctx.game_id]
                return
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
        self.remove_item(self.play_card_select)
        self.create_card_selection()
        await interaction.edit(view=self)

    async def attegg(self, interaction: discord.Interaction):
        """
        Handle the 'attegg' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            return
        await interaction.respond(
            MESSAGES["before_attegg"].format(
                interaction.user.id,
                self.ctx.game.next_player_id,
                self.ctx.game.draw_in_turn + 2,
            ),
            view=NopeView(
                ctx=self.ctx.copy(),
                target_player_id=self.ctx.game.next_player_id,
                callback_action=lambda _: self.finalize_attegg(interaction),
            ),
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
        await interaction.respond(
            MESSAGES["before_skip"].format(interaction.user.id, target_player_id),
            view=NopeView(
                ctx=self.ctx.copy(),
                target_player_id=target_player_id,
                callback_action=lambda _: self.finalize_skip(interaction),
            ),
        )

    async def shuffle(self, interaction: discord.Interaction):
        """
        Handle the 'shuffle' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        random.shuffle(self.ctx.game.deck)
        if not interaction.user:
            return
        await interaction.respond(
            MESSAGES["shuffled"].format(interaction.user.id),
        )

    async def predict(self, interaction: discord.Interaction):
        """
        Handle the 'predict' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            return
        next_cards = "".join(
            MESSAGES["next_cards_list"].format(
                CARDS[card]["emoji"], CARDS[card]["title"]
            )
            for card in self.ctx.game.deck[-1:-4:-1]
        )
        await interaction.respond(
            MESSAGES["predicted"].format(interaction.user.id),
        )
        await interaction.respond(
            MESSAGES["next_cards"].format(next_cards),
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
        else:
            self.ctx.game.current_player_hand.remove(selected)
            self.ctx.game.current_player_hand.remove(selected)
            await interaction.edit(
                content=self.default_message(interaction.user.id),
                view=self,
            )
            async with ChoosePlayerView(
                self.ctx.copy(),
                lambda target_player_id: self.begin_steal(
                    interaction, target_player_id, selected
                ),
            ) as view:
                await interaction.respond(
                    MESSAGES["steal_prompt"], view=view, ephemeral=True
                )

    async def begin_steal(
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
        await interaction.respond(
            MESSAGES["before_steal"].format(
                CARDS[food_card]["emoji"], interaction.user.id, target_player_id
            ),
            view=NopeView(
                ctx=self.ctx.copy(),
                target_player_id=target_player_id,
                callback_action=lambda target_interaction: self.finalize_steal(
                    interaction, target_interaction, target_player_id
                ),
            ),
        )

    async def finalize_steal(
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
        stolen_card = random.choice(target_hand)
        self.ctx.game.hands[target_player_id].remove(stolen_card)
        self.ctx.game.current_player_hand.append(stolen_card)
        self.create_card_selection()
        await interaction.edit(
            content=self.default_message(interaction.user.id),
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

    async def finalize_defuse(self, interaction: discord.Interaction):
        """
        Finalize the 'defuse' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.user:
            raise TypeError("interaction.user is None")
        await interaction.respond(MESSAGES["defused"].format(interaction.user.id))
        await self.end_turn(interaction)

    async def finalize_attegg(self, interaction: discord.Interaction):
        """
        Finalize the 'attegg' action.

        Args:
            interaction (discord.Interaction): The interaction that triggered the action.
        """
        if not interaction.message:
            return
        self.disable_all_items()
        await interaction.edit(view=self)
        prev_to_draw_in_turn = self.ctx.game.draw_in_turn
        self.ctx.game.draw_in_turn = 0
        self.ctx.game.next_turn()
        self.ctx.game.draw_in_turn = prev_to_draw_in_turn + 2
        await self.end_turn(interaction)

    async def finalize_skip(self, interaction: discord.Interaction):
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

    CARD_ACTIONS = {
        "attegg": attegg,
        "skip": skip,
        "shuffle": shuffle,
        "predict": predict,
    }
