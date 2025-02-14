# Eggsplode

Play items, betray your friends, and be the last one to survive in this action-packed Discord game! Inspired by the card game Exploding Kittens, Eggsplode mixes explosions and... eggs.

## Features:

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

1. Set up a bot on the [Discord Dev Portal](https://discord.dev) and copy its Bot Token (can be found on the *Bot* page); Optionally, you can invite it to a Discord server to test it.

2. Clone the GitHub repo:
```
git clone https://github.com/iqnite/eggsplode
```

3. Go to the folder you cloned the repo into:
```
cd eggsplode
```

4. (Optional) Create a virtual environment:
```
python -m venv .venv
```

5. (Optional) Activate the venv:

**Windows:**
```
.venv\Scripts\activate.bat
```

**Linux/macOS:**
```
source .venv/bin/activate
```

6. Install the dependencies:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```
  
7. Copy the `.env.example` file, rename it to `.env`, and replace `YOUR_BOT_TOKEN` with the token you copied earlier

8. Finally, start the bot by running the `app.py` file:
```
python app.py
```

That's it! Your bot should now be online.
