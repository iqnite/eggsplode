import os
import random
import json
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
assert DISCORD_TOKEN is not None, "DISCORD_TOKEN is not set in .env file"
with open('cardtypes.json', encoding='utf-8') as f:
    CARDS = json.load(f)

app = commands.Bot()


class Game:
    def __init__(self, *players):
        self.players: list[int] = list(players)
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.current_player: int = 0
        self.action_id: int = 0

    def start(self):
        for card in CARDS:
            self.deck.extend([card] * CARDS[card]['count'])
        self.deck = self.deck * (1 + len(self.players) // 5)
        random.shuffle(self.deck)
        for _ in range(7):
            for player in self.players:
                assert isinstance(player, int), "Player must be an integer"
                if player not in self.hands.keys():
                    self.hands[player] = []
                self.hands[player].append(self.deck.pop())
        for player in self.players:
            assert isinstance(player, int), "Player must be an integer"
            self.hands[player].append('defuse')
        for _ in range(len(self.players) - 1):
            self.deck.append('eggsplode')
        random.shuffle(self.deck)

    @property
    def current_player_id(self):
        return self.players[self.current_player]

    def group_hand(self, user_id, usable_only=False):
        hand = self.hands[user_id]
        result_cards = []
        result_counts = []
        for card in hand:
            if usable_only and not CARDS[card]['usable']:
                continue
            if card in result_cards:
                continue
            result_cards.append(card)
            result_counts.append(hand.count(card))
        return list(zip(result_cards, result_counts))

    def draw_card(self, user_id):
        card = self.deck.pop()
        if card == 'eggsplode':
            if 'defuse' in self.hands[user_id]:
                self.hands[user_id].remove('defuse')
                self.deck.insert(random.randint(
                    0, len(self.deck)), 'eggsplode')
                self.next_turn()
                return 'defuse'
            else:
                self.remove_player(user_id)
                if len(self.players) == 1:
                    return 'gameover'
                else:
                    return 'eggsplode'
        else:
            self.hands[user_id].append(card)
            self.next_turn()
            return card

    def next_turn(self):
        self.current_player = 0 if self.current_player == len(
            self.players) - 1 else self.current_player + 1

    def remove_player(self, user_id):
        del self.players[self.players.index(
            user_id)]
        del self.hands[user_id]
        self.current_player -= 1
        self.next_turn()

    def kick_ends_game(self, user_id):
        self.remove_player(user_id)
        if len(self.players) == 1:
            return True
        else:
            for i in range(len(self.deck)-1, 0, -1):
                if self.deck[i] == 'eggsplode':
                    self.deck.pop(i)
                    break
            return False


games: dict[int, Game] = {}


class TurnView(discord.ui.View):
    def __init__(self, game_id: int):
        super().__init__(timeout=30)
        self.game_id = game_id
        self.game: Game = games[game_id]
        self.action_id = self.game.action_id
        self.interacted = False

    async def on_timeout(self):
        if not self.interacted and self.action_id == self.game.action_id:
            assert self.message
            view = TurnView(self.game_id)
            prev_user = self.game.current_player_id
            if self.game.kick_ends_game(self.game.current_player_id):
                await self.message.edit(content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n# 🎉 <@{self.game.players[0]}> wins!", view=None)
                del games[self.game_id]
            else:
                await self.message.edit(content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n### ⌛ <@{self.game.current_player_id}>'s turn!", view=view)

    @discord.ui.button(label="Play!", style=discord.ButtonStyle.blurple, emoji="🤚")
    async def play(self, button: discord.ui.Button, interaction: discord.Interaction):
        assert interaction.user
        if interaction.user.id != self.game.current_player_id:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return
        assert interaction.message
        self.interacted = True
        view = PlayView(self, interaction, self.game_id, self.action_id)
        await view.create_view()
        await interaction.response.send_message("**Play** as many cards as you want, then **draw** a card to end your turn!", view=view, ephemeral=True)


class PlayView(discord.ui.View):
    def __init__(self, parent_view: TurnView, parent_interaction: discord.Interaction, game_id: int, action_id: int):
        super().__init__(timeout=120)
        self.parent_view = parent_view
        self.parent_interaction = parent_interaction
        self.game = games[game_id]
        self.game_id = game_id
        self.action_id = action_id
        self.interacted = False

    async def create_view(self):
        await self.create_card_selection(self.parent_interaction)

    async def on_timeout(self):
        if not self.interacted and self.action_id == self.game.action_id:
            view = TurnView(self.game_id)
            prev_user = self.game.current_player_id
            if self.game.kick_ends_game(self.game.current_player_id):
                await self.parent_interaction.followup.send(content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n# 🎉 <@{self.game.players[0]}> wins!")
                del games[self.game_id]
            else:
                await self.parent_interaction.followup.send(content=f"*💀 <@{prev_user}> was kicked for inactivity.*\n### ⌛ <@{self.game.current_player_id}>'s turn!", view=view)
            await super().on_timeout()

    async def verify_turn(self, interaction: discord.Interaction):
        assert interaction.user
        if interaction.user.id != self.game.current_player_id:
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("❌ It's not your turn!", ephemeral=True)
            return False
        if self.action_id != self.game.action_id:
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("❌ This turn has ended or the action is not valid anymore! Make sure to click **Play** on the latest message.", ephemeral=True)
            return False
        self.game.action_id += 1
        self.action_id += 1
        return True

    async def end_turn(self, interaction: discord.Interaction):
        self.interacted = True
        view = TurnView(self.game_id)
        await interaction.followup.send(f"### ⌛ <@{self.game.current_player_id}>'s turn!", view=view)
        self.parent_view.disable_all_items()
        assert self.parent_interaction.message
        await interaction.followup.edit_message(self.parent_interaction.message.id, view=self.parent_view)

    async def create_card_selection(self, interaction: discord.Interaction):
        assert interaction.user
        user_cards = self.game.group_hand(
            interaction.user.id, usable_only=True)
        if len(user_cards) == 0:
            return
        self.play_card_select = discord.ui.Select(
            placeholder="Select a card to play",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    value=card,
                    label=f"{CARDS[card]['title']} ({count}x)",
                    description=CARDS[card]['description'],
                    emoji=CARDS[card]['emoji'],
                ) for card, count in user_cards
            ],
        )
        self.play_card_select.callback = self.play_card
        self.add_item(self.play_card_select)

    @discord.ui.button(label="Draw", style=discord.ButtonStyle.blurple, emoji="🤚")
    async def draw_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.draw_card(interaction)

    async def draw_card(self, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        if not await self.verify_turn(interaction):
            return
        assert interaction.user
        card = self.game.draw_card(interaction.user.id)
        match card:
            case 'defuse':
                await interaction.followup.send(f"## 🔧 <@{interaction.user.id}> drew an Eggsplode card! Luckily, they had an Defuse and put it back into the deck!")
            case 'eggsplode':
                await interaction.followup.send(f"## 💥 <@{interaction.user.id}> drew an Eggsplode card and died!")
            case 'gameover':
                await interaction.followup.send(f"## 💥 <@{interaction.user.id}> drew an Eggsplode card and died!")
                await interaction.followup.send(f"# 🎉 <@{self.game.players[0]}> wins!")
                del games[self.game_id]
                self.on_timeout = super().on_timeout
                return
            case other:
                await interaction.followup.send(f"🃏 <@{interaction.user.id}> drew a card!")
                await interaction.followup.send(f"You drew a **{CARDS[card]['emoji']} {CARDS[card]['title']}**!", ephemeral=True)
        await self.end_turn(interaction)

    async def play_card(self, interaction: discord.Interaction):
        if not await self.verify_turn(interaction):
            return
        selected = self.play_card_select.values[0]
        assert isinstance(selected, str)
        assert interaction.user
        self.game.hands[interaction.user.id].remove(selected)
        self.remove_item(self.play_card_select)
        await self.create_card_selection(interaction)
        await interaction.response.edit_message(view=self)
        match selected:
            case 'shuffle':
                random.shuffle(self.game.deck)
                await interaction.followup.send(f"🔄 <@{interaction.user.id}> shuffled the deck!")
            case 'skip':
                await interaction.followup.send(f"⏩ <@{interaction.user.id}> skipped their turn and did not draw a card!")
                self.game.next_turn()
                await self.end_turn(interaction)
            case 'predict':
                next_cards = "".join(
                    f"\n- **{CARDS[card]['emoji']} {CARDS[card]['title']}**" for card in self.game.deck[-1:-4:-1]
                )
                await interaction.followup.send(f"🔮 <@{interaction.user.id}> looked at the next 3 cards on the deck!")
                await interaction.followup.send(f"### Next 3 cards on the deck:{next_cards}", ephemeral=True)
            case _:
                await interaction.followup.send(f"🙁 Sorry, not implemented yet.", ephemeral=True)


class StartGameView(discord.ui.View):
    def __init__(self, game_id):
        super().__init__(timeout=600)
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
        await interaction.followup.send(f"### ⌛ <@{game.current_player_id}>'s turn!", view=view)


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
    game_id = ctx.interaction.id
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
    return map(str, games_with_user(ctx.interaction.user.id))


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
    autocomplete=game_id_autocomplete,
)
async def hand(
    ctx: discord.ApplicationContext,
    game_id: str,
):
    assert ctx.interaction.user
    if not game_id:
        games_with_id = games_with_user(ctx.interaction.user.id)
        if not games_with_id:
            await ctx.respond("❌ You are not in any games!", ephemeral=True)
            return
        new_game_id = games_with_id[0]
    else:
        new_game_id = int(game_id)
    if new_game_id not in games:
        await ctx.respond("❌ Game not found!", ephemeral=True)
        return
    if ctx.interaction.user.id not in games[new_game_id].players:
        await ctx.respond("❌ You are not in this game!", ephemeral=True)
        return
    try:
        player_hand = games[new_game_id].group_hand(ctx.interaction.user.id)
        hand_details = "".join(
            f"\n- **{CARDS[card]['emoji']} {CARDS[card]['title']}** ({count}x): {CARDS[card]['description']}"
            for card, count in player_hand
        )
        await ctx.respond(f"# Your hand:{hand_details}", ephemeral=True)
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
