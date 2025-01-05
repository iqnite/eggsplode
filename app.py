import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
assert DISCORD_TOKEN is not None, "DISCORD_TOKEN is not set in .env file"

app = commands.Bot()

games = {}


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
    name="ping",
    description="Pong!",
)
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond("Pong!")


print("Hello, World!")
app.run(DISCORD_TOKEN)
