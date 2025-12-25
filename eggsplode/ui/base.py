"""
Contains the BaseView class for the Eggsplode game.
"""

from typing import TYPE_CHECKING
import discord

from eggsplode.strings import format_message

if TYPE_CHECKING:
    from eggsplode.core import Game


class BaseView(discord.ui.DesignerView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_ignoring_interactions = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return (
            await super().interaction_check(interaction)
            and not self.is_ignoring_interactions
        )

    def ignore_interactions(self):
        self.is_ignoring_interactions = True

    def allow_interactions(self):
        self.is_ignoring_interactions = False


class BaseGameView(BaseView):
    def __init__(self, game: "Game", timeout=None):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.game = game
        self.game.events.game_end += self.ignore_interactions

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await super().interaction_check(interaction):
            return False
        if interaction.user is None or interaction.user.id not in self.game.players:
            await interaction.respond(
                format_message("user_not_in_game"), ephemeral=True
            )
            return False
        await interaction.response.defer(invisible=True)
        return True


class TextView(discord.ui.DesignerView):
    def __init__(
        self,
        key_or_text,
        *format_args,
        verbatim=False,
        random_from_list=False,
        **format_kwargs
    ):
        super().__init__(
            discord.ui.TextDisplay(
                key_or_text.format(*format_args, **format_kwargs)
                if verbatim
                else format_message(
                    key_or_text,
                    *format_args,
                    random_from_list=random_from_list,
                    **format_kwargs
                )
            )
        )
