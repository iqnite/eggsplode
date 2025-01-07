import os
import random
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
assert DISCORD_TOKEN is not None, "DISCORD_TOKEN is not set in .env file"

app = commands.Bot()


CARDS = {
    'eggsplode': {
        'title': "Eggsplode",
        'description': "If you draw this card and don't have an Unfuse, you lose the game.",
        'emoji': "💥",
    },
    'unfuse': {
        'title': "Unfuse",
        'description': "Put an Eggsplode card back into the deck. Used automatically when you draw an Eggsplode card.",
        'emoji': "🔧",
    },
    'nope': {
        'title': "Nope",
        'description': "Stop the action of another card. Can be used at any time.",
        'emoji': "🛑",
    },
    'attegg': {
        'title': "Attegg",
        'description': "End your turn without drawing, and force the next player to draw twice.",
        'emoji': "⚡",
    },
    'shuffle': {
        'title': "Shuffle",
        'description': "Shuffle the deck.",
        'emoji': "🌀",
    },
    'predict': {
        'title': "Predict",
        'description': "Look at the first 3 cards on the deck.",
        'emoji': "🔮",
    },
}
CARD_DISTRIBUTION = ['nope'] * 5 + ['attegg'] * 4 + ['shuffle'] * 4 + ['predict'] * 5
USABLE_CARDS = {'attegg', 'shuffle', 'predict'}


class Game:
    def __init__(self, *players):
        self.players: list[int | None] = list(players)
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.current_player: int = 0
        self.turn_id: int = 0

    def start(self):
        self.deck = CARD_DISTRIBUTION * (1 + len(self.players) // 5)
        random.shuffle(self.deck)
        for _ in range(7):
            for player in self.players:
                assert isinstance(player, int), "Player must be an integer"
                if player not in self.hands.keys():
                    self.hands[player] = []
                self.hands[player].append(self.deck.pop())
        for player in self.players:
            assert isinstance(player, int), "Player must be an integer"
            self.hands[player].append('unfuse')
        for _ in range(len(self.players) - 1):
            self.deck.append('eggsplode')
        random.shuffle(self.deck)

    @property
    def current_player_id(self):
        return self.players[self.current_player]

    @property
    def alive_players(self):
        return [player for player in self.players if player]

    def group_hand(self, user_id, usable_only=False):
        hand = self.hands[user_id]
        result_cards = []
        result_counts = []
        for card in hand:
            if usable_only and card not in USABLE_CARDS:
                continue
            if card in result_cards:
                continue
            result_cards.append(card)
            result_counts.append(hand.count(card))
        return zip(result_cards, result_counts)


games: dict[str, Game] = {}


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
        if interaction.user.id != game.current_player_id:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return
        if not interaction.message:
            await interaction.response.send_message("❌ Could not determine message ID!", ephemeral=True)
            return
        view = PlayView(self, interaction.message.id,
                        self.game_id, game.turn_id)
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
        if interaction.user.id != game.current_player_id:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return False
        if self.turn_id != game.turn_id:
            await interaction.response.send_message("❌ This turn has ended! Make sure to click **Play!** on the latest message.", ephemeral=True)
            return False
        return True

    async def turn_end(self, interaction: discord.Interaction):
        game = games[self.game_id]
        game.turn_id += 1
        while True:
            game.current_player = 0 if game.current_player == len(
                game.players) - 1 else game.current_player + 1
            if game.current_player_id:
                break
        view = TurnView(self.game_id)
        await interaction.followup.send(f"⌛ <@{game.current_player_id}>'s turn!", view=view)
        self.parent_view.disable_all_items()
        await interaction.followup.edit_message(self.parent_id, view=self.parent_view)

    @staticmethod
    def final_turn_method(func):
        async def wrapped(self, button: discord.ui.Button, interaction: discord.Interaction):
            game = games[self.game_id]
            if not await self.verify_turn(interaction, game):
                return
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            if await func(self, button, interaction):
                return
            await self.turn_end(interaction)
        return wrapped

    @staticmethod
    def turn_method(func):
        async def wrapped(self, button: discord.ui.Button, interaction: discord.Interaction):
            game = games[self.game_id]
            if not await self.verify_turn(interaction, game):
                return
            await func(self, button, interaction)
        return wrapped

    @discord.ui.button(label="Draw", style=discord.ButtonStyle.blurple, emoji="🤚")
    @final_turn_method
    async def draw_card(self, button: discord.ui.Button, interaction: discord.Interaction):
        assert interaction.user
        game = games[self.game_id]
        card = game.deck.pop()
        if card == 'eggsplode':
            if 'unfuse' in game.hands[interaction.user.id]:
                game.hands[interaction.user.id].remove('unfuse')
                game.deck.append('eggsplode')
                random.shuffle(game.deck)
                await interaction.followup.send(f"🔧 <@{interaction.user.id}> drew an Eggsplode card. Luckily, they had an unfuse and put it back into the deck!")
            else:
                game.players[game.players.index(interaction.user.id)] = None
                await interaction.followup.send(f"💥 <@{interaction.user.id}> drew an Eggsplode card and died!")
                if len(game.alive_players) == 1:
                    for player in game.players:
                        if player:
                            await interaction.followup.send(f"# 🎉 <@{player}> wins!")
                            del games[self.game_id]
                            return True
        else:
            await interaction.followup.send(f"🃏 <@{interaction.user.id}> drew a card!")
            await interaction.followup.send(f"You drew a **{CARDS[card]['emoji']} {CARDS[card]['title']}**!", ephemeral=True)


class StartGameView(discord.ui.View):
    def __init__(self, game_id):
        super().__init__()
        self.game_id = game_id

    @discord.ui.button(label="Join", style=discord.ButtonStyle.blurple, emoji="👋")
    async def join_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        game = games[self.game_id]
        assert interaction.user
        if interaction.user.id in game.players:
            await interaction.response.send_message("❌ You are already in the game!", ephemeral=True)
            return
        game.players.append(interaction.user.id)
        assert interaction.message and interaction.message.content
        await interaction.response.edit_message(content=interaction.message.content + f"\n- <@{interaction.user.id}>")

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, emoji="🚀")
    async def start_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        game: Game = games[self.game_id]
        assert interaction.user
        if interaction.user.id != game.players[0]:
            await interaction.response.send_message("❌ Only the game creator can start the game!", ephemeral=True)
            return
        if len(game.players) < 2:
            await interaction.response.send_message("❌ Not enough players to start the game!", ephemeral=True)
            return
        game.start()
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"🚀 Game Started!")
        view = TurnView(self.game_id)
        await interaction.followup.send(f"⌛ <@{game.current_player_id}>'s turn!", view=view)


@app.slash_command(
    name="start",
    description="Start a new Eggsplode game!",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def start(ctx: discord.ApplicationContext):
    assert ctx.interaction.user
    game_id = str(ctx.interaction.id)
    view = StartGameView(game_id)
    games[game_id] = Game(ctx.interaction.user.id)
    await ctx.response.send_message(f"# New game\n-# Game ID: {game_id}\n<@{ctx.interaction.user.id}> wants to start a new Eggsplode game! Click on **Join** to participate!\n**Players:**\n- <@{ctx.interaction.user.id}>", view=view)


def games_with_user(user_id):
    return [
        i for i in games.keys()
        if user_id in games[i].players
    ]


async def game_id_autocomplete(ctx: discord.AutocompleteContext):
    if not ctx.interaction.user:
        return []
    return games_with_user(ctx.interaction.user.id)


@app.slash_command(
    name="hand",
    description="View your hand.",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
@discord.option(
    "game_id",
    type=str,
    description="The game ID",
    required=False,
    default="",
    autocomplete=game_id_autocomplete
)
async def hand(
    ctx: discord.ApplicationContext,
    game_id: str
):
    assert ctx.interaction.user
    if not game_id:
        games_with_id = games_with_user(ctx.interaction.user.id)
        if not games_with_id:
            await ctx.respond("❌ You are not in any games!", ephemeral=True)
            return
        game_id = games_with_id[0]
    if game_id not in games:
        await ctx.respond("❌ Game not found!", ephemeral=True)
        return
    if ctx.interaction.user.id not in games[game_id].players:
        await ctx.respond("❌ You are not in this game!", ephemeral=True)
        return
    try:
        player_hand = games[game_id].group_hand(ctx.interaction.user.id)
        await ctx.respond(f"# Your hand:{"".join(f"\n- **{CARDS[card]['emoji']} {CARDS[card]['title']}** ({count}x): {CARDS[card]['description']}" for card, count in player_hand)}", ephemeral=True)
    except KeyError:
        await ctx.respond("❌ Game has not started yet!", ephemeral=True)


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
