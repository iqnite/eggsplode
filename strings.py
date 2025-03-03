"""
Common strings used by modules.
"""

import os
import json
from dotenv import load_dotenv

VERSION = "v0.5.3"

with open("messages.json", encoding="utf-8") as f:
    MESSAGES = json.load(f)
with open("cardtypes.json", encoding="utf-8") as f:
    CARDS = json.load(f)

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOG_PATH = os.getenv("LOG_PATH")
RESTART_CMD = os.getenv("RESTART_CMD")
ADMIN_MAINTENANCE_CODE = os.getenv("ADMIN_MAINTENANCE_CODE")
ADMIN_LISTGAMES_CODE = os.getenv("ADMIN_LISTGAMES_CODE")
