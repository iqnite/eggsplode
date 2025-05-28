"""
Contains commands for the main Eggsplode game.
"""

import discord
from discord.ext import commands
from eggsplode.commands import EggsplodeApp
from eggsplode.core import Game
from eggsplode.strings import CARDS, get_card_by_title, get_message
from eggsplode.ui import EndGameView


class EggsplodeGame(commands.Cog):
    def __init__(self, app: EggsplodeApp):
        self.app = app

    async def get_game(
        self, interaction: discord.Interaction, quiet: bool = False
    ) -> Game | None:
        game_id = interaction.channel_id
        if not (game_id and interaction.user):
            return None
        if (
            game_id not in self.app.games
            or (game := self.app.games[game_id]) is None
            or not game.running
        ):
            if not quiet:
                await interaction.respond(get_message("game_not_found"), ephemeral=True)
            return None
        if interaction.user.id not in game.players + game.config.get("players", []):
            if not quiet:
                await interaction.respond(
                    get_message("user_not_in_game"), ephemeral=True
                )
            return None
        if not game.hands:
            if not quiet:
                await interaction.respond(
                    get_message("game_not_started"), ephemeral=True
                )
            return None
        return game

    @discord.slash_command(
        name="start",
        description="Start a new Eggsplode game!",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def start_game(self, ctx: discord.ApplicationContext):
        await self.app.create_game(ctx.interaction)

    @discord.slash_command(
        name="draw",
        description="Draw a card from the deck.",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def draw_card(self, ctx: discord.ApplicationContext):
        game = await self.get_game(ctx.interaction)
        if game is None:
            return
        await game.draw_callback(ctx.interaction)

    async def card_autocomplete(self, ctx: discord.AutocompleteContext) -> list[str]:
        user = ctx.interaction.user
        if not user or not user.id:
            return []
        game = await self.get_game(ctx.interaction, quiet=True)
        if game is None:
            return []
        if not game.hands or user.id not in game.hands:
            return []
        hand = game.group_hand(user.id, usable_only=True)
        return [
            card_title + f" ({count}x)"
            for card, count in hand.items()
            if ctx.value.lower() in (card_title := CARDS[card]["title"]).lower()
        ]

    @discord.slash_command(
        name="play",
        description="Play a card from your hand.",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    @discord.option(
        name="card",
        description="The card to play.",
        input_type=str,
        required=False,
        autocomplete=card_autocomplete,
    )
    async def play_card(self, ctx: discord.ApplicationContext, card: str | None = None):
        if not ctx.interaction.user:
            raise ValueError("interaction.user is None")
        game = await self.get_game(ctx.interaction)
        if game is None:
            return
        if card:
            try:
                card = get_card_by_title(card.split(" (")[0], match_case=False)
                if card not in game.hands.get(ctx.interaction.user.id, []):
                    raise ValueError("Card not in hand")
            except ValueError:
                await ctx.respond(
                    get_message("card_not_found").format(card), ephemeral=True
                )
                return
            game.anchor_interaction = ctx.interaction
            await game.play_callback(ctx.interaction, card)
        else:
            await game.show_hand(ctx.interaction)

    @discord.slash_command(
        name="games",
        description="View which games you're in.",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def list_user_games(self, ctx: discord.ApplicationContext):
        self.app.cleanup()
        if not ctx.interaction.user:
            return
        found_games = self.app.games_with_user(ctx.interaction.user.id)
        await ctx.respond(
            (
                get_message("list_games_title").format(
                    "\n".join(
                        get_message("list_games_item").format(i) for i in found_games
                    )
                )
                if found_games
                else get_message("user_not_in_any_games")
            ),
            ephemeral=True,
        )

    @discord.slash_command(
        name="end",
        description="End the current Eggsplode game.",
        integration_types={discord.IntegrationType.guild_install},
    )
    @discord.default_permissions(manage_messages=True)
    async def end_game(self, ctx: discord.ApplicationContext):
        game_id = ctx.interaction.channel_id
        if not (game_id and ctx.interaction.user):
            return
        if (
            game_id not in self.app.games
            or (game := self.app.games[game_id]) is None
            or not game.running
        ):
            await ctx.respond(get_message("game_not_found"), ephemeral=True)
            return
        if game is None or not ctx.interaction.user:
            return
        view = EndGameView(game, ctx.interaction.user.id)
        await ctx.respond(view=view, ephemeral=True)


def setup(bot: EggsplodeApp):
    bot.add_cog(EggsplodeGame(bot))
