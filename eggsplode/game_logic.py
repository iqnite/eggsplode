"""
Contains the game logic for the Eggsplode game.
"""

from datetime import datetime
import random
from .strings import CARDS


class Game:
    """
    Represents the game logic for the Eggsplode game.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, config: dict):
        """
        Initializes the game with the given players.

        Args:
            config: The initial configuration for the game.
        """
        self.config = config
        self.players: list[int] = []
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.current_player: int = 0
        self.action_id: int = 0
        self.draw_in_turn: int = 0
        self.awaiting_prompt: bool = False
        self.last_activity = datetime.now()

    def start(self):
        """
        Starts the game by initializing the deck and dealing cards to players.
        """
        self.last_activity = datetime.now()
        self.deck = []
        self.players = list(self.config["players"])
        for card in CARDS:
            self.deck += (
                [card]
                * CARDS[card]["count"]
                * (
                    CARDS[card].get("expansion", "base")
                    in self.config.get("expansions", []) + ["base"]
                )
            )
        self.deck = self.deck * (1 + len(self.players) // 5)
        random.shuffle(self.deck)
        self.hands = {
            player: ["defuse"] + [self.deck.pop() for _ in range(7)]
            for player in self.players
        }
        self.deck += ["radioeggtive"] * (
            "radioeggtive" in self.config.get("expansions", [])
        )
        self.deck += ["eggsplode"] * int(
            self.config.get(
                "deck_eggsplode_cards",
                len(self.players) - 1,
            )
        )
        self.deck += ["defuse"] * int(self.config.get("deck_defuse_cards", 0))
        random.shuffle(self.deck)

    @property
    def current_player_id(self) -> int:
        """
        Returns the ID of the current player.

        Returns:
            int: The ID of the current player.
        """
        return self.players[self.current_player]

    @property
    def current_player_hand(self) -> list[str]:
        """
        Returns the hand of the current player.

        Returns:
            list[str]: The hand of the current player.
        """
        return self.hands[self.current_player_id]

    @property
    def next_player(self) -> int:
        """
        Returns the index of the next player.

        Returns:
            int: The index of the next player.
        """
        return (
            0
            if self.current_player >= len(self.players) - 1
            else self.current_player + 1
        )

    @property
    def next_player_id(self) -> int:
        """
        Returns the ID of the next player.

        Returns:
            int: The ID of the next player.
        """
        return self.players[self.next_player]

    def next_turn(self):
        """
        Advances the game to the next player's turn.
        """
        self.last_activity = datetime.now()
        if self.draw_in_turn > 1:
            self.draw_in_turn -= 1
            if self.draw_in_turn == 1:
                self.draw_in_turn = 0
            return
        self.current_player = self.next_player

    def group_hand(self, user_id: int, usable_only: bool = False) -> dict:
        """
        Groups the cards in a player's hand.

        Args:
            user_id (int): The ID of the player.
            usable_only (bool): Whether to include only usable cards.

        Returns:
            dict: A dictionary of card counts.
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

    def draw_card(self, index: int = -1) -> str:
        """
        Draws a card for the specified player.

        Args:
            user_id (int): The ID of the player.

        Returns:
            str: The drawn card.
        """
        card = self.deck.pop(index)
        if card == "eggsplode":
            if "defuse" in self.hands[self.current_player_id]:
                self.hands[self.current_player_id].remove("defuse")
                self.next_turn()
            else:
                self.remove_player(self.current_player_id)
                self.draw_in_turn = 0
                if len(self.players) == 1:
                    return "gameover"
        elif card == "radioeggtive":
            self.next_turn()
        elif card == "radioeggtive_face_up":
            self.remove_player(self.current_player_id)
            self.draw_in_turn = 0
            if len(self.players) == 1:
                return "gameover"
        else:
            self.hands[self.current_player_id].append(card)
            self.next_turn()
        return card

    def remove_player(self, user_id: int):
        """
        Removes a player from the game.

        Args:
            user_id (int): The ID of the player to remove.
        """
        del self.players[self.players.index(user_id)]
        del self.hands[user_id]
        self.current_player -= 1
        self.draw_in_turn = 0
        self.next_turn()

    def any_player_has_cards(self) -> bool:
        """
        Checks if any player has cards left.

        Returns:
            bool: True if any player has cards, False otherwise.
        """
        eligible_players = self.players.copy()
        eligible_players.remove(self.current_player_id)
        return any(self.hands[player] for player in eligible_players)

    def card_comes_in(self, card) -> int | None:
        """
        Shows the remaining turns until a card is drawn.

        Args:
            card (str): The card to be drawn

        Returns:
            int: The number of turns until the card is drawn, or -1 if the card is not in the deck
        """
        for i in range(len(self.deck) - 1, -1, -1):
            if self.deck[i] == card:
                return len(self.deck) - 1 - i

    def cards_help(self, user_id: int, template: str = "") -> str:
        """
        Provides help information for the cards in a player's hand.

        Args:
            user_id (int): The ID of the player.
            template (str): The template for formatting the help information.

        Returns:
            str: The formatted help information.
        """
        grouped_hand = self.group_hand(user_id)
        return "\n".join(
            template.format(
                CARDS[card]["emoji"],
                CARDS[card]["title"],
                count,
                CARDS[card]["description"],
            )
            for card, count in grouped_hand.items()
        )


class ActionContext:  # pylint: disable=too-few-public-methods
    """
    Represents the context for an action in the game.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        app,
        game_id: int,
        action_id: int | None = None,
    ):
        """
        Initializes the action context.

        Args:
            app: The application instance.
            game_id (int): The ID of the game.
            action_id (int, optional): The ID of the action.
        """
        self.app = app
        self.games: dict[int, Game] = self.app.games
        self.game_id: int = game_id
        self.game: Game = self.games[game_id]
        if action_id is not None:
            self.action_id: int = action_id
        elif self.game:
            self.action_id: int = self.game.action_id

    def copy(self, **kwargs):
        """
        Creates a copy of the action context with optional overrides.

        Args:
            **kwargs: Optional overrides for the context attributes.

        Returns:
            ActionContext: A new action context with the specified overrides.
        """
        return self.__class__(
            app=kwargs.get("app", self.app),
            game_id=kwargs.get("game_id", self.game_id),
            action_id=kwargs.get("action_id", self.action_id),
        )
