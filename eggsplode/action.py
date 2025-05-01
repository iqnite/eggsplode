"""
Contains the PlayView and TurnView classes which handle the game actions in the Discord bot.
"""

import asyncio
from datetime import datetime, timedelta
import discord

from .cards import base
from .game_logic import Game
from .strings import CARDS, get_message, replace_emojis
from .base_views import BaseView
from .nope import NopeView


def turn_action(func):
    async def wrapper(view, item, interaction: discord.Interaction):
        if not interaction.user:
            raise TypeError("interaction.user is None")
        if interaction.user.id != view.game.current_player_id:
            await interaction.respond(
                get_message("not_your_turn"), ephemeral=True, delete_after=5
            )
            return
        if view.paused:
            await interaction.respond(
                get_message("awaiting_prompt"), ephemeral=True, delete_after=5
            )
            return
        view.game.log.anchor_interaction = interaction
        view.inactivity_count = 0
        return await func(view, item, interaction)

    return wrapper


class TurnView(BaseView):
    def __init__(self, game: Game):
        super().__init__(game)
        self.paused = False
        self.inactivity_count = 0
        self.game.events.turn_start += self.next_turn
        self.game.events.turn_reset += self.resume
        self.game.events.action_start += self.pause
        self.game.events.action_end += self.resume
        self.game.events.game_end += self.pause

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.action_timer()

    async def action_timer(self):
        while (
            datetime.now() - self.game.last_activity
            < timedelta(seconds=self.game.config.get("turn_timeout", 60))
        ) or self.paused:
            await asyncio.sleep(1)
        await self.on_action_timeout()

    def pause(self):
        self.paused = True

    async def resume(self):
        self.game.last_activity = datetime.now()
        self.paused = False
        await self.game.log.temporary(self.game.create_turn_prompt_message(), view=self)

    async def next_turn(self):
        await self.resume()
        async with self:
            pass

    async def on_action_timeout(self):
        assert self.game.log.anchor_interaction is not None
        self.pause()
        self.inactivity_count += 1
        if self.inactivity_count > 5:
            await self.game.log(get_message("game_timeout"))
            await self.game.events.game_end()
            return
        turn_player: int = self.game.current_player_id
        await self.game.log(get_message("timeout"))
        _, hold = await self.game.draw_from(
            self.game.log.anchor_interaction, timed_out=True
        )
        if hold:
            await self.game.log(get_message("user_drew_card").format(turn_player))
        if len(self.game.players) == 1:
            return
        await self.game.events.turn_end()

    @discord.ui.button(label="Draw", style=discord.ButtonStyle.blurple, emoji="🤚")
    @turn_action
    async def draw_callback(self, _, interaction: discord.Interaction):
        await self.game.events.action_start()
        await base.draw_card(self.game, interaction)

    @discord.ui.button(label="Play a card", style=discord.ButtonStyle.green, emoji="🎴")
    @turn_action
    async def play(self, _, interaction: discord.Interaction):
        view = PlayView(self.game)
        await interaction.respond(
            view.create_play_prompt_message(self.game.current_player_id),
            view=view,
            ephemeral=True,
        )
        await self.game.events.turn_reset()


class PlayView(discord.ui.View):
    def __init__(self, game: Game):
        super().__init__(timeout=60)
        self.game = game
        self.action_id = game.action_id
        self.play_card_select = None
        self.create_card_selection()

    async def update(self, interaction: discord.Interaction):
        if not interaction.user:
            return
        self.create_card_selection()
        await interaction.edit(
            content=self.create_play_prompt_message(interaction.user.id),
            view=self,
        )

    def create_play_prompt_message(self, user_id: int) -> str:
        return get_message("play_prompt").format(
            self.game.cards_help(user_id, template=get_message("hand_list"))
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user:
            raise TypeError("interaction.user is None")
        if interaction.user.id != self.game.current_player_id:
            await interaction.edit(
                content=get_message("not_your_turn"), view=None, delete_after=5
            )
            return False
        if self.action_id != self.game.action_id:
            await interaction.edit(
                content=get_message("invalid_turn"), view=None, delete_after=10
            )
            return False
        self.game.action_id += 1
        self.action_id = self.game.action_id
        await self.game.events.action_start()
        self.disable_all_items()
        await interaction.edit(view=self, delete_after=0)
        return True

    def create_card_selection(self):
        if self.play_card_select:
            self.remove_item(self.play_card_select)
        user_cards: dict = self.game.group_hand(
            self.game.current_player_id, usable_only=True
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
                    emoji=replace_emojis(CARDS[card]["emoji"]),
                )
                for card in user_cards
            ],
        )
        self.play_card_select.callback = lambda interaction: self.play_card(
            None, interaction
        )
        self.add_item(self.play_card_select)

    async def play_card(self, _, interaction: discord.Interaction):
        if not (interaction.message and interaction.user and self.play_card_select):
            return
        selected = self.play_card_select.values[0]
        if not isinstance(selected, str):
            raise TypeError("selected is not a str")
        await self.game.events.action_start()
        if CARDS[selected].get("combo", 0) == 1:
            await base.food_combo(self.game, interaction, selected)
        else:
            self.game.current_player_hand.remove(selected)
            if CARDS[selected].get("explicit", False):
                await self.game.play(interaction, selected)
            else:
                async with NopeView(
                    self.game,
                    ok_callback_action=lambda _: self.game.play(interaction, selected),
                ) as view:
                    await self.game.log(
                        get_message("play_card").format(
                            interaction.user.id,
                            CARDS[selected]["emoji"],
                            CARDS[selected]["title"],
                            int((datetime.now() + timedelta(seconds=5)).timestamp()),
                        ),
                        view=view,
                    )
