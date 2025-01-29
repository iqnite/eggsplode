"""
Interactable views.
"""

import asyncio
import random
import discord
from common import MESSAGES, CARDS
from game_logic import ActionContext


class BaseView(discord.ui.View):
    """
    Represents the base view.

    Attributes:
        ctx (ActionContext): The context dictionary.
    """

    def __init__(self, ctx: ActionContext, **kwargs):
        """
        Initializes the BaseView.

        Args:
            ctx (dict): The context dictionary.
        """
        super().__init__(**kwargs, disable_on_timeout=True)
        self.ctx = ctx

    def default_message(self, user_id: int):
        """
        Returns the cards help message.
        """
        return MESSAGES["play_prompt"].format(
            self.ctx.game.cards_help(user_id, template=MESSAGES["hand_list"]),
            len(self.ctx.game.deck),
            self.ctx.game.deck.count("eggsplode"),
        )


class TurnView(BaseView):
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
        super().__init__(ctx, timeout=600)
        self.timer: int

    async def action_timer(self):
        """
        Controls the action timeout.
        """
        self.timer = 0
        while self.timer < 60:
            await asyncio.sleep(1)
            if self.timer < 0:
                return
            if not self.ctx.game.awaiting_prompt:
                self.timer += 1
        await self.on_action_timeout()

    def stop_timer(self):
        """
        Stops the action timer.
        """
        self.timer = -2

    async def on_action_timeout(self):
        """
        Handles the action timeout event.
        """
        if not isinstance(self.ctx.parent_interaction, discord.Interaction):
            raise TypeError("parent_interaction is not a discord.Interaction")
        turn_player: int = self.ctx.game.current_player_id
        card: str = self.ctx.game.draw_card(turn_player)
        caught = None
        for _ in range(5):
            try:
                match card:
                    case "defuse":
                        await self.ctx.parent_interaction.respond(
                            MESSAGES["timeout"]
                            + MESSAGES["defused"].format(turn_player)
                        )
                    case "eggsplode":
                        await self.ctx.parent_interaction.respond(
                            MESSAGES["timeout"]
                            + MESSAGES["eggsploded"].format(turn_player)
                        )
                    case "gameover":
                        await self.ctx.parent_interaction.respond(
                            MESSAGES["timeout"]
                            + MESSAGES["eggsploded"].format(turn_player)
                        )
                        await self.ctx.parent_interaction.respond(
                            MESSAGES["game_over"].format(self.ctx.game.players[0])
                        )
                        del self.ctx.games[self.ctx.game_id]
                        return
                    case _:
                        await self.ctx.parent_interaction.respond(
                            MESSAGES["timeout"]
                            + MESSAGES["user_drew_card"].format(turn_player)
                        )
                view = TurnView(self.ctx.copy())
                view.message = self.message
                await self.ctx.parent_interaction.respond(
                    MESSAGES["next_turn"].format(self.ctx.game.current_player_id),
                    view=view,
                )
            except (discord.errors.NotFound, AttributeError) as e:
                caught = e
                continue
            else:
                await view.action_timer()
                break
        else:
            if caught:
                raise caught

    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user:
            return False
        if interaction.user.id != self.ctx.game.current_player_id:
            self.disable_all_items()
            await interaction.edit(view=self)
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return False
        if self.timer < 0:
            self.disable_all_items()
            await interaction.edit(view=self)
            await interaction.respond(MESSAGES["invalid_turn"], ephemeral=True)
            return False
        self.timer = 0
        return True

    @discord.ui.button(label="Play!", style=discord.ButtonStyle.blurple, emoji="🤚")
    async def play(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the Play button click event.

        Args:
            _ (discord.ui.Button): The button instance.
            interaction (discord.Interaction): The interaction instance.
        """
        if not interaction.user:
            return
        self.ctx.action_id = self.ctx.game.action_id
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
        await interaction.respond(
            self.default_message(interaction.user.id),
            view=view,
            ephemeral=True,
        )


class PlayView(BaseView):
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
        super().__init__(ctx)
        self.play_card_select = None

    async def create_view(self):
        """
        Creates the card selection view.
        """
        if not isinstance(self.ctx.parent_interaction, discord.Interaction):
            raise TypeError("parent_interaction is not a discord.Interaction")
        self.create_card_selection(self.ctx.parent_interaction)

    async def interaction_check(self, interaction: discord.Interaction):
        """
        Checks if the interaction is valid.

        Args:
            interaction (discord.Interaction): The interaction instance.

        Returns:
            bool: Whether the interaction is valid.
        """

        if not interaction.user:
            raise TypeError("interaction.user is None")
        if not isinstance(self.ctx.parent_view, TurnView):
            raise TypeError("parent_view is not a TurnView")
        if self.ctx.game.awaiting_prompt:
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return False
        if interaction.user.id != self.ctx.game.current_player_id:
            self.disable_all_items()
            await interaction.edit(view=self)
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return False
        if self.ctx.action_id != self.ctx.game.action_id:
            self.disable_all_items()
            await interaction.edit(view=self)
            await interaction.respond(MESSAGES["invalid_turn"], ephemeral=True)
            return False
        self.ctx.game.action_id += 1
        self.ctx.action_id += 1
        self.ctx.parent_view.timer = 0
        return True

    async def end_turn(self, interaction: discord.Interaction):
        """
        Ends the player's turn.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        if not isinstance(self.ctx.parent_view, TurnView):
            raise TypeError("parent_view is not a TurnView")
        if not isinstance(self.ctx.parent_interaction, discord.Interaction):
            raise TypeError("parent_interaction is not a discord.Interaction")
        self.ctx.parent_view.stop_timer()
        self.ctx.parent_view.disable_all_items()
        await self.ctx.parent_interaction.edit(view=self.ctx.parent_view)
        view = TurnView(self.ctx.copy(parent_interaction=interaction, parent_view=self))
        view.message = await interaction.respond(
            MESSAGES["next_turn"].format(self.ctx.game.current_player_id), view=view
        )
        await view.action_timer()

    def create_card_selection(self, interaction: discord.Interaction):
        """
        Creates the card selection dropdown.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        if self.play_card_select:
            self.remove_item(self.play_card_select)
        if not interaction.user:
            return
        user_cards: dict = self.ctx.game.group_hand(
            interaction.user.id, usable_only=True
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
        if not interaction.user:
            return
        self.disable_all_items()
        await interaction.edit(view=self)
        card: str = self.ctx.game.draw_card(interaction.user.id)
        match card:
            case "defuse":
                await interaction.respond(
                    MESSAGES["defused"].format(interaction.user.id)
                )
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
                if isinstance(self.ctx.parent_view, TurnView):
                    self.ctx.parent_view.stop_timer()
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
        Plays a selected card.

        Args:
            interaction (discord.Interaction): The interaction instance.
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
        self.create_card_selection(interaction)
        await interaction.edit(view=self)

    async def attegg(self, interaction: discord.Interaction):
        """
        Begins the attegg action.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        if not interaction.user:
            return
        await interaction.respond(
            MESSAGES["before_attegg"].format(
                interaction.user.id, self.ctx.game.next_player_id
            ),
            view=NopeView(
                ctx=self.ctx.copy(parent_interaction=interaction, parent_view=self),
                target_player_id=self.ctx.game.next_player_id,
                callback_action=lambda _: self.finalize_attegg(interaction),
            ),
        )

    async def skip(self, interaction: discord.Interaction):
        """
        Begins the skip action.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        if not interaction.user:
            return
        await interaction.respond(
            MESSAGES["before_skip"].format(
                interaction.user.id,
                (
                    self.ctx.game.next_player_id
                    if self.ctx.game.atteggs == 0
                    else interaction.user.id
                ),
            ),
            view=NopeView(
                ctx=self.ctx.copy(parent_interaction=interaction, parent_view=self),
                target_player_id=(
                    self.ctx.game.next_player_id
                    if self.ctx.game.atteggs == 0
                    else interaction.user.id
                ),
                callback_action=lambda _: self.finalize_skip(interaction),
            ),
        )

    async def shuffle(self, interaction: discord.Interaction):
        """
        Begins the shuffle action.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        random.shuffle(self.ctx.game.deck)
        if not interaction.user:
            return
        await interaction.respond(
            MESSAGES["shuffled"].format(interaction.user.id),
        )

    async def predict(self, interaction: discord.Interaction):
        """
        Begins the predict action.

        Args:
            interaction (discord.Interaction): The interaction instance.
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
        Begins the food combo action.

        Args:
            interaction (discord.Interaction): The interaction instance.
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
            view = ChoosePlayerView(
                self.ctx.copy(parent_interaction=interaction, parent_view=self),
                lambda target_player_id: self.begin_steal(
                    interaction, target_player_id, selected
                ),
            )
            await view.create_user_selection()
            await interaction.respond(
                MESSAGES["steal_prompt"], view=view, ephemeral=True
            )

    async def begin_steal(
        self, interaction: discord.Interaction, target_player_id: int, food_card: str
    ):
        """
        Begins the steal action.

        Args:
            interaction (discord.Interaction): The interaction instance.
            target_player_id (int): The target player ID.
        """
        if not interaction.user:
            return
        await interaction.respond(
            MESSAGES["before_steal"].format(
                CARDS[food_card]["emoji"], interaction.user.id, target_player_id
            ),
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
        if not interaction.user:
            return
        target_hand = self.ctx.game.hands[target_player_id]
        stolen_card = random.choice(target_hand)
        self.ctx.game.hands[target_player_id].remove(stolen_card)
        self.ctx.game.current_player_hand.append(stolen_card)
        self.create_card_selection(interaction)
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

    async def finalize_attegg(self, interaction: discord.Interaction):
        """
        Finalizes the attegg action.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        if not interaction.message:
            return
        self.disable_all_items()
        await interaction.edit(view=self)
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


class NopeView(BaseView):
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
        super().__init__(ctx, timeout=10)
        self.target_player = target_player_id
        self.callback_action = callback_action
        self.nopes = 0
        self.ctx.game.awaiting_prompt = True
        if not isinstance(self.ctx.parent_interaction, discord.Interaction):
            raise TypeError("parent_interaction is not a discord.Interaction")
        if not self.ctx.parent_interaction.user:
            raise TypeError("parent_interaction.user is None")

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        if self.ctx.action_id == self.ctx.game.action_id:
            self.ctx.game.awaiting_prompt = False
            if not self.nopes % 2 and self.callback_action:
                await self.callback_action(None)
        await super().on_timeout()

    @discord.ui.button(label="OK!", style=discord.ButtonStyle.green, emoji="✅")
    async def ok_callback(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the OK button click event.

        Args:
            _ (discord.ui.Button): The button instance.
            interaction (discord.Interaction): The interaction instance.
        """
        if not (interaction.user and self.ctx.parent_interaction):
            return
        if not isinstance(self.ctx.parent_interaction, discord.Interaction):
            raise TypeError("parent_interaction is not a discord.Interaction")
        if interaction.user.id != self.target_player:
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return
        if self.nopes % 2:
            await interaction.respond(MESSAGES["action_noped"], ephemeral=True)
            return
        self.on_timeout = super().on_timeout
        self.ctx.game.awaiting_prompt = False
        self.disable_all_items()
        await interaction.edit(view=self)
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
        if not isinstance(self.ctx.parent_interaction, discord.Interaction):
            raise TypeError("parent_interaction is not a discord.Interaction")
        if not (interaction.user and self.ctx.parent_interaction.user):
            return
        if (
            not self.nopes % 2
            and self.ctx.parent_interaction.user.id == interaction.user.id
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


class ChoosePlayerView(BaseView):
    """
    Represents the view to select a user.
    """

    def __init__(self, ctx: ActionContext, callback_action):
        """
        Initializes the ChoosePlayerView.
        """
        super().__init__(ctx, timeout=10)
        self.eligible_players = self.ctx.game.players.copy()
        self.eligible_players.remove(self.ctx.game.current_player_id)
        self.callback_action = callback_action
        self.ctx.game.awaiting_prompt = True
        self.user_select = None

    async def on_timeout(self):
        self.ctx.game.awaiting_prompt = False
        if not self.user_select:
            return
        await self.callback_action(int(self.user_select.options[0].value))
        await super().on_timeout()

    async def create_user_selection(self):
        """
        Creates the user selection dropdown.

        Args:
            interaction (discord.Interaction): The interaction instance.
        """
        options = []
        for user_id in self.eligible_players:
            user = await self.ctx.app.get_or_fetch_user(user_id)
            if not user:
                continue
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
        if not (interaction and self.user_select):
            return
        self.on_timeout = super().on_timeout
        self.ctx.game.awaiting_prompt = False
        self.disable_all_items()
        await interaction.edit(view=self)
        if not isinstance(self.user_select.values[0], str):
            raise TypeError("user_select.values[0] is not a str")
        await self.callback_action(int(self.user_select.values[0]))


class StartGameView(BaseView):
    """
    Represents the view for starting a game.

    Attributes:
        app (Eggsplode): The Eggsplode bot instance.
        game_id (int): The game ID.
    """

    def __init__(self, ctx: ActionContext):
        """
        Initializes the StartGameView.

        Args:
            app (Eggsplode): The Eggsplode bot instance.
            game_id (int): The game ID.
        """
        super().__init__(ctx, timeout=600)

    async def on_timeout(self):
        """
        Handles the timeout event.
        """
        del self.ctx.games[self.ctx.game_id]
        await super().on_timeout()

    @discord.ui.button(label="Join", style=discord.ButtonStyle.blurple, emoji="👋")
    async def join_game(self, _: discord.ui.Button, interaction: discord.Interaction):
        """
        Handles the Join button click event.

        Args:
            _ (discord.ui.Button): The button instance.
            interaction (discord.Interaction): The interaction instance.
        """
        if not interaction.user:
            return
        if interaction.user.id in self.ctx.game.players:
            await interaction.respond(MESSAGES["already_in_game"], ephemeral=True)
            return
        self.ctx.game.players.append(interaction.user.id)
        if not (interaction.message and interaction.message.content):
            return
        await interaction.edit(
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
        if not interaction.user:
            return
        if interaction.user.id != self.ctx.game.players[0]:
            await interaction.respond(
                MESSAGES["not_game_creator_start"], ephemeral=True
            )
            return
        if len(self.ctx.game.players) < 2:
            await interaction.respond(
                MESSAGES["not_enough_players_to_start"], ephemeral=True
            )
            return
        self.on_timeout = super().on_timeout
        self.ctx.game.start()
        self.disable_all_items()
        await interaction.edit(view=self)
        await interaction.respond(MESSAGES["game_started"], ephemeral=True)
        view = TurnView(self.ctx.copy(parent_interaction=interaction, parent_view=self))
        view.message = await interaction.respond(
            MESSAGES["next_turn"].format(self.ctx.game.current_player_id), view=view
        )
        await view.action_timer()
