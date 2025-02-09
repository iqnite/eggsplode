"""
Contains the TurnView class, which handles the turn-based interactions
for the game, including timers and user interactions.
"""

import asyncio
import random
import discord
from strings import MESSAGES
from game_logic import ActionContext
from .base_view import BaseView
from .play_view import PlayView


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
        while self.timer < 60:
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
        card: str = self.ctx.game.draw_card(turn_player)
        caught = None
        for _ in range(5):
            try:
                match card:
                    case "defuse":
                        self.ctx.game.deck.insert(
                            random.randint(0, len(self.ctx.game.deck)), "eggsplode"
                        )
                        await self.parent_interaction.respond(
                            MESSAGES["timeout"]
                            + MESSAGES["defused"].format(turn_player)
                        )
                    case "eggsplode":
                        await self.parent_interaction.respond(
                            MESSAGES["timeout"]
                            + MESSAGES["eggsploded"].format(turn_player)
                        )
                    case "gameover":
                        await self.parent_interaction.respond(
                            MESSAGES["timeout"]
                            + MESSAGES["eggsploded"].format(turn_player)
                        )
                        await self.parent_interaction.respond(
                            MESSAGES["game_over"].format(self.ctx.game.players[0])
                        )
                        del self.ctx.games[self.ctx.game_id]
                        return
                    case _:
                        await self.parent_interaction.respond(
                            MESSAGES["timeout"]
                            + MESSAGES["user_drew_card"].format(turn_player)
                        )
                async with TurnView(
                    self.ctx.copy(),
                    parent_interaction=self.parent_interaction,
                    inactivity_count=self.inactivity_count + 1,
                ) as view:
                    await self.parent_interaction.respond(
                        MESSAGES["next_turn"].format(self.ctx.game.current_player_id),
                        view=view,
                    )
            except (discord.errors.NotFound, AttributeError) as e:
                caught = e
                continue
            else:
                break
        else:
            if caught:
                raise caught

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
                self.default_message(interaction.user.id),
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
