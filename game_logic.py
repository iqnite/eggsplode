"""
Game logic for Eggsplode.
"""

import json
import random
import discord
from discord.ext import commands

with open("cardtypes.json", encoding="utf-8") as f:
    CARDS = json.load(f)


class ActionContext:
    def __init__(
        self,
        *,
        app=None,
        parent_view=None,
        parent_interaction: discord.Interaction | None = None,
        game_id: int | None = None,
        action_id: int | None = None,
    ):
        if app:
            self.app: Eggsplode = app
            self.games: dict[int, Game] = self.app.games
        if parent_view:
            self.parent_view: discord.ui.View | TurnView | PlayView | NopeView = (
                parent_view
            )
        if game_id:
            self.game_id: int = game_id
            self.game: Game = self.games[game_id]
        if parent_interaction:
            self.parent_interaction: discord.Interaction = parent_interaction
        if action_id:
            self.action_id: int = action_id
        elif self.game:
            self.action_id: int = self.game.action_id

    def copy(
        self,
        *,
        app=None,
        parent_view=None,
        parent_interaction: discord.Interaction | None = None,
        game_id: int | None = None,
        action_id: int | None = None,
    ):
        return ActionContext(
            app=app if app else self.app,
            parent_view=parent_view if parent_view else self.parent_view,
            parent_interaction=parent_interaction if parent_interaction else self.parent_interaction,
            game_id=game_id if game_id else self.game_id,
            action_id=action_id if action_id else self.action_id,
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
            if usable_only and not CARDS[card]["usable"]:
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

    def kick_ends_game(self, user_id):
        """
        Kicks a player for inactivity and checks if the game ends.

        Args:
            user_id (int): Player ID.

        Returns:
            bool: True if the game ends, False otherwise.
        """
        self.remove_player(user_id)
        if len(self.players) == 1:
            return True
        for i in range(len(self.deck) - 1, 0, -1):
            if self.deck[i] == "eggsplode":
                self.deck.pop(i)
                break
        return False


class Eggsplode(commands.Bot):
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
            app (Eggsplode): The Eggsplode bot instance.
            game_id (int): The game ID.
        """
        super().__init__(timeout=30)
        self.ctx = ctx
        self.interacted = False

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if not self.interacted and self.ctx.action_id == self.ctx.game.action_id:
            assert self.message
            view = TurnView(self.ctx)
            prev_user = self.ctx.game.current_player_id
            if self.ctx.game.kick_ends_game(self.ctx.game.current_player_id):
                await self.message.edit(
                    content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n# 🎉 <@{self.ctx.game.players[0]}> wins!",
                    view=None,
                )
                del self.ctx.games[self.ctx.game_id]
            else:
                await self.message.edit(
                    content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n### ⌛ <@{self.ctx.game.current_player_id}>'s turn!",
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
                "❌ It's not your turn!", ephemeral=True
            )
            return
        assert interaction.message
        self.interacted = True
        view = PlayView(
            ActionContext(
                parent_view=self,
                parent_interaction=interaction,
                game_id=self.ctx.game_id,
                action_id=self.ctx.action_id,
            )
        )
        await view.create_view()
        await interaction.response.send_message(
            "**Play** as many cards as you want, then **draw** a card to end your turn!",
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
            parent_view (TurnView): The parent TurnView instance.
            parent_interaction (discord.Interaction): The parent interaction instance.
            game_id (int): The game ID.
            action_id (int): The action ID.
        """
        super().__init__(timeout=120)
        self.ctx = ctx
        self.interacted = False
        self.play_card_select = None

    async def create_view(self):
        """
        Creates the card selection view.
        """
        await self.create_card_selection(self.ctx.parent_interaction)

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if not self.interacted and self.ctx.action_id == self.ctx.game.action_id:
            view = TurnView(self.ctx)
            prev_user = self.ctx.game.current_player_id
            if self.ctx.game.kick_ends_game(self.ctx.game.current_player_id):
                await self.ctx.parent_interaction.followup.send(
                    content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n# 🎉 <@{self.ctx.game.players[0]}> wins!"
                )
                del self.ctx.games[self.ctx.game_id]
            else:
                await self.ctx.parent_interaction.followup.send(
                    content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n### ⌛ <@{self.ctx.game.current_player_id}>'s turn!",
                    view=view,
                )
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
        if interaction.user.id != self.ctx.game.current_player_id:
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("❌ It's not your turn!", ephemeral=True)
            return False
        if self.ctx.action_id != self.ctx.game.action_id:
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                "❌ This turn has ended or the action is not valid anymore! Use **/play** to update it.",
                ephemeral=True,
            )
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
        self.interacted = True
        view = TurnView(self.ctx)
        await interaction.followup.send(
            f"### ⌛ <@{self.ctx.game.current_player_id}>'s turn!", view=view
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
        user_cards = self.ctx.game.group_hand(interaction.user.id, usable_only=True)
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
        card = self.ctx.game.draw_card(interaction.user.id)
        match card:
            case "defuse":
                await interaction.followup.send(
                    f"## 🔧 <@{interaction.user.id}> drew an Eggsplode card! Luckily, they had an Defuse and put it back into the deck!"
                )
            case "eggsplode":
                await interaction.followup.send(
                    f"## 💥 <@{interaction.user.id}> drew an Eggsplode card and died!"
                )
            case "gameover":
                await interaction.followup.send(
                    f"## 💥 <@{interaction.user.id}> drew an Eggsplode card and died!"
                )
                await interaction.followup.send(
                    f"# 🎉 <@{self.ctx.game.players[0]}> wins!"
                )
                del self.ctx.games[self.ctx.game_id]
                self.on_timeout = super().on_timeout
                return
            case _:
                await interaction.followup.send(
                    f"🃏 <@{interaction.user.id}> drew a card!"
                )
                await interaction.followup.send(
                    f"You drew a **{CARDS[card]['emoji']} {CARDS[card]['title']}**!",
                    ephemeral=True,
                )
        await self.end_turn(interaction)

    async def play_card(self, interaction: discord.Interaction):
        """
        Plays a selected card.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        if not await self.verify_turn(interaction):
            return
        assert self.play_card_select
        selected = self.play_card_select.values[0]
        assert isinstance(selected, str)
        assert interaction.user
        self.ctx.game.hands[interaction.user.id].remove(selected)
        self.remove_item(self.play_card_select)
        await self.create_card_selection(interaction)
        await interaction.response.edit_message(view=self)
        match selected:
            case "attegg":
                await interaction.followup.send(
                    f"⚡ <@{interaction.user.id}> wants to skip and force <@{self.ctx.game.next_player_id}> to draw twice. Accept?",
                    view=NopeView(
                        ctx=self.ctx.copy(parent_interaction=interaction),
                        target_player=self.ctx.game.next_player_id,
                        staged_action=lambda: self.finalize_attegg(interaction),
                    ),
                )
            case "skip":
                await interaction.followup.send(
                    f"⏩ <@{interaction.user.id}> skipped their turn and did not draw a card! Next up: <@{self.ctx.game.next_player_id if self.ctx.game.atteggs < 2 else interaction.user.id}>. Accept?",
                    view=NopeView(
                        ctx=self.ctx.copy(parent_interaction=interaction),
                        target_player=(
                            self.ctx.game.next_player_id
                            if self.ctx.game.atteggs < 2
                            else interaction.user.id
                        ),
                        staged_action=lambda: self.finalize_skip(interaction),
                    ),
                )
            case "shuffle":
                random.shuffle(self.ctx.game.deck)
                await interaction.followup.send(
                    f"🌀 <@{interaction.user.id}> shuffled the deck!",
                )
                await interaction.followup.send(
                    "Don't forget to draw a card!", ephemeral=True
                )
            case "predict":
                next_cards = "".join(
                    f"\n- **{CARDS[card]['emoji']} {CARDS[card]['title']}**"
                    for card in self.ctx.game.deck[-1:-4:-1]
                )
                await interaction.followup.send(
                    f"🔮 <@{interaction.user.id}> looked at the next 3 cards on the deck!"
                )
                await interaction.followup.send(
                    f"### Next 3 cards on the deck:{next_cards}\n-# Don't forget to draw a card!",
                    ephemeral=True,
                )
            case _:
                await interaction.followup.send(
                    "🙁 Sorry, not implemented yet.", ephemeral=True
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
        prev_atteggs = self.ctx.game.atteggs
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
        staged_action (callable): The staged action to perform.
        interacted (bool): Whether the view has been interacted with.
    """

    def __init__(
        self,
        ctx: ActionContext,
        target_player: int,
        staged_action=None,
    ):
        """
        Initializes the NopeView.

        Args:
            parent_interaction (discord.Interaction): The parent interaction instance.
            app (Eggsplode): The Eggsplode bot instance.
            game_id (int): The game ID.
            action_id (int): The action ID.
            target_player (int): The target player ID.
            staged_action (callable): The staged action to perform.
        """
        super().__init__(timeout=30)
        self.ctx = ctx
        self.target_player = target_player
        self.staged_action = staged_action
        self.interacted = False

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if not self.interacted and self.ctx.action_id == self.ctx.game.action_id:
            if self.staged_action:
                await self.staged_action()
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
        assert self.ctx.parent_interaction.user
        if interaction.user.id != self.target_player:
            await interaction.response.send_message(
                "❌ It's not your turn!", ephemeral=True
            )
            return
        self.interacted = True
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        if self.staged_action:
            await self.staged_action()

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
        assert self.ctx.parent_interaction.user
        if self.ctx.parent_interaction.user.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ You can't Nope yourself!", ephemeral=True
            )
            return
        if interaction.user.id not in self.ctx.game.players:
            await interaction.response.send_message(
                "❌ You are not in this game!", ephemeral=True
            )
            return
        try:
            self.ctx.game.hands[interaction.user.id].remove("nope")
        except ValueError:
            await interaction.response.send_message(
                "❌ You have no **Nope** cards to play!", ephemeral=True
            )
            return
        assert interaction.message
        self.interacted = True
        self.disable_all_items()
        await interaction.response.edit_message(
            content=f"~~{interaction.message.content}~~\n🛑 <@{interaction.user.id}>: **Nope!**\n-# Don't forget to draw a card!",
            view=self,
        )


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
        super().__init__(timeout=600)
        self.app = app
        self.game_id = game_id

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
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
                "❌ You are already in the game!", ephemeral=True
            )
            return
        game.players.append(interaction.user.id)
        assert interaction.message and interaction.message.content
        await interaction.response.edit_message(
            content=interaction.message.content + f"\n- <@{interaction.user.id}>"
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
                "❌ Only the game creator can start the game!", ephemeral=True
            )
            return
        if len(game.players) < 2:
            await interaction.response.send_message(
                "❌ Not enough players to start the game!", ephemeral=True
            )
            return
        game.start()
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("🚀 Game Started!")
        view = TurnView(ActionContext(app=self.app, game_id=self.game_id))
        await interaction.followup.send(
            f"### ⌛ <@{game.current_player_id}>'s turn!", view=view
        )
