# Eggsplode

With support from [Hack Club](https://hackclub.com/).

The Discord adaptation of the Exploding Kittens card game! During your turn, you draw a card. If it's an Eggsplode card, you lose! Use all the other cards to attack, steal, defuse, survive, and win!

[🤖 **Install**](https://iqnite.github.io/eggsplode/install.html) | [🗨️ **Support and community server**](https://iqnite.github.io/eggsplode/discord.html) | [🌐 **Website**](https://iqnite.github.io/eggsplode/)

![Banner](https://iqnite.github.io/images/eggsplode_banner.png)

Eggsplode is the Discord adaptation of the **Exploding Kittens** card game, a highly strategic version of Uno and Russian Roulette. It has most of the original game's features, including...

- 25+ unique cards, each with their own mechanics and new ones added regularly!
  - Defuse, Radioeggtive, Eggsperiment, Attegg, Alter the Future, ...
- Endless playstyles and strategies!
  - Chill out and watch the others kill each other? Or jump right into the mix and set everything on fire?
- Fine-tune your games with recipes and expansions!
  - Danger Mode? Eggzilla? Eye for an Eye? Or maybe just a classic round...
- Entirely on Discord, with no player limits!
  - Suddenly your 500 server members want to play? We got it, buddy.
- **Lots of easter eggs, surprises, secrets, and bad jokes...**
  - Listen, I can't spoil everything, just go play by yourself!

**Eggsplode is completely free and open-source.**

*No eggs were injured while making this game.*

## Credits

- This project is created and maintained by [**Phorb**](https://iqnite.github.io/).
- Huge thanks to **Psilo** for making the card icons!
- The project is based on the [**Pycord**](https://pycord.dev/) library.
- The game concept is based on the card game [**Exploding Kittens**](https://explodingkittens.com/).
- Thanks to all the early testers for their feedback and patience!
- And of course, thank you for playing!

Parts of the code review and debugging process were assisted by GitHub Copilot.

## Installing (Test version)

### 1. Bot Setup

First, we need to create a Bot on Discord's side.

1. On the [Discord Dev Portal](https://discord.com/developers/applications), click on *New Application*. Customize the title, icon, description, etc.
2. In the *Installation* page, select `application.commands` in both *User Install* and *Guild Install*. Also select `bot` in *Guild Install*. Under *Permissions*, select the following:
    - Send Messages
    - Send Messages in Threads
    - Attach Files
    - Embed Links
3. Under *Install Link*, make sure *Discord Provided Link* is selected. Copy the install link and open it to install your bot. For now, you should only install it to a test server.
4. In the *Bot* page, click on *Reset Token*. Copy the new token to a safe place (we'll need it later).
5. In Discord, enable *Developer Mode* under *User Settings* > *Advanced*.
6. Right-click on your test server and select *Copy Server ID*.

### 2. Project Setup

Clone the Git repo and go to the folder you cloned the repo into.

```bash
git clone https://github.com/iqnite/eggsplode
cd eggsplode
```

> [!NOTE]
> I strongly recommend to look into Git and version control before contributing to Eggsplode, as it's important knowledge. There are easy-to-understand tutorials about Git on YouTube, which is why I will not explain it here.

1. Copy the `.env.example` file and rename it to `.env`.
2. Open the new `.env` file in a text editor.
3. Replace `YOUR_BOT_TOKEN` with... your Bot Token.
4. Save the file and close the text editor.
5. In the `resources` folder, copy the `config.json.example` file and rename it to `config.json`.
6. Open the new `config.json` file in a text editor.
7. Set the `test_guild_id` to your test server ID.
8. Save the file and close the text editor.

> [!TIP]
> If you don't have your bot token or test server ID anymore, simply repeat steps 4 or 6 in the [Bot Setup](#1-bot-setup) section, respectively.

### 3. Installation

Time to install the dependencies!

> [!IMPORTANT]
> Eggsplode requires Python 3.10 or higher.

Python's package manager (pip) will automatically detect the required libraries if you run the following commands.

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> [!TIP]
> If one of these commands fails, try replacing `python` with `python3` or `pip` with `pip3`.
>
> Although it is best practice to create a virtual environment, it is not strictly necessary. If your operating system enforces it, please google "python virtual environment" and go by a tutorial.

### 4. Start the bot

You're all set! Now you can start the bot and it should appear online on your test server!
