"""
Contains the views for the short interactions in the game, such as "Nope" and "Defuse".
"""

from collections.abc import Callable, Coroutine
import discord
from ..strings import CARDS, MESSAGES
from ..game_logic import ActionContext
from .base import BaseView


class NopeView(BaseView):
    """
    A view that handles the "Nope" button interactions in the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
        target_player_id (int): The ID of the target player.
        callback_action (function): The callback function to be called after the interaction.
        nopes (int): The count of "Nope" interactions.
    """

    def __init__(
        self,
        ctx: ActionContext,
        nope_callback_action: Callable[[], None] | None = None,
    ):
        """
        Initializes the NopeView with the given context, target player ID, and callback action.

        Args:
            ctx (ActionContext): The context of the current action.
            target_player_id (int): The ID of the target player.
            callback_action (function): The callback function to be called after the interaction.
        """
        super().__init__(ctx, timeout=10)
        self.nope_callback_action = nope_callback_action
        self.nopes = 0
        self.ctx.game.active_nope_views.append(self)

    async def on_timeout(self):
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    async def finish(self):
        self.on_timeout = super().on_timeout
        self.ctx.game.active_nope_views.remove(self)
        try:
            await super().on_timeout()
        finally:
            if self.nope_callback_action and self.nopes % 2:
                self.nope_callback_action()

    @discord.ui.button(label="Nope!", style=discord.ButtonStyle.red, emoji="🛑")
    async def nope_callback(
        self, _: discord.ui.Button, interaction: discord.Interaction
    ):
        """
        Handles the "Nope" button interaction.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if not interaction.user:
            return
        if (
            not self.nopes % 2
            and self.ctx.game.current_player_id == interaction.user.id
        ):
            await interaction.respond(MESSAGES["no_self_nope"], ephemeral=True)
            return
        if interaction.user.id not in self.ctx.game.players:
            await interaction.respond(MESSAGES["user_not_in_game"], ephemeral=True)
            return
        try:
            self.ctx.game.hands[interaction.user.id].remove("nope")
        except ValueError:
            await interaction.respond(MESSAGES["no_nope_cards"], ephemeral=True)
            return
        if not interaction.message:
            return
        self.nopes += 1
        new_message_content = "".join(
            (line.strip("~~") + "\n" if line.startswith("~~") else "~~" + line + "~~\n")
            for line in interaction.message.content.split("\n")
        ) + (
            MESSAGES["message_edit_on_nope"].format(interaction.user.id)
            if self.nopes % 2
            else MESSAGES["message_edit_on_yup"].format(interaction.user.id)
        )
        await interaction.edit(content=new_message_content, view=self)


class BlockingNopeView(NopeView):
    """
    A view that handles the "Nope" and "OK" button interactions in the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
        target_player_id (int): The ID of the target player.
        callback_action (function): The callback function to be called after the interaction.
        nopes (int): The count of "Nope" interactions.
    """

    def __init__(
        self,
        ctx: ActionContext,
        target_player_id: int,
        ok_callback_action: Callable[[discord.Interaction | None], Coroutine],
    ):
        """
        Initializes the NopeView with the given context, target player ID, and callback action.

        Args:
            ctx (ActionContext): The context of the current action.
            target_player_id (int): The ID of the target player.
            callback_action (function): The callback function to be called after the interaction.
        """
        super().__init__(ctx)
        self.ctx.game.awaiting_prompt = True
        self.target_player_id = target_player_id
        self.ok_callback_action = ok_callback_action

    async def on_timeout(self):
        """
        Handles the timeout event for the view.
        """
        try:
            await super().on_timeout()
        finally:
            if self.ctx.action_id == self.ctx.game.action_id:
                self.ctx.game.awaiting_prompt = False
                if not self.nopes % 2:
                    await self.ok_callback_action(None)

    @discord.ui.button(label="OK!", style=discord.ButtonStyle.green, emoji="✅")
    async def ok_callback(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the "OK" button interaction.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if not interaction.user:
            return
        if interaction.user.id != self.target_player_id:
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return
        if self.nopes % 2:
            await interaction.respond(MESSAGES["action_noped"], ephemeral=True)
            return
        self.on_timeout = super().on_timeout
        self.disable_all_items()
        await interaction.edit(view=self)
        self.ctx.game.awaiting_prompt = False
        await self.ok_callback_action(interaction)


class DefuseView(BaseView):
    """
    A view that allows players to interact with the defuse action in the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
        callback_action (callable): The function to execute after finishing the interaction.
        card_position (int): The position of the card in the deck.
    """

    def __init__(
        self,
        ctx: ActionContext,
        callback_action: Callable[[], Coroutine],
        card="eggsplode",
        prev_card=None,
    ):
        """
        Initializes the DefuseView with the given context and callback action.

        Args:
            ctx (ActionContext): The context of the current action.
            callback_action (callable): The function to execute after finishing the interaction.
        """
        super().__init__(ctx, timeout=10)
        self.ctx.game.awaiting_prompt = True
        self.callback_action = callback_action
        self.card = card
        self.prev_card = prev_card if prev_card else card
        self.card_position = 0
        self.generate_move_prompt()

    async def finish(self):
        """
        Inserts a card back into the deck and disables all interaction items.
        """
        self.ctx.game.deck.insert(self.card_position, self.card)
        self.ctx.game.awaiting_prompt = False
        await self.callback_action()

    async def on_timeout(self):
        """
        Handles the timeout event by finishing the interaction.
        """
        try:
            await super().on_timeout()
        finally:
            await self.finish()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the confirm button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        self.disable_all_items()
        await interaction.edit(view=self)
        self.on_timeout = super().on_timeout
        await self.finish()

    @discord.ui.button(label="Top", style=discord.ButtonStyle.blurple, emoji="⏫")
    async def top(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the top button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        self.card_position = len(self.ctx.game.deck)
        await self.update_view(interaction)

    @discord.ui.button(label="Move up", style=discord.ButtonStyle.blurple, emoji="⬆️")
    async def move_up(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the move up button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if self.card_position < len(self.ctx.game.deck):
            self.card_position += 1
        else:
            self.card_position = 0
        await self.update_view(interaction)

    @discord.ui.button(label="Move down", style=discord.ButtonStyle.blurple, emoji="⬇️")
    async def move_down(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the move down button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        if self.card_position > 0:
            self.card_position -= 1
        else:
            self.card_position = len(self.ctx.game.deck)
        await self.update_view(interaction)

    @discord.ui.button(label="Bottom", style=discord.ButtonStyle.blurple, emoji="⏬")
    async def bottom(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the bottom button click event.

        Args:
            _ (discord.ui.Button): The button that was clicked.
            interaction (discord.Interaction): The interaction object.
        """
        self.card_position = 0
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        """
        Updates the view with the current state of the defuse interaction.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.edit(
            content=self.generate_move_prompt(),
            view=self,
        )

    def generate_move_prompt(self):
        """
        Generates the prompt message for the defuse interaction.
        """
        return MESSAGES["move_prompt"].format(
            CARDS[self.prev_card]["title"],
            self.card_position,
            len(self.ctx.game.deck),
            "\n".join(
                MESSAGES["players_list_item"].format(player)
                for player in self.ctx.game.players
            ),
        )


class ChoosePlayerView(BaseView):
    """
    A view that allows the current player to choose another player from the game.

    Attributes:
        ctx (ActionContext): The context of the current action.
        callback_action (function): The callback function to execute after a player is selected.
        eligible_players (list): List of player IDs eligible for selection.
        user_select (discord.ui.Select): The select menu for choosing a player.
    """

    def __init__(self, ctx: ActionContext, callback_action: Callable[[int], Coroutine]):
        """
        Initializes the ChoosePlayerView with the given context and callback action.

        Args:
            ctx (ActionContext): The context of the current action.
            callback_action (function): The callback function to execute after a player is selected.
        """
        super().__init__(ctx, timeout=10)
        self.ctx.game.awaiting_prompt = True
        self.eligible_players = self.ctx.game.players.copy()
        self.eligible_players.remove(self.ctx.game.current_player_id)
        self.callback_action = callback_action
        self.user_select = None

    async def __aenter__(self):
        """
        Enters the context manager.

        Returns:
            ChoosePlayerView: The ChoosePlayerView object.
        """
        await self.create_user_selection()
        return self

    async def on_timeout(self):
        """
        Handles the timeout event for the view.
        """
        try:
            await super().on_timeout()
        finally:
            await self.callback_action(self.eligible_players[0])

    async def create_user_selection(self):
        """
        Creates the user selection menu with eligible players.
        """
        options = [
            discord.SelectOption(
                value=str(user_id),
                label=f"{user.display_name} ({len(self.ctx.game.hands[user_id])} cards)",
            )
            for user_id in self.eligible_players
            if (user := await self.ctx.app.get_or_fetch_user(user_id))
            and self.ctx.game.hands[user_id]
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
        """
        Handles the selection of a player from the user selection menu.

        Args:
            interaction (Interaction): The interaction object representing the user's action.
        """
        if not (interaction and self.user_select):
            return
        self.on_timeout = super().on_timeout
        self.disable_all_items()
        await interaction.edit(view=self)
        if not isinstance(self.user_select.values[0], str):
            raise TypeError("user_select.values[0] is not a str")
        await self.callback_action(int(self.user_select.values[0]))
