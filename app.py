import os
import random
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
assert DISCORD_TOKEN is not None, "DISCORD_TOKEN is not set in .env file"

app = commands.Bot()

games = {}


CARDS = {
    'eggsplode': {
        'title': 'Eggsplode',
        'description': 'You lose the game.',
        'emoji': '💥',
    },
    'unfuse': {
        'title': 'Unfuse',
        'description': 'Put an Eggsplode card back into the deck.',
        'emoji': '🔧',
    },
    'attegg': {
        'title': 'Attegg',
        'description': 'End your turn without drawing, and force the next player to draw twice.',
        'emoji': '⚡',
    },
    'predict': {
        'title': 'Predict',
        'description': 'Guess the next card. If you are correct, you can give it to another player.',
        'emoji': '🔮',
    },
}

CARD_DISTRIBUTION = ['attegg'] * 4 + ['predict'] * 5


class Game:
    def __init__(self, *players):
        self.players = list(players)
        self.alive = []
        self.hands = {}
        self.deck = []
        self.current_player = 0
        self.turn_id = 0

    async def start(self):
        for card in CARD_DISTRIBUTION:
            for player in self.players:
                self.deck.append(card)
                self.hands[player] = []
        random.shuffle(self.deck)
        self.alive = self.players.copy()
        for _ in range(7):
            for player in self.players:
                self.hands[player].append(
                    self.deck.pop()
                )
        for player in self.players:
            self.hands[player].append('unfuse')
            self.deck.append('eggsplode')
        random.shuffle(self.deck)

    @property
    async def current_player_id(self):
        return self.players[self.current_player]


class TurnView(discord.ui.View):
    def __init__(self, game_id):
        super().__init__()
        self.game_id = game_id

    @discord.ui.button(label="Play!", style=discord.ButtonStyle.blurple, emoji="🤚")
    async def play(self, button: discord.ui.Button, interaction: discord.Interaction):
        game = games[self.game_id]
        if not interaction.user:
            await interaction.response.send_message("❌ Could not determine user!", ephemeral=True)
            return
        if interaction.user.id != game.players[game.current_player]:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return
        if not interaction.message:
            await interaction.response.send_message("❌ Could not determine message ID!", ephemeral=True)
            return
        view = PlayView(self, interaction.message.id, self.game_id, game.turn_id)
        await interaction.response.send_message("Select an action", view=view, ephemeral=True)


class PlayView(discord.ui.View):
    def __init__(self, parent_view: TurnView, parent_id, game_id, turn_id):
        super().__init__()
        self.parent_view = parent_view
        self.parent_id = parent_id
        self.game_id = game_id
        self.turn_id = turn_id

    async def verify_turn(self, interaction: discord.Interaction, game: Game):
        if not interaction.user:
            await interaction.response.send_message("❌ Could not determine user!", ephemeral=True)
            return False
        if interaction.user.id != game.players[game.current_player]:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return False
        if self.turn_id != game.turn_id:
            await interaction.response.send_message("❌ The turn has ended!", ephemeral=True)
            return False
        return True

    async def turn_end(self, interaction: discord.Interaction):
        game = games[self.game_id]
        game.current_player = (game.current_player + 1) % len(game.players)
        game.turn_id += 1
        view = TurnView(self.game_id)
        await interaction.followup.send(f"⌛ <@{await game.current_player_id}>'s turn!", view=view)
        self.parent_view.disable_all_items()
        await interaction.followup.edit_message(self.parent_id, view=self.parent_view)

    @staticmethod
    def turn_method(func):
        async def wrapped(self: PlayView, button: discord.ui.Button, interaction: discord.Interaction):
            game = games[self.game_id]
            if not await self.verify_turn(interaction, game):
                return
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            await func(self, button, interaction)
            await self.turn_end(interaction)
        return wrapped

    @discord.ui.button(label="Draw", style=discord.ButtonStyle.blurple, emoji="🤚")
    @turn_method
    async def draw_card(self, button: discord.ui.Button, interaction: discord.Interaction):
        assert interaction.user
        ...  # TODO: Draw card
        await interaction.followup.send(f"🃏 <@{interaction.user.id}> drew a card!")


class StartGameView(discord.ui.View):
    def __init__(self, game_id):
        super().__init__()
        self.game_id = game_id

    @discord.ui.button(label="Join", style=discord.ButtonStyle.blurple, emoji="👋")
    async def join_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        game = games[self.game_id]
        if not interaction.user:
            await interaction.response.send_message("❌ Could not determine user!", ephemeral=True)
            return
        if interaction.user.id in game.players:
            await interaction.response.send_message("❌ You are already in the game!", ephemeral=True)
            return
        game.players.append(interaction.user.id)
        if interaction.message and interaction.message.content:
            await interaction.response.edit_message(content=interaction.message.content + f"\n- <@{interaction.user.id}>")
        else:
            await interaction.response.send_message("❌ An error occurred! Please try again.", ephemeral=True)

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, emoji="🚀")
    async def start_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        game = games[self.game_id]
        if not interaction.user:
            await interaction.response.send_message("❌ Could not determine user!", ephemeral=True)
            return
        if interaction.user.id != game.players[0]:
            await interaction.response.send_message("❌ Only the game creator can start the game!", ephemeral=True)
            return
        if len(game.players) < 2:
            await interaction.response.send_message("❌ Not enough players to start the game!", ephemeral=True)
            return
        await game.start()
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"🚀 Game Started!")
        view = TurnView(self.game_id)
        await interaction.followup.send(f"⌛ <@{await game.current_player_id}>'s turn!", view=view)


@app.slash_command(
    name="start",
    description="Start a new Eggsplode game!",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def start(ctx: discord.ApplicationContext):
    if not ctx.interaction.user:
        await ctx.response.send_message("❌ Could not determine user!", ephemeral=True)
        return
    game_id = str(ctx.interaction.id)
    view = StartGameView(game_id)
    games[game_id] = Game(ctx.interaction.user.id)
    await ctx.response.send_message(f"# New game\n-# Game ID: {game_id}\n<@{ctx.interaction.user.id}> wants to start a new Eggsplode game! Click on **Join** to participate!\n**Players:**\n- <@{ctx.interaction.user.id}>", view=view)


async def game_id_autocomplete(ctx: discord.AutocompleteContext):
    return list(games.keys())


@app.slash_command(
    name="hand",
    description="View your hand.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def hand(
    ctx: discord.ApplicationContext,
    game_id: discord.Option(str, "The game ID", autocomplete=game_id_autocomplete),
):
    if not ctx.interaction.user:
        await ctx.respond("❌ Could not determine user!", ephemeral=True)
        return
    if game_id not in games:
        await ctx.respond("❌ Game not found!", ephemeral=True)
        return
    if ctx.interaction.user.id not in games[game_id].players:
        await ctx.respond("❌ You are not in this game!", ephemeral=True)
        return
    try:
        await ctx.respond(f"Your hand:{"".join(f"\n- **{CARDS[i]['emoji']} {CARDS[i]['title']}**" for i in games[game_id].hands[ctx.interaction.user.id])}", ephemeral=True)
    except KeyError:
        await ctx.respond("❌ Game not started!", ephemeral=True)


@app.slash_command(
    name="ping",
    description="Pong!",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"Pong! ({app.latency*1000:.0f}ms)")


print("Hello, World!")
app.run(DISCORD_TOKEN)
