"""
Contains the PlayView and TurnView classes which handle the game actions in the Discord bot.
"""

import asyncio
from collections.abc import Callable, Coroutine
import random
import discord


from .. import cards
from ..ctx import ActionContext, PlayActionContext
from ..strings import CARDS, MESSAGES
from ..views.short import NopeView
from .base import BaseView


class TurnView(BaseView):
    def __init__(
        self,
        ctx: ActionContext,
        parent_interaction: discord.Interaction,
        inactivity_count: int = 0,
    ):
        super().__init__(ctx, timeout=None)
        self.timer: int | None = 0
        self.inactivity_count = inactivity_count
        self.parent_interaction = parent_interaction

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.action_timer()

    async def action_timer(self):
        if self.timer is None:
            return
        self.start_timer()
        try:
            while self.timer < int(self.ctx.game.config.get("turn_timeout", 60)):
                await asyncio.sleep(1)
                if self.timer is None:
                    return
                if self.ctx.game.awaiting_prompt:
                    continue
                self.timer += 1
        except TypeError as e:
            # Log the error for debugging purposes
            print(f"TypeError encountered in action_timer: {e}")
            return
        await self.on_action_timeout()

    def deactivate(self):
        # None is used to represent a deactivated timer
        self.timer = None

    def start_timer(self):
        if self.timer is None:
            return
        self.timer = 0

    async def on_action_timeout(self):
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
            case "defused":
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
        response += "\n" + self.create_turn_prompt_message()
        self.ctx.game.action_id += 1
        async with TurnView(
            self.ctx.copy(action_id=self.ctx.game.action_id),
            parent_interaction=self.parent_interaction,
            inactivity_count=self.inactivity_count + 1,
        ) as view:
            await self.parent_interaction.respond(response, view=view)

    def create_turn_prompt_message(self) -> str:
        return MESSAGES["next_turn"].format(
            self.ctx.game.current_player_id,
            len(self.ctx.game.deck),
            self.ctx.game.deck.count("eggsplode"),
        ) + ("\n" + cards.radioeggtive_warning(self.ctx))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user:
            return False
        if interaction.user.id != self.ctx.game.current_player_id:
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return False
        if self.timer is None or self.timer < 0:
            self.disable_all_items()
            await interaction.edit(view=self)
            await interaction.respond(MESSAGES["invalid_turn"], ephemeral=True)
            return False
        self.start_timer()
        return True

    @discord.ui.button(label="Play!", style=discord.ButtonStyle.blurple, emoji="🤚")
    async def play(self, _: discord.ui.Button, interaction: discord.Interaction):
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
        self.deactivate()
        self.ctx.game.action_id += 1
        async with TurnView(
            self.ctx.copy(action_id=self.ctx.game.action_id),
            parent_interaction=interaction,
        ) as view:
            await interaction.respond(view.create_turn_prompt_message(), view=view)


class PlayView(BaseView):
    def __init__(
        self,
        ctx: ActionContext,
        *,
        on_valid_interaction: Callable[[discord.Interaction], None],
        end_turn: Callable[[discord.Interaction], Coroutine],
        on_game_over: Callable[[], None],
    ):
        super().__init__(ctx)
        self.ctx = PlayActionContext.from_ctx(
            ctx=ctx,
            disable_view=self.deactivate,
            update_view=self.update,
            end_turn=end_turn,
            on_game_over=on_game_over,
        )
        self.play_card_select = None
        self.on_valid_interaction = on_valid_interaction
        self.end_turn = end_turn
        self.on_game_over = on_game_over
        self.create_card_selection()

    async def deactivate(self, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.edit(view=self)

    async def update(self, interaction: discord.Interaction):
        if not interaction.user:
            return
        self.create_card_selection()
        await interaction.edit(
            content=self.create_play_prompt_message(interaction.user.id),
            view=self,
        )

    def create_play_prompt_message(self, user_id: int) -> str:
        return MESSAGES["play_prompt"].format(
            self.ctx.game.cards_help(user_id, template=MESSAGES["hand_list"])
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user:
            raise TypeError("interaction.user is None")
        if self.ctx.game.awaiting_prompt:
            await interaction.respond(MESSAGES["awaiting_prompt"], ephemeral=True)
            return False
        if interaction.user.id != self.ctx.game.current_player_id:
            await interaction.respond(MESSAGES["not_your_turn"], ephemeral=True)
            return False
        if self.ctx.action_id != self.ctx.game.action_id:
            await interaction.respond(MESSAGES["invalid_turn"], ephemeral=True)
            return False
        self.ctx.game.action_id += 1
        self.ctx.action_id = self.ctx.game.action_id
        self.on_valid_interaction(interaction)
        return True

    def create_card_selection(self):
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
        await cards.draw_card(self.ctx, interaction)

    async def play_card(self, _, interaction: discord.Interaction):
        if not (interaction.message and interaction.user and self.play_card_select):
            return
        selected = self.play_card_select.values[0]
        if not isinstance(selected, str):
            raise TypeError("selected is not a str")
        await interaction.edit(view=self)
        if CARDS[selected].get("combo", 0) == 1:
            await cards.food_combo(self.ctx.copy(view=self), interaction, selected)
        else:
            self.ctx.game.current_player_hand.remove(selected)
            if CARDS[selected].get("explicit", False):
                await self.CARD_ACTIONS[selected](self.ctx.copy(view=self), interaction)
            else:
                async with NopeView(
                    self.ctx.copy(view=self),
                    ok_callback_action=lambda _: self.CARD_ACTIONS[selected](
                        self.ctx.copy(view=self), interaction
                    ),
                ) as view:
                    await interaction.respond(
                        MESSAGES["play_card"].format(
                            interaction.user.id,
                            CARDS[selected]["emoji"],
                            CARDS[selected]["title"],
                        ),
                        view=view,
                    )
        self.create_card_selection()
        await interaction.edit(
            content=self.create_play_prompt_message(interaction.user.id),
            view=self,
        )

    CARD_ACTIONS = {
        "attegg": cards.attegg,
        "skip": cards.skip,
        "shuffle": cards.shuffle,
        "predict": cards.predict,
        "draw_from_bottom": cards.draw_from_bottom,
        "targeted_attegg": cards.targeted_attegg,
        "alter_future": cards.alter_future,
        "reverse": cards.reverse,
    }
