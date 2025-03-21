"""
Common strings used by modules.
"""

import os
import json
from dotenv import load_dotenv

VERSION = "1.0"

with open("messages.json", encoding="utf-8") as f:
    MESSAGES = json.load(f)
with open("cards.json", encoding="utf-8") as f:
    CARDS = json.load(f)
with open("expansions.json", encoding="utf-8") as f:
    EXPANSIONS = json.load(f)
try:
    with open("emojis.json", encoding="utf-8") as f:
        EMOJIS = json.load(f)
except FileNotFoundError:
    EMOJIS = {}

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOG_PATH = os.getenv("LOG_PATH")
RESTART_CMD = os.getenv("RESTART_CMD")
ADMIN_MAINTENANCE_CODE = os.getenv("ADMIN_MAINTENANCE_CODE")
ADMIN_LISTGAMES_CODE = os.getenv("ADMIN_LISTGAMES_CODE")
