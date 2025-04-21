# Eggsplode

Play items, betray your friends, and be the last one to survive in this action-packed Discord game! Inspired by the card game Exploding Kittens, Eggsplode mixes explosions and... eggs.

![Banner](https://iqnite.github.io/images/eggsplode_banner.png)

## Features

- **Start** games with one command, join with one click!
- **Fast-paced** turn-based system!
- Play as many cards as you want, then draw - if you draw an **Eggsplode** card, you're out!
- Attack, steal, predict, bluff, and cheat to be the last one standing and **win**!
- Use **combos** to counter attacks!
- Lots of **secrets**, easter eggs, and egg puns

*No eggs were injured while making this game.*

## Quicklinks

- [Install](https://iqnite.github.io/eggsplode/install.html)
- [Support and community server](https://iqnite.github.io/eggsplode/discord.html)
- [Website](https://iqnite.github.io/eggsplode/)

## Credits

- This project is created and maintained by [Phorb](https://iqnite.github.io/).
- Huge thanks to Psilo for making the card icons!
- The project is based on the [PyCord](https://pycord.dev/) library.
- The game concept is based on the card game [Exploding Kittens](https://explodingkittens.com/).
- Thanks to all the early testers for their feedback and patience!
- And of course, thanks to you for playing!

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

> [!IMPORTANT]
> I strongly recommend to look into Git and version control before contributing to Eggsplode, as it's important knowledge. There are easy-to-understand tutorials about Git on YouTube, which is why I will not explain it here.

```bash
git clone https://github.com/iqnite/eggsplode
cd eggsplode
```

1. Copy the `.env.example` file and rename it to `.env`.
2. Open the new `.env` file in a text editor.
3. Replace `YOUR_BOT_TOKEN` with... your Bot Token.
4. Replace `YOUR_TEST_GUILD_ID` with your Test Server ID.
5. Save the file and close the text editor.

> [!TIP]
> If you don't have your bot token or test server ID anymore, simply repeat steps 4 or 6 in the [Bot Setup](#1-bot-setup) section, respectively.

### 3. Installation

Time to install the dependencies!

> [!TIP]
> Although it is best practice to create a virtual environment, it is not strictly necessary. If your operating system enforces it, please google "python virtual environment" and go by a tutorial.

Python's package manager (pip) will automatically detect the required libraries if you run the following commands.

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

> [!TIP]
> If one of these commands fails, try replacing `python3` with just `python` or `pip` with `pip3`.
  
### 4. Start the bot

You're all set! Now you can start the bot and it should appear online on your test server!
