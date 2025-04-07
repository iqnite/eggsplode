# Eggsplode

Play items, betray your friends, and be the last one to survive in this action-packed Discord game! Inspired by the card game Exploding Kittens, Eggsplode mixes explosions and... eggs.

![Banner](https://iqnite.github.io/images/eggsplode_banner_3.png)

## Features

- **Start** games with one command, join with one click!
- **Fast-paced** turn-based system!
- Play as many cards as you want, then draw - if you draw an **Eggsplode** card, you're out!
- Attack, steal, predict, bluff, and cheat to be the last one standing and **win**!
- Use **combos** to counter attacks!
- Lots of **secrets**, easter eggs, and egg puns

*All eggs contained are 100% bio.*

## Quicklinks

- [Install](https://iqnite.github.io/eggsplode/install.html)
- [Support and community server](https://iqnite.github.io/eggsplode/discord.html)
- [Website](https://iqnite.github.io/eggsplode/)

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
4. In the *Bot* page, click on *Reset Token*. Copy the new token (we'll need it later).

### 2. Project Setup

Clone the Git repo and go to the folder you cloned the repo into.

> [!NOTE]
> I strongly recommend to look into Git and version control before contributing to Eggsplode, as it's important knowledge. There are easy-to-understand tutorials about Git on YouTube, which is why I will not explain it here.

```bash
git clone https://github.com/iqnite/eggsplode
cd eggsplode
```

Remember that Bot Token you copied earlier? We need it now. If you don't have it anymore, simply repeat step 4 in the [Bot Setup](#1-bot-setup) section.

1. Copy the `.env.example` file and rename it to `.env`.
2. Open the new `.env` file in a text editor and replace `YOUR_BOT_TOKEN` with... your Bot Token
3. Save the file and close the text editor

### 3. Installation

Time to install the dependencies!

> [!NOTE]
> Although it is best practice to create a virtual environment, it is not strictly necessary. If your operating system enforces it, please google "python virtual environment" and go by a tutorial.

Python's package manager (pip) will automatically detect the required libraries if you run the following commands.

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
  
### 4. Start the bot

You're all set! Now you can start the bot and it should appear online on your test server!

*If you don't know how to start a Python program, you **really** shouldn't be contributing to Eggsplode. 😊*
