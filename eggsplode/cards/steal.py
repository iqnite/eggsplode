"""
Contains effects for cards that steal from other players.
"""

import random
from typing import TYPE_CHECKING
import discord
from eggsplode.strings import available_cards, format_message, replace_emojis, tooltip
from eggsplode.ui import ChoosePlayerView, ChooseCardView, NopeView, TextView

if TYPE_CHECKING:
    from eggsplode.core import Game


async def begg(game: "Game", interaction: discord.Interaction):
    view = ChoosePlayerView(
        game,
        lambda target_player_id: begg_begin(game, interaction, target_player_id),
        condition=lambda user_id: user_id != game.current_player_id
        and len(game.hands[user_id]) > 0,
    )
    if await view.skip_if_single_option():
        return
    await view.create_user_selection()
    await interaction.respond(view=view, ephemeral=True)


async def begg_begin(
    game: "Game", interaction: discord.Interaction, target_player_id: int
):
    view = NopeView(
        game,
        message=format_message(
            "before_begg",
            game.current_player_id,
            target_player_id,
        ),
        target_player_id=target_player_id,
        ok_callback_action=lambda target_interaction: begg_ask_card(
            game, interaction, target_interaction, target_player_id
        ),
    )
    await game.send(view, interaction)
    await view.start_timer(interaction)


async def begg_ask_card(
    game: "Game",
    interaction: discord.Interaction,
    target_interaction: discord.Interaction | None,
    target_player_id: int,
):
    target_hand = game.hands[target_player_id]
    if not target_hand:
        await game.send(
            TextView("no_cards_to_steal", game.current_player_id, target_player_id),
            interaction,
        )
        await game.events.action_end()
        return
    if not target_interaction:
        # If the target player doesn't respond in time, steal a random card
        await steal_finish(
            game, interaction, None, target_player_id, text_variant="_begg_timeout"
        )
        return
    view = ChooseCardView(
        game,
        target_player_id,
        lambda cards: begg_finish(game, interaction, target_player_id, cards[0]),
        text=format_message("begg_prompt", game.current_player_id),
    )
    await view.create_card_selection()
    await target_interaction.respond(view=view, ephemeral=True)


async def begg_finish(
    game, interaction: discord.Interaction, target_player_id: int, card: str
):
    game.hands[target_player_id].remove(card)
    game.current_player_hand.append(card)
    await game.send(
        TextView("begg_success", target_player_id, game.current_player_id),
        interaction,
    )
    try:
        await interaction.respond(
            view=TextView(
                "begg_success_you",
                tooltip(card),
                game.current_player_hand.count(card),
            ),
            ephemeral=True,
        )
    finally:
        await game.events.action_end()


async def steal_finish(
    game: "Game",
    interaction: discord.Interaction,
    target_interaction: discord.Interaction | None,
    target_player_id: int,
    text_variant: str = "",
    cards_to_restore: list[str] | None = None,
):
    target_hand = game.hands[target_player_id]
    if not target_hand:
        await game.send(
            TextView("no_cards_to_steal", game.current_player_id, target_player_id),
            interaction,
        )
        await game.events.action_end()
        return
    stolen_card = random.choice(target_hand)
    game.hands[target_player_id].remove(stolen_card)
    game.current_player_hand.append(stolen_card)
    if cards_to_restore:
        for card in cards_to_restore:
            target_hand.append(card)
    await game.send(
        TextView(
            f"stolen_card_public{text_variant}",
            action_player=game.current_player_id,
            target_player=target_player_id,
        ),
        interaction,
    )
    try:
        await interaction.respond(
            view=TextView(
                "stolen_card_you",
                tooltip(stolen_card),
                game.current_player_hand.count(stolen_card),
            ),
            ephemeral=True,
        )
        if target_interaction:
            await target_interaction.respond(
                view=TextView(
                    "stolen_card_them",
                    game.current_player_id,
                    tooltip(stolen_card),
                    target_hand.count(stolen_card),
                ),
                ephemeral=True,
            )
    finally:
        await game.events.action_end()


async def food_combo_begin(
    game: "Game",
    interaction: discord.Interaction,
    target_player_id: int,
    food_card: str,
):
    view = NopeView(
        game,
        message=format_message(
            "before_steal",
            replace_emojis(available_cards[food_card]["emoji"]),
            game.current_player_id,
            target_player_id,
        ),
        target_player_id=target_player_id,
        ok_callback_action=lambda target_interaction: steal_finish(
            game, interaction, target_interaction, target_player_id
        ),
    )
    await game.send(view, interaction)
    await view.start_timer(interaction)


async def food_combo(
    game: "Game", interaction: discord.Interaction, card: str = "steal"
):
    if card != "steal":
        if card in game.current_player_hand:
            game.current_player_hand.remove(card)
        else:
            await interaction.respond(
                view=TextView("card_not_found", card),
                ephemeral=True,
                delete_after=10,
            )
            return
    view = ChoosePlayerView(
        game,
        lambda target_player_id: food_combo_begin(
            game, interaction, target_player_id, card
        ),
        condition=lambda user_id: user_id != game.current_player_id
        and len(game.hands[user_id]) > 0,
    )
    if await view.skip_if_single_option():
        return
    await view.create_user_selection()
    await interaction.respond(view=view, ephemeral=True)


async def trade(game: "Game", interaction: discord.Interaction):
    view = ChoosePlayerView(
        game,
        lambda target_player_id: trade_begin(game, interaction, target_player_id),
        condition=lambda user_id: user_id != game.current_player_id
        and len(game.hands[user_id]) > 0,
    )
    if await view.skip_if_single_option():
        return
    await view.create_user_selection()
    await interaction.respond(view=view, ephemeral=True)


async def trade_begin(
    game: "Game", interaction: discord.Interaction, target_player_id: int
):
    view = NopeView(
        game,
        message=format_message(
            "before_trade",
            game.current_player_id,
            target_player_id,
        ),
        target_player_id=target_player_id,
        ok_callback_action=lambda target_interaction: trade_choose_card(
            game, interaction, target_interaction, target_player_id
        ),
    )
    await game.send(view, interaction)
    await view.start_timer(interaction)


async def trade_choose_card(
    game: "Game",
    interaction: discord.Interaction,
    target_interaction: discord.Interaction | None,
    target_player_id: int,
):
    target_hand = game.hands[target_player_id]
    if not target_hand:
        await game.send(
            TextView("no_cards_to_steal", game.current_player_id, target_player_id),
            interaction,
        )
        await game.events.action_end()
        return
    stolen_card = random.choice(target_hand)
    game.hands[target_player_id].remove(stolen_card)
    game.current_player_hand.append(stolen_card)
    if target_interaction:
        await target_interaction.respond(
            view=TextView(
                "stolen_card_them_trade",
                game.current_player_id,
                tooltip(stolen_card),
                target_hand.count(stolen_card),
            ),
            ephemeral=True,
        )
    view = ChooseCardView(
        game,
        game.current_player_id,
        lambda cards: trade_finish(game, interaction, target_player_id, cards[0]),
        text=format_message(
            "choose_card_to_trade", tooltip(stolen_card), target_player_id
        ),
    )
    await view.create_card_selection()
    await interaction.respond(view=view, ephemeral=True)


async def trade_finish(
    game: "Game",
    interaction: discord.Interaction,
    target_player_id: int,
    card_to_give: str,
):
    game.current_player_hand.remove(card_to_give)
    game.hands[target_player_id].append(card_to_give)
    try:
        await interaction.respond(
            view=TradeFinishedView(game, target_player_id, card_to_give),
        )
    finally:
        await game.events.action_end()


class TradeFinishedView(discord.ui.DesignerView):
    def __init__(self, game: "Game", target_player_id: int, card_given: str):
        super().__init__(timeout=None)
        self.game = game
        self.target_player_id = target_player_id
        self.card_given = card_given
        self.add_item(
            discord.ui.TextDisplay(
                format_message(
                    "trade_success", game.current_player_id, target_player_id
                )
            )
        )
        self.view_button = discord.ui.Button(
            label=format_message("view_traded_cards_button"),
            style=discord.ButtonStyle.primary,
            emoji="👀",
        )
        self.view_button.callback = self.view_card
        self.add_item(discord.ui.ActionRow(self.view_button))

    async def view_card(self, interaction: discord.Interaction):
        if not interaction.user:
            return
        if interaction.user.id != self.target_player_id:
            await interaction.respond(
                view=TextView("not_allowed_to_view_cards"), ephemeral=True
            )
            return
        await interaction.respond(
            view=TextView(
                "traded_card_them",
                tooltip(self.card_given),
                self.game.hands[self.target_player_id].count(self.card_given),
            ),
            ephemeral=True,
        )


async def raid(game: "Game", interaction: discord.Interaction):
    view = ChoosePlayerView(
        game,
        lambda target_player_id: raid_begin(game, interaction, target_player_id),
        condition=lambda user_id: user_id != game.current_player_id
        and len(game.hands[user_id]) >= 3,
    )
    if await view.skip_if_single_option():
        return
    await view.create_user_selection()
    await interaction.respond(view=view, ephemeral=True)


async def raid_begin(
    game: "Game", interaction: discord.Interaction, target_player_id: int
):
    view = NopeView(
        game,
        message=format_message(
            "before_raid",
            game.current_player_id,
            target_player_id,
        ),
        target_player_id=target_player_id,
        ok_callback_action=lambda target_interaction: raid_choose_cards(
            game, interaction, target_interaction, target_player_id
        ),
    )
    await game.send(view, interaction)
    await view.start_timer(interaction)


async def raid_choose_cards(
    game: "Game",
    interaction: discord.Interaction,
    target_interaction: discord.Interaction | None,
    target_player_id: int,
    hidden_cards: list[str] | None = None,
):
    if hidden_cards is None:
        hidden_cards = []
    target_hand = game.hands[target_player_id]
    if len(target_hand) < 3 - len(hidden_cards):
        # Cancel the raid if the target player doesn't have enough cards left to hide
        await game.send(
            TextView("no_cards_to_steal", game.current_player_id, target_player_id),
            interaction,
        )
        await game.events.action_end()
        return
    if hidden_cards:
        target_hand.remove(hidden_cards[-1])
    if len(hidden_cards) >= 2 or not target_interaction:
        await steal_finish(
            game,
            interaction,
            target_interaction=target_interaction,
            target_player_id=target_player_id,
            text_variant="" if target_interaction else "_raid_timeout",
            cards_to_restore=hidden_cards,
        )
        return
    view = ChooseCardView(
        game,
        target_player_id,
        lambda cards: raid_choose_cards(
            game,
            interaction,
            target_interaction,
            target_player_id,
            hidden_cards + cards,
        ),
        text=format_message(
            "raid_prompt", len(hidden_cards) + 1, game.current_player_id
        ),
    )
    await view.create_card_selection()
    await target_interaction.respond(view=view, ephemeral=True)
