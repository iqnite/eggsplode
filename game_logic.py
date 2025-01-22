"""
Eggsplode game logic.
"""

import random
from common import CARDS


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
                if player not in self.hands:
                    self.hands[player] = []
                self.hands[player].append(self.deck.pop())
        for player in self.players:
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
        result = {}
        for card in player_cards:
            if usable_only:
                if not CARDS[card]["usable"]:
                    continue
                if CARDS[card].get("combo", 0) > 0 and player_cards.count(card) < 2:
                    continue
            if card in result:
                continue
            result[card] = player_cards.count(card)
        return result

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

    def any_player_has_cards(self):
        """
        Checks if any player has cards.
        """
        eligible_players = self.players.copy()
        eligible_players.remove(self.current_player_id)
        return any(self.hands[player] for player in eligible_players)

    def cards_help(self, user_id, template=""):
        """
        Returns the help message for cards.

        Args:
            user_id (int): Player ID.

        Returns:
            str: Help message.
        """
        "\n".join(
            template.format(
                CARDS[card]["emoji"],
                CARDS[card]["title"],
                count,
                CARDS[card]["description"],
            )
            for card, count in self.group_hand(user_id)
        )


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
        self.app = app
        self.games: dict[int, Game] = self.app.games
        self.parent_view = parent_view
        self.parent_interaction = parent_interaction
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
