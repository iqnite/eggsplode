"""
Common strings used by modules.
"""

import os
import json
from dotenv import load_dotenv

with open("resources/info.json", encoding="utf-8") as f:
    CONFIG = json.load(f)
with open("resources/messages.json", encoding="utf-8") as f:
    MESSAGES = json.load(f)
with open("resources/cards.json", encoding="utf-8") as f:
    CARDS = json.load(f)
with open("resources/expansions.json", encoding="utf-8") as f:
    EXPANSIONS = json.load(f)
try:
    with open("resources/emojis.json", encoding="utf-8") as f:
        EMOJIS = json.load(f)
except FileNotFoundError:
    EMOJIS = {}


def replace_emojis(text: str) -> str:
    for name, emoji in EMOJIS.items():
        text = text.replace(name, emoji)
    return text


def get_message(key: str) -> str:
    message = MESSAGES[key]
    if isinstance(message, str):
        return replace_emojis(message)
    if isinstance(message, list):
        return "\n".join([replace_emojis(m) for m in message])
    raise ValueError(f"Invalid message format for key: {key}")


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOG_PATH = os.getenv("LOG_PATH")
try:
    TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", "0"))
except ValueError as e:
    TEST_GUILD_ID = 0
