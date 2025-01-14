"""
Eggsplode Discord Bot

This module contains the implementation of the Eggsplode Discord bot, including
the game logic, bot commands, and interaction views.

Classes:
    Game: Represents a game of Eggsplode.
    Eggsplode: Represents the Eggsplode bot.
    TurnView: Represents the view for a player's turn.
    PlayView: Represents the view for playing cards.
    NopeView: Represents the view for the Nope action.
    StartGameView: Represents the view for starting a game.

Functions:
    games_with_user(user_id): Returns a list of games that the user is in.
    game_id_autocomplete(ctx): Autocompletes the game ID for the user.
    start(ctx): Starts a new Eggsplode game.
    play(ctx, game_id): Plays the user's turn.
    hand(ctx, game_id): Views the user's hand.
    show_help(ctx): Shows the help message.
    ping(ctx): Checks if the Eggsplode bot is online.
    admincmd(ctx, command): Executes an admin command.
"""

import os
import random
import json
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
ADMIN_MAINTENANCE_CODE = os.getenv("ADMIN_MAINTENANCE_CODE")
ADMIN_LISTGAMES_CODE = os.getenv("ADMIN_LISTGAMES_CODE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
assert DISCORD_TOKEN is not None, "DISCORD_TOKEN is not set in .env file"
with open("cardtypes.json", encoding="utf-8") as f:
    CARDS = json.load(f)


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

    def __init__(self, app: Eggsplode, game_id: int):
        """
        Initializes the TurnView.

        Args:
            app (Eggsplode): The Eggsplode bot instance.
            game_id (int): The game ID.
        """
        super().__init__(timeout=30)
        self.app = app
        self.game_id = game_id
        self.game: Game = self.app.games[game_id]
        self.action_id = self.game.action_id
        self.interacted = False

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if not self.interacted and self.action_id == self.game.action_id:
            assert self.message
            view = TurnView(self.app, self.game_id)
            prev_user = self.game.current_player_id
            if self.game.kick_ends_game(self.game.current_player_id):
                await self.message.edit(
                    content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n# 🎉 <@{self.game.players[0]}> wins!",
                    view=None,
                )
                del self.app.games[self.game_id]
            else:
                await self.message.edit(
                    content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n### ⌛ <@{self.game.current_player_id}>'s turn!",
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
        if interaction.user.id != self.game.current_player_id:
            await interaction.response.send_message(
                "❌ It's not your turn!", ephemeral=True
            )
            return
        assert interaction.message
        self.interacted = True
        view = PlayView(self, interaction, self.game_id, self.action_id)
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

    def __init__(
        self,
        parent_view: TurnView,
        parent_interaction: discord.Interaction,
        game_id: int,
        action_id: int,
    ):
        """
        Initializes the PlayView.

        Args:
            parent_view (TurnView): The parent TurnView instance.
            parent_interaction (discord.Interaction): The parent interaction instance.
            game_id (int): The game ID.
            action_id (int): The action ID.
        """
        super().__init__(timeout=120)
        self.parent_view = parent_view
        self.parent_interaction = parent_interaction
        self.game = parent_view.app.games[game_id]
        self.game_id = game_id
        self.action_id = action_id
        self.interacted = False
        self.play_card_select = None

    async def create_view(self):
        """
        Creates the card selection view.
        """
        await self.create_card_selection(self.parent_interaction)

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if not self.interacted and self.action_id == self.game.action_id:
            view = TurnView(self.parent_view.app, self.game_id)
            prev_user = self.game.current_player_id
            if self.game.kick_ends_game(self.game.current_player_id):
                await self.parent_interaction.followup.send(
                    content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n# 🎉 <@{self.game.players[0]}> wins!"
                )
                del self.parent_view.app.games[self.game_id]
            else:
                await self.parent_interaction.followup.send(
                    content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n### ⌛ <@{self.game.current_player_id}>'s turn!",
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
        if interaction.user.id != self.game.current_player_id:
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("❌ It's not your turn!", ephemeral=True)
            return False
        if self.action_id != self.game.action_id:
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                "❌ This turn has ended or the action is not valid anymore! Use **/play** to update it.",
                ephemeral=True,
            )
            return False
        self.game.action_id += 1
        self.action_id += 1
        return True

    async def end_turn(self, interaction: discord.Interaction):
        """
        Ends the player's turn.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        self.interacted = True
        view = TurnView(self.parent_view.app, self.game_id)
        await interaction.followup.send(
            f"### ⌛ <@{self.game.current_player_id}>'s turn!", view=view
        )
        self.parent_view.disable_all_items()
        assert self.parent_interaction.message
        await interaction.followup.edit_message(
            self.parent_interaction.message.id, view=self.parent_view
        )

    async def create_card_selection(self, interaction: discord.Interaction):
        """
        Creates the card selection dropdown.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        assert interaction.user
        user_cards = self.game.group_hand(interaction.user.id, usable_only=True)
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
        card = self.game.draw_card(interaction.user.id)
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
                await interaction.followup.send(f"# 🎉 <@{self.game.players[0]}> wins!")
                del self.parent_view.app.games[self.game_id]
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
        self.game.hands[interaction.user.id].remove(selected)
        self.remove_item(self.play_card_select)
        await self.create_card_selection(interaction)
        await interaction.response.edit_message(view=self)
        match selected:
            case "attegg":
                await interaction.followup.send(
                    f"⚡ <@{interaction.user.id}> wants to skip and force <@{self.game.next_player_id}> to draw twice. Accept?",
                    view=NopeView(
                        parent_interaction=interaction,
                        app=self.parent_view.app,
                        game_id=self.game_id,
                        action_id=self.action_id,
                        target_player=self.game.next_player_id,
                        staged_action=lambda: self.finalize_attegg(interaction),
                    ),
                )
            case "skip":
                await interaction.followup.send(
                    f"⏩ <@{interaction.user.id}> skipped their turn and did not draw a card! Next up: <@{self.game.next_player_id if self.game.atteggs < 2 else interaction.user.id}>. Accept?",
                    view=NopeView(
                        parent_interaction=interaction,
                        app=self.parent_view.app,
                        game_id=self.game_id,
                        action_id=self.action_id,
                        target_player=(
                            self.game.next_player_id
                            if self.game.atteggs < 2
                            else interaction.user.id
                        ),
                        staged_action=lambda: self.finalize_skip(interaction),
                    ),
                )
            case "shuffle":
                random.shuffle(self.game.deck)
                await interaction.followup.send(
                    f"🌀 <@{interaction.user.id}> shuffled the deck!",
                )
                await interaction.followup.send(
                    "Don't forget to draw a card!", ephemeral=True
                )
            case "predict":
                next_cards = "".join(
                    f"\n- **{CARDS[card]['emoji']} {CARDS[card]['title']}**"
                    for card in self.game.deck[-1:-4:-1]
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
        prev_atteggs = self.game.atteggs
        self.game.atteggs = 0
        self.game.next_turn()
        self.game.atteggs = prev_atteggs + 1
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
        self.game.next_turn()
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
        parent_interaction: discord.Interaction,
        app: Eggsplode,
        game_id: int,
        action_id: int,
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
        self.parent_interaction = parent_interaction
        self.game = app.games[game_id]
        self.game_id = game_id
        self.action_id = action_id
        self.target_player = target_player
        self.staged_action = staged_action
        self.interacted = False

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if not self.interacted and self.action_id == self.game.action_id:
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
        assert self.parent_interaction.user
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
        assert self.parent_interaction.user
        if self.parent_interaction.user.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ You can't Nope yourself!", ephemeral=True
            )
            return
        if interaction.user.id not in self.game.players:
            await interaction.response.send_message(
                "❌ You are not in this game!", ephemeral=True
            )
            return
        try:
            self.game.hands[interaction.user.id].remove("nope")
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
        view = TurnView(self.app, self.game_id)
        await interaction.followup.send(
            f"### ⌛ <@{game.current_player_id}>'s turn!", view=view
        )


eggsplode_app = Eggsplode(
    activity=discord.Activity(type=discord.ActivityType.watching, name="you")
)


@eggsplode_app.slash_command(
    name="start",
    description="Start a new Eggsplode game!",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def start(ctx: discord.ApplicationContext):
    """
    Starts a new Eggsplode game.

    Args:
        ctx (discord.ApplicationContext): The application context.
    """
    if eggsplode_app.admin_maintenance:
        await ctx.respond(
            "⚠️ The bot is currently under maintenance. Please try again later. You can find more info in our support server.",
            ephemeral=True,
        )
        return
    assert ctx.interaction.user
    game_id = ctx.interaction.id
    view = StartGameView(eggsplode_app, game_id)
    eggsplode_app.games[game_id] = Game(ctx.interaction.user.id)
    await ctx.respond(
        f"# New game\n-# Game ID: {game_id}\n<@{ctx.interaction.user.id}> wants to start a new Eggsplode game! Click on **Join** to participate!\n**Players:**\n- <@{ctx.interaction.user.id}>",
        view=view,
    )


def games_with_user(user_id):
    """
    Returns a list of games that the user is in.

    Args:
        user_id (int): The user ID.

    Returns:
        list[Game]: List of games.
    """
    return [i for i, game in eggsplode_app.games.items() if user_id in game.players]


async def game_id_autocomplete(ctx: discord.AutocompleteContext):
    """
    Autocompletes the game ID for the user.

    Args:
        ctx (discord.AutocompleteContext): The autocomplete context.

    Returns:
        list[str]: List of game IDs.
    """
    if not ctx.interaction.user:
        return []
    return map(str, games_with_user(ctx.interaction.user.id))


@eggsplode_app.slash_command(
    name="play",
    description="Play your turn.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
@discord.option(
    "game_id",
    type=str,
    description="The game ID",
    required=False,
    default="",
    autocomplete=game_id_autocomplete,
)
async def play(
    ctx: discord.ApplicationContext,
    game_id: str,
):
    """
    Plays the user's turn.

    Args:
        ctx (discord.ApplicationContext): The application context.
        game_id (str): The game ID.
    """
    assert ctx.interaction.user
    if not game_id:
        games_with_id = games_with_user(ctx.interaction.user.id)
        if not games_with_id:
            await ctx.respond("❌ You are not in any games!", ephemeral=True)
            return
        new_game_id = games_with_id[0]
    else:
        new_game_id = int(game_id)
    if new_game_id not in eggsplode_app.games:
        await ctx.respond("❌ Game not found!", ephemeral=True)
        return
    if ctx.interaction.user.id not in eggsplode_app.games[new_game_id].players:
        await ctx.respond("❌ You are not in this game!", ephemeral=True)
        return
    if not eggsplode_app.games[new_game_id].hands:
        await ctx.respond("❌ Game has not started yet!", ephemeral=True)
        return
    view = TurnView(eggsplode_app, new_game_id)
    await ctx.respond(
        "Click on **Play!** to make your turn.", view=view, ephemeral=True
    )


@eggsplode_app.slash_command(
    name="hand",
    description="View your hand.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
@discord.option(
    "game_id",
    type=str,
    description="The game ID",
    required=False,
    default="",
    autocomplete=game_id_autocomplete,
)
async def hand(
    ctx: discord.ApplicationContext,
    game_id: str,
):
    """
    Views the user's hand.

    Args:
        ctx (discord.ApplicationContext): The application context.
        game_id (str): The game ID.
    """
    assert ctx.interaction.user
    if not game_id:
        games_with_id = games_with_user(ctx.interaction.user.id)
        if not games_with_id:
            await ctx.respond("❌ You are not in any games!", ephemeral=True)
            return
        new_game_id = games_with_id[0]
    else:
        new_game_id = int(game_id)
    if new_game_id not in eggsplode_app.games:
        await ctx.respond("❌ Game not found!", ephemeral=True)
        return
    if ctx.interaction.user.id not in eggsplode_app.games[new_game_id].players:
        await ctx.respond("❌ You are not in this game!", ephemeral=True)
        return
    try:
        player_hand = eggsplode_app.games[new_game_id].group_hand(
            ctx.interaction.user.id
        )
        hand_details = "".join(
            f"\n- **{CARDS[card]['emoji']} {CARDS[card]['title']}** ({count}x): {CARDS[card]['description']}"
            for card, count in player_hand
        )
        await ctx.respond(f"# Your hand:{hand_details}", ephemeral=True)
    except KeyError:
        await ctx.respond("❌ Game has not started yet!", ephemeral=True)


@eggsplode_app.slash_command(
    name="help",
    description="Learn how to play Eggsplode!",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def show_help(ctx: discord.ApplicationContext):
    """
    Shows the help message.

    Args:
        ctx (discord.ApplicationContext): The application context.
    """
    await ctx.respond(
        "\n".join(
            (
                "# How to start a game",
                "Use the </start:1325457141628141661> command to create a new game. Once everyone has joined, select **Start game** to begin!",
                "# How to play",
                "1. Once it's your turn, click on **Play!**",
                "2. Play as many cards form the dropdown menu as you want. You can also not play any cards.",
                "3. Click on **Draw** to draw a card from the deck and end your turn. It may not be required after playing some card types.",
                "# Eggsploding and Defusing",
                "If you draw an **Eggsplode** card and don't have **Defuse** card, you're out of the game. If you have a **Defuse** card, you can put the **Eggsplode** card back into the deck.",
            )
        )
    )


@eggsplode_app.slash_command(
    name="ping",
    description="Check if Eggsplode is online.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def ping(ctx: discord.ApplicationContext):
    """
    Checks if the Eggsplode bot is online.

    Args:
        ctx (discord.ApplicationContext): The application context.
    """
    await ctx.respond(f"Pong! ({eggsplode_app.latency*1000:.0f}ms)")


@eggsplode_app.slash_command(
    name="admincmd",
    description="Staff only.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
@discord.option(
    "command",
    type=str,
    description="If you don't know any command, you're not an admin.",
    required=True,
)
async def admincmd(
    ctx: discord.ApplicationContext,
    command: str,
):
    """
    Executes an admin command.

    Args:
        ctx (discord.ApplicationContext): The application context.
        command (str): The admin command.
    """
    if command == ADMIN_MAINTENANCE_CODE:
        eggsplode_app.admin_maintenance = not eggsplode_app.admin_maintenance
        await ctx.respond(
            f"🔧 Admin maintenance mode {'enabled' if eggsplode_app.admin_maintenance else 'disabled'}.{' ✅ No games running.' if not eggsplode_app.games else ''}",
            ephemeral=True,
        )
    elif command == ADMIN_LISTGAMES_CODE:
        await ctx.respond(
            f"📋 **Games:**\n- {', '.join(str(i) for i in eggsplode_app.games)}",
            ephemeral=True,
        )
    else:
        await ctx.respond("❌ Invalid command.", ephemeral=True)


print("Hello, World!")
eggsplode_app.run(DISCORD_TOKEN)
