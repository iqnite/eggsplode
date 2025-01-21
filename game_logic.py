"""
Game logic for Eggsplode.
"""

import json
import random
import discord
from discord.ext import commands

with open("cardtypes.json", encoding="utf-8") as f:
    CARDS = json.load(f)
with open("messages.json", encoding="utf-8") as f:
    MESSAGES = json.load(f)


class ActionContext:  # pylint: disable=too-few-public-methods
    """
    Represents the context of an action.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        app,
        game_id,
        action_id=None,
        parent_view=None,
        parent_interaction=None,
    ):
        self.app: Eggsplode = app
        self.games: dict[int, Game] = self.app.games
        self.parent_view: discord.ui.View | TurnView | PlayView | NopeView | None = (
            parent_view
        )
        self.parent_interaction: discord.Interaction | None = parent_interaction
        self.game_id: int = game_id
        self.game: Game = self.games[game_id]
        if action_id:
            self.action_id: int = action_id
        elif self.game:
            self.action_id: int = self.game.action_id

    def copy(self, **kwargs):
        """
        Copies the context with the given changes.
        """
        return ActionContext(
            app=kwargs.get("app", self.app),
            parent_view=kwargs.get("parent_view", self.parent_view),
            parent_interaction=kwargs.get(
                "parent_interaction", self.parent_interaction
            ),
            game_id=kwargs.get("game_id", self.game_id),
            action_id=kwargs.get("action_id", self.action_id),
        )


class Game:
    """
    Represents a game of Eggsplode.

    Attributes:
        players (list[int]): List of player IDs.
        hands (dict[int, list[str]]): Dictionary mapping player IDs to their hands.
        deck (list[str]): List of cards in the deck.
        current_player (int): Index of the current player.
        action_id (int): ID of the current action.
        atteggs (int): Number of atteggs.
    """

    def __init__(self, *players):
        """
        Initializes a new game with the given players.

        Args:
            players (int): Player IDs.
        """
        self.players: list[int] = list(players)
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.current_player: int = 0
        self.action_id: int = 0
        self.atteggs: int = 0
        self.awaiting_prompt: bool = False

    def start(self):
        """
        Starts the game by shuffling the deck and dealing cards to players.
        """
        for card in CARDS:
            self.deck.extend([card] * CARDS[card]["count"])
        self.deck = self.deck * (1 + len(self.players) // 5)
        random.shuffle(self.deck)
        for _ in range(7):
            for player in self.players:
                assert isinstance(player, int), "Player must be an integer"
                if player not in self.hands:
                    self.hands[player] = []
                self.hands[player].append(self.deck.pop())
        for player in self.players:
            assert isinstance(player, int), "Player must be an integer"
            self.hands[player].append("defuse")
        for _ in range(len(self.players) - 1):
            self.deck.append("eggsplode")
        random.shuffle(self.deck)

    @property
    def current_player_id(self):
        """
        Returns the ID of the current player.

        Returns:
            int: Current player ID.
        """
        return self.players[self.current_player]

    @property
    def next_player(self):
        """
        Returns the index of the next player.

        Returns:
            int: Index of the next player.
        """
        return (
            0
            if self.current_player == len(self.players) - 1
            else self.current_player + 1
        )

    @property
    def next_player_id(self):
        """
        Returns the ID of the next player.

        Returns:
            int: Next player ID.
        """
        return self.players[self.next_player]

    def next_turn(self):
        """
        Advances the game to the next turn.
        """
        if self.atteggs > 0:
            self.atteggs -= 1
            return
        self.current_player = self.next_player

    def group_hand(self, user_id, usable_only=False):
        """
        Groups the cards in a player's hand.

        Args:
            user_id (int): Player ID.
            usable_only (bool): Whether to include only usable cards.

        Returns:
            list[tuple[str, int]]: List of tuples containing card names and counts.
        """
        player_cards = self.hands[user_id]
        result_cards = []
        result_counts = []
        for card in player_cards:
            if usable_only:
                if not CARDS[card]["usable"]:
                    continue
                if CARDS[card].get("combo", 0) > 0 and player_cards.count(card) < 2:
                    continue
            if card in result_cards:
                continue
            result_cards.append(card)
            result_counts.append(player_cards.count(card))
        return list(zip(result_cards, result_counts))

    def draw_card(self, user_id):
        """
        Draws a card for the given player.

        Args:
            user_id (int): Player ID.

        Returns:
            str: The drawn card.
        """
        card = self.deck.pop()
        if card == "eggsplode":
            if "defuse" in self.hands[user_id]:
                self.hands[user_id].remove("defuse")
                self.deck.insert(random.randint(0, len(self.deck)), "eggsplode")
                self.next_turn()
                return "defuse"
            self.remove_player(user_id)
            if len(self.players) == 1:
                return "gameover"
            return "eggsplode"
        self.hands[user_id].append(card)
        self.next_turn()
        return card

    def remove_player(self, user_id):
        """
        Removes a player from the game.

        Args:
            user_id (int): Player ID.
        """
        del self.players[self.players.index(user_id)]
        del self.hands[user_id]
        self.current_player -= 1
        self.atteggs = 0
        self.next_turn()


class Eggsplode(commands.Bot):  # pylint: disable=too-many-ancestors
    """
    Represents the Eggsplode bot.

    Attributes:
        admin_maintenance (bool): Whether the bot is in maintenance mode.
        games (dict[int, Game]): Dictionary of active games.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Eggsplode bot.

        Args:
            kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.admin_maintenance: bool = False
        self.games: dict[int, Game] = {}


class TurnView(discord.ui.View):
    """
    Represents the view for a player's turn.

    Attributes:
        app (Eggsplode): The Eggsplode bot instance.
        game_id (int): The game ID.
        game (Game): The game instance.
        action_id (int): The action ID.
        interacted (bool): Whether the view has been interacted with.
    """

    def __init__(self, ctx: ActionContext):
        """
        Initializes the TurnView.

        Args:
            ctx (dict): The context dictionary. Required keys:
                app
                action_id
                game
                game_id
        """
        super().__init__(timeout=60, disable_on_timeout=True)
        self.ctx: ActionContext = ctx
        self.interacted = False

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if not self.interacted and self.ctx.action_id == self.ctx.game.action_id:
            assert self.message
            view = TurnView(self.ctx.copy())
            turn_player: int = self.ctx.game.current_player_id
            card: str = self.ctx.game.draw_card(turn_player)
            match card:
                case "defuse":
                    await self.message.reply(MESSAGES["defused"].format(turn_player))
                case "eggsplode":
                    await self.message.reply(MESSAGES["eggsploded"].format(turn_player))
                case "gameover":
                    await self.message.reply(MESSAGES["eggsploded"].format(turn_player))
                    await self.message.reply(
                        MESSAGES["game_over"].format(self.ctx.game.players[0])
                    )
                    del self.ctx.games[self.ctx.game_id]
                    self.on_timeout = super().on_timeout
                    return
                case _:
                    await self.message.reply(MESSAGES["timeout"].format(turn_player))
            await self.message.reply(
                MESSAGES["next_turn"].format(self.ctx.game.current_player_id),
                view=view,
            )

    @discord.ui.button(label="Play!", style=discord.ButtonStyle.blurple, emoji="🤚")
    async def play(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the Play button click event.

        Args:
            _ (discord.ui.Button): The button instance.
            interaction (discord.Interaction): The interaction instance.
        """
        assert interaction.user
        if interaction.user.id != self.ctx.game.current_player_id:
            await interaction.response.send_message(
                MESSAGES["not_your_turn"], ephemeral=True
            )
            return
        assert interaction.message
        view = PlayView(
            ActionContext(
                app=self.ctx.app,
                parent_view=self,
                parent_interaction=interaction,
                game_id=self.ctx.game_id,
                action_id=self.ctx.action_id,
            )
        )
        await view.create_view()
        await interaction.response.send_message(
            MESSAGES["play_prompt"].format(
                len(self.ctx.game.deck), self.ctx.game.deck.count("eggsplode")
            ),
            view=view,
            ephemeral=True,
        )


class PlayView(discord.ui.View):
    """
    Represents the view for playing cards.

    Attributes:
        parent_view (TurnView): The parent TurnView instance.
        parent_interaction (discord.Interaction): The parent interaction instance.
        game (Game): The game instance.
        game_id (int): The game ID.
        action_id (int): The action ID.
        interacted (bool): Whether the view has been interacted with.
        play_card_select (discord.ui.Select): The card selection dropdown.
    """

    def __init__(self, ctx: ActionContext):
        """
        Initializes the PlayView.

        Args:
            ctx (dict): The context dictionary. Required keys:
                parent_view
                parent_interaction
                game
                game_id
                action_id
        """
        super().__init__(timeout=60, disable_on_timeout=True)
        self.ctx: ActionContext = ctx
        self.play_card_select = None

    async def create_view(self):
        """
        Creates the card selection view.
        """
        assert self.ctx.parent_interaction
        await self.create_card_selection(self.ctx.parent_interaction)

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        assert isinstance(self.ctx.parent_view, TurnView)
        if (
            not self.ctx.parent_view.interacted
            and self.ctx.action_id == self.ctx.game.action_id
        ):
            await super().on_timeout()

    async def verify_turn(self, interaction: discord.Interaction):
        """
        Verifies if it's the player's turn.

        Args:
            interaction (discord.Interaction): The interaction instance.

        Returns:
            bool: True if it's the player's turn, False otherwise.
        """
        assert interaction.user
        if self.ctx.game.awaiting_prompt:
            await interaction.response.send_message(MESSAGES["not_your_turn"], ephemeral=True)
            return False
        if interaction.user.id != self.ctx.game.current_player_id:
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(MESSAGES["not_your_turn"], ephemeral=True)
            return False
        if self.ctx.action_id != self.ctx.game.action_id:
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(MESSAGES["invalid_turn"], ephemeral=True)
            return False
        self.ctx.game.action_id += 1
        self.ctx.action_id += 1
        return True

    async def end_turn(self, interaction: discord.Interaction):
        """
        Ends the player's turn.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        assert isinstance(self.ctx.parent_view, TurnView)
        assert self.ctx.parent_interaction
        self.ctx.parent_view.interacted = True
        view = TurnView(self.ctx.copy())
        await interaction.followup.send(
            MESSAGES["next_turn"].format(self.ctx.game.current_player_id), view=view
        )
        self.ctx.parent_view.disable_all_items()
        assert self.ctx.parent_interaction.message
        await interaction.followup.edit_message(
            self.ctx.parent_interaction.message.id, view=self.ctx.parent_view
        )

    async def create_card_selection(self, interaction: discord.Interaction):
        """
        Creates the card selection dropdown.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        assert interaction.user
        user_cards: list = self.ctx.game.group_hand(
            interaction.user.id, usable_only=True
        )
        if len(user_cards) == 0:
            return
        self.play_card_select = discord.ui.Select(
            placeholder="Select a card to play",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    value=card,
                    label=f"{CARDS[card]['title']} ({count}x)",
                    description=CARDS[card]["description"],
                    emoji=CARDS[card]["emoji"],
                )
                for card, count in user_cards
            ],
        )
        self.play_card_select.callback = self.play_card
        self.add_item(self.play_card_select)

    @discord.ui.button(label="Draw", style=discord.ButtonStyle.blurple, emoji="🤚")
    async def draw_callback(
        self, _: discord.ui.Button, interaction: discord.Interaction
    ):
        """
        Handles the Draw button click event.

        Args:
            _ (discord.ui.Button): The button instance.
            interaction (discord.Interaction): The interaction instance.
        """
        await self.draw_card(interaction)

    async def draw_card(self, interaction: discord.Interaction):
        """
        Draws a card for the player.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        if not await self.verify_turn(interaction):
            return
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        assert interaction.user
        card: str = self.ctx.game.draw_card(interaction.user.id)
        match card:
            case "defuse":
                await interaction.followup.send(
                    MESSAGES["defused"].format(interaction.user.id)
                )
            case "eggsplode":
                await interaction.followup.send(
                    MESSAGES["eggsploded"].format(interaction.user.id)
                )
            case "gameover":
                await interaction.followup.send(
                    MESSAGES["eggsploded"].format(interaction.user.id)
                )
                await interaction.followup.send(
                    MESSAGES["game_over"].format(self.ctx.game.players[0])
                )
                del self.ctx.games[self.ctx.game_id]
                self.on_timeout = super().on_timeout
                return
            case _:
                await interaction.followup.send(
                    MESSAGES["user_drew_card"].format(interaction.user.id)
                )
                await interaction.followup.send(
                    MESSAGES["you_drew_card"].format(
                        CARDS[card]["emoji"], CARDS[card]["title"]
                    ),
                    ephemeral=True,
                )
        await self.end_turn(interaction)

    async def play_card(self, interaction: discord.Interaction):
        """
        Plays a selected card.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        assert interaction.message
        if not await self.verify_turn(interaction):
            return
        assert self.play_card_select
        selected = self.play_card_select.values[0]
        assert isinstance(selected, str)
        assert interaction.user
        await interaction.response.edit_message(view=self)
        self.ctx.game.hands[interaction.user.id].remove(selected)
        if selected == "attegg":
            await interaction.followup.send(
                MESSAGES["before_attegg"].format(
                    interaction.user.id, self.ctx.game.next_player_id
                ),
                view=NopeView(
                    ctx=self.ctx.copy(parent_interaction=interaction, parent_view=self),
                    target_player_id=self.ctx.game.next_player_id,
                    callback_action=lambda _: self.finalize_attegg(interaction),
                ),
            )
        elif selected == "skip":
            await interaction.followup.send(
                MESSAGES["before_skip"].format(
                    interaction.user.id,
                    (
                        self.ctx.game.next_player_id
                        if self.ctx.game.atteggs < 2
                        else interaction.user.id
                    ),
                ),
                view=NopeView(
                    ctx=self.ctx.copy(parent_interaction=interaction, parent_view=self),
                    target_player_id=(
                        self.ctx.game.next_player_id
                        if self.ctx.game.atteggs < 2
                        else interaction.user.id
                    ),
                    callback_action=lambda _: self.finalize_skip(interaction),
                ),
            )
        elif selected == "shuffle":
            random.shuffle(self.ctx.game.deck)
            await interaction.followup.send(
                MESSAGES["shuffled"].format(interaction.user.id),
            )
        elif selected == "predict":
            next_cards = "".join(
                MESSAGES["next_cards_list"].format(
                    CARDS[card]["emoji"], CARDS[card]["title"]
                )
                for card in self.ctx.game.deck[-1:-4:-1]
            )
            await interaction.followup.send(
                MESSAGES["predicted"].format(interaction.user.id),
            )
            await interaction.followup.send(
                MESSAGES["next_cards"].format(next_cards),
                ephemeral=True,
            )
        elif selected.startswith("food"):
            if not self.any_player_has_cards():
                self.ctx.game.hands[interaction.user.id].append(selected)
                await interaction.followup.send(MESSAGES["no_players_have_cards"])
            else:
                self.ctx.game.hands[interaction.user.id].remove(selected)
                view = ChoosePlayerView(
                    self.ctx.copy(parent_interaction=interaction, parent_view=self),
                    lambda target_player_id: self.begin_steal(
                        interaction, target_player_id
                    ),
                )
                await view.create_user_selection()
                await interaction.followup.send(
                    MESSAGES["steal_prompt"], view=view, ephemeral=True
                )
        else:
            await interaction.followup.send(MESSAGES["not_implemented"], ephemeral=True)
        self.remove_item(self.play_card_select)
        await self.create_card_selection(interaction)
        await interaction.followup.edit_message(interaction.message.id, view=self)

    def any_player_has_cards(self):
        """
        Checks if any player has cards.
        """
        eligible_players = self.ctx.game.players.copy()
        eligible_players.remove(self.ctx.game.current_player_id)
        return any(self.ctx.game.hands[player] for player in eligible_players)

    async def begin_steal(
        self, interaction: discord.Interaction, target_player_id: int
    ):
        """
        Begins the steal action.

        Args:
            interaction (discord.Interaction): The interaction instance.
            target_player_id (int): The target player ID.
        """
        assert interaction.user
        await interaction.followup.send(
            MESSAGES["before_steal"].format(interaction.user.id, target_player_id),
            view=NopeView(
                ctx=self.ctx.copy(parent_interaction=interaction, parent_view=self),
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
        Finalizes the steal action.

        Args:
            interaction (discord.Interaction): The interaction instance.
            target_interaction (discord.Interaction): The target interaction instance.
            target_player_id (int): The target player ID.
        """
        target_hand = self.ctx.game.hands[target_player_id]
        stolen_card = random.choice(target_hand)
        self.ctx.game.hands[target_player_id].remove(stolen_card)
        self.ctx.game.hands[self.ctx.game.current_player_id].append(stolen_card)
        await self.create_card_selection(interaction)
        assert interaction.message
        await interaction.followup.edit_message(interaction.message.id, view=self)
        await interaction.followup.send(
            MESSAGES["stolen_card_public"].format(
                self.ctx.game.current_player_id, target_player_id
            )
        )
        await interaction.followup.send(
            MESSAGES["stolen_card_you"].format(
                CARDS[stolen_card]["emoji"], CARDS[stolen_card]["title"]
            ),
            ephemeral=True,
        )
        if target_interaction:
            await target_interaction.followup.send(
                MESSAGES["stolen_card_them"].format(
                    self.ctx.game.current_player_id,
                    CARDS[stolen_card]["emoji"],
                    CARDS[stolen_card]["title"],
                ),
                ephemeral=True,
            )

    async def finalize_attegg(self, interaction: discord.Interaction):
        """
        Finalizes the attegg action.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        assert interaction.message
        self.disable_all_items()
        await interaction.followup.edit_message(interaction.message.id, view=self)
        prev_atteggs: int = self.ctx.game.atteggs
        self.ctx.game.atteggs = 0
        self.ctx.game.next_turn()
        self.ctx.game.atteggs = prev_atteggs + 1
        await self.end_turn(interaction)

    async def finalize_skip(self, interaction: discord.Interaction):
        """
        Finalizes the skip action.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        assert interaction.message
        self.disable_all_items()
        await interaction.followup.edit_message(interaction.message.id, view=self)
        self.ctx.game.next_turn()
        await self.end_turn(interaction)


class NopeView(discord.ui.View):
    """
    Represents the view for the Nope action.

    Attributes:
        parent_interaction (discord.Interaction): The parent interaction instance.
        game (Game): The game instance.
        game_id (int): The game ID.
        action_id (int): The action ID.
        target_player (int): The target player ID.
        callback_action (callable): The staged action to perform.
        interacted (bool): Whether the view has been interacted with.
    """

    def __init__(
        self,
        ctx: ActionContext,
        target_player_id: int,
        callback_action,
    ):
        """
        Initializes the NopeView.

        Args:
            ctx: The context dictionary. Required keys:
                parent_interaction
                game
                action_id
            target_player (int): The target player ID.
            callback_action (callable): The staged action to perform.
        """
        super().__init__(timeout=10, disable_on_timeout=True)
        self.ctx = ctx
        self.target_player = target_player_id
        self.callback_action = callback_action
        self.interacted = False
        self.ctx.game.awaiting_prompt = True

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if not self.interacted and self.ctx.action_id == self.ctx.game.action_id:
            self.ctx.game.awaiting_prompt = False
            if self.callback_action:
                await self.callback_action(None)
            return await super().on_timeout()

    @discord.ui.button(label="OK!", style=discord.ButtonStyle.green, emoji="✅")
    async def ok_callback(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the OK button click event.

        Args:
            _ (discord.ui.Button): The button instance.
            interaction (discord.Interaction): The interaction instance.
        """
        assert interaction.user
        assert self.ctx.parent_interaction
        assert self.ctx.parent_interaction.user
        if interaction.user.id != self.target_player:
            await interaction.response.send_message(
                MESSAGES["not_your_turn"], ephemeral=True
            )
            return
        self.interacted = True
        self.ctx.game.awaiting_prompt = False
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        if self.callback_action:
            await self.callback_action(interaction)

    @discord.ui.button(label="Nope!", style=discord.ButtonStyle.red, emoji="🛑")
    async def nope_callback(
        self, _: discord.ui.Button, interaction: discord.Interaction
    ):
        """
        Handles the Nope button click event.

        Args:
            _ (discord.ui.Button): The button instance.
            interaction (discord.Interaction): The interaction instance.
        """
        assert interaction.user
        assert self.ctx.parent_interaction
        assert self.ctx.parent_interaction.user
        if self.ctx.parent_interaction.user.id == interaction.user.id:
            await interaction.response.send_message(
                MESSAGES["no_self_nope"], ephemeral=True
            )
            return
        if interaction.user.id not in self.ctx.game.players:
            await interaction.response.send_message(
                MESSAGES["user_not_in_game"], ephemeral=True
            )
            return
        try:
            self.ctx.game.hands[interaction.user.id].remove("nope")
        except ValueError:
            await interaction.response.send_message(
                MESSAGES["no_nope_cards"], ephemeral=True
            )
            return
        assert interaction.message
        self.interacted = True
        self.ctx.game.awaiting_prompt = False
        self.disable_all_items()
        await interaction.response.edit_message(
            content=MESSAGES["message_edit_on_nope"].format(
                interaction.message.content, interaction.user.id
            ),
            view=self,
        )


class ChoosePlayerView(discord.ui.View):
    """
    Represents the view to select a user.
    """

    def __init__(self, ctx: ActionContext, callback_action):
        """
        Initializes the ChoosePlayerView.
        """
        super().__init__(timeout=10, disable_on_timeout=True)
        self.ctx: ActionContext = ctx
        self.eligible_players = self.ctx.game.players.copy()
        self.eligible_players.remove(self.ctx.game.current_player_id)
        self.callback_action = callback_action
        self.user_select = None
        self.interacted = False

    async def on_timeout(self):
        if not self.interacted:
            assert self.user_select
            await self.callback_action(self.user_select.options[0].value)
            return await super().on_timeout()

    async def create_user_selection(self):
        """
        Creates the user selection dropdown.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        options = []
        for user_id in self.eligible_players:
            user = await self.ctx.app.get_or_fetch_user(user_id)
            assert user
            if not self.ctx.game.hands[user_id]:
                continue
            options.append(
                discord.SelectOption(
                    value=str(user_id),
                    label=f"{user.display_name} ({len(self.ctx.game.hands[user_id])} cards)",
                )
            )
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
        Called when the user selects an item.
        """
        assert interaction
        assert self.user_select
        self.interacted = True
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        assert isinstance(self.user_select.values[0], str)
        await self.callback_action(int(self.user_select.values[0]))


class StartGameView(discord.ui.View):
    """
    Represents the view for starting a game.

    Attributes:
        app (Eggsplode): The Eggsplode bot instance.
        game_id (int): The game ID.
    """

    def __init__(self, app: Eggsplode, game_id: int):
        """
        Initializes the StartGameView.

        Args:
            app (Eggsplode): The Eggsplode bot instance.
            game_id (int): The game ID.
        """
        super().__init__(timeout=600, disable_on_timeout=True)
        self.app = app
        self.game_id = game_id
        self.started = False

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if not self.started:
            del self.app.games[self.game_id]
            await super().on_timeout()

    @discord.ui.button(label="Join", style=discord.ButtonStyle.blurple, emoji="👋")
    async def join_game(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the Join button click event.

        Args:
            _ (discord.ui.Button): The button instance.
            interaction (discord.Interaction): The interaction instance.
        """
        game = self.app.games[self.game_id]
        assert interaction.user
        if interaction.user.id in game.players:
            await interaction.response.send_message(
                MESSAGES["already_in_game"], ephemeral=True
            )
            return
        game.players.append(interaction.user.id)
        assert interaction.message and interaction.message.content
        await interaction.response.edit_message(
            content=MESSAGES["players_list_item"].format(
                interaction.message.content, interaction.user.id
            )
        )

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, emoji="🚀")
    async def start_game(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the Start Game button click event.

        Args:
            _ (discord.ui.Button): The button instance.
            interaction (discord.Interaction): The interaction instance.
        """
        game = self.app.games[self.game_id]
        assert interaction.user
        if interaction.user.id != game.players[0]:
            await interaction.response.send_message(
                MESSAGES["not_game_creator_start"], ephemeral=True
            )
            return
        if len(game.players) < 2:
            await interaction.response.send_message(
                MESSAGES["not_enough_players_to_start"], ephemeral=True
            )
            return
        self.started = True
        game.start()
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(MESSAGES["game_started"], ephemeral=True)
        view = TurnView(
            ActionContext(
                app=self.app,
                parent_interaction=interaction,
                parent_view=None,
                action_id=None,
                game_id=self.game_id,
            )
        )
        await interaction.followup.send(
            MESSAGES["next_turn"].format(game.current_player_id), view=view
        )
