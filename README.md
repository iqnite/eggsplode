# Eggsplode

## How to setup and test

1. Clone the GitHub repo
```
git clone https://github.com/iqnite/eggsplode
```

2. Go to the folder you cloned the repo into
```
cd eggsplode
```

3. Create a virtual environment
```
python -m venv .venv
```

4. Activate the venv

**Windows:**
```
venv\Scripts\activate.bat
```

**Linux/macOS:**
```
source myvenv/bin/activate
```

5. Install the dependencies
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. Set up a bot on the [Discord Dev Portal](https://discord.dev) and copy its Bot Token; Optionally, you can invite it to a Discord server to test it
   
7. In the Eggsplode folder, create a new file called `.env` and paste the following contents into it:
```
DISCORD_TOKEN="YOUR_BOT_TOKEN"
ADMIN_MAINTENANCE_CODE="maintenance"
ADMIN_LISTGAMES_CODE="listgames"
```

8. Finally, start the bot by running the `app.py` file
```
python app.py
```

That's it! Your bot should now be online.
