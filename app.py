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
    'attegg': {
        'title': 'Attegg',
        'description': 'End your turn without drawing, and force the next player to draw twice.',
        'emoji': '⚡',
    },
    'unfuse': {
        'title': 'Unfuse',
        'description': 'Put an Eggsplode card back into the deck.',
        'emoji': '🔧',
    },
    'eggsplode': {
        'title': 'Eggsplode',
        'description': 'You lose the game.',
        'emoji': '💥',
    },
}

CARD_DISTRIBUTION = ['attegg'] * 4 + ['predict'] * 5


def new_game(game_id):
    for card in CARD_DISTRIBUTION:
        for player in games[game_id]['players']:
            games[game_id]['deck'].append(card)
            games[game_id]['hands'][player] = []
    random.shuffle(games[game_id]['deck'])
    games[game_id]['alive'] = games[game_id]['players'].copy()
    for _ in range(7):
        for player in games[game_id]['players']:
            games[game_id]['hands'][player].append(
                games[game_id]['deck'].pop()
            )
    for player in games[game_id]['players']:
        games[game_id]['hands'][player].append('unfuse')
        games[game_id]['deck'].append('eggsplode')
    random.shuffle(games[game_id]['deck'])


class StartGameView(discord.ui.View):
    def __init__(self, game_id):
        super().__init__()
        self.game_id = game_id

    @discord.ui.button(label="Join", style=discord.ButtonStyle.blurple, emoji="👋")
    async def join_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id in games[self.game_id]['players']:
            await interaction.response.send_message("❌ You are already in the game!", ephemeral=True)
            return
        games[self.game_id]['players'].append(interaction.user.id)
        await interaction.response.send_message(f"👋 <@{interaction.user.id}> joined the game!\n-# Game {self.game_id}")

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, emoji="🎉")
    async def start_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != games[self.game_id]['players'][0]:
            await interaction.response.send_message("❌ Only the game creator can start the game!", ephemeral=True)
            return
        if len(games[self.game_id]['players']) < 2:
            await interaction.response.send_message("❌ Not enough players to start the game!", ephemeral=True)
            return
        new_game(self.game_id)
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"🎉 Game Started! Players:{"".join({f"\n- <@{i}>" for i in games[self.game_id]['players']})}\n-# Game {self.game_id}")


@app.slash_command(
    name="start",
    description="Start a new Eggsplode game!",
)
async def start(ctx: discord.ApplicationContext):
    game_id = str(ctx.interaction.id)
    view = StartGameView(game_id)
    games[game_id] = {
        'players': [ctx.interaction.user.id],
        'alive': [],
        'hands': {},
        'deck': [],
    }
    await ctx.response.send_message(f"<@{ctx.interaction.user.id}> wants to start a new Eggsplode game! Click on Join to participate!\n-# Game {game_id}", view=view)


@app.slash_command(
    name="hand",
    description="View your hand.",
)
async def hand(
    ctx: discord.ApplicationContext,
    game_id: discord.Option(str, "The game ID", choices=list(games.keys())),
):
    if game_id not in games:
        await ctx.respond("❌ Game not found!", ephemeral=True)
        return
    if ctx.interaction.user.id not in games[game_id]['players']:
        await ctx.respond("❌ You are not in this game!", ephemeral=True)
        return
    try:
        await ctx.respond(f"Your hand: {", ".join(games[game_id]['hands'][ctx.interaction.user.id])}", ephemeral=True)
    except KeyError:
        await ctx.respond("❌ Game not started!", ephemeral=True)


@app.slash_command(
    name="ping",
    description="Pong!",
)
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"Pong! ({app.latency*1000:.0f}ms)")


print("Hello, World!")
app.run(DISCORD_TOKEN)
