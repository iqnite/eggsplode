"""
Common strings used by modules.
"""

import os
import json
from dotenv import load_dotenv

MAX_COMPONENTS = 40

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

with open("resources/info.json", encoding="utf-8") as f:
    INFO = json.load(f)
try:
    with open("resources/config.json", encoding="utf-8") as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    CONFIG = {}
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

TEST_GUILD_ID = CONFIG.get("test_guild_id", 0)


def replace_emojis(text: str) -> str:
    for name, emoji in EMOJIS.items():
        text = text.replace(name, emoji)
    return text


def format_message(key: str, *format_args) -> str:
    message = MESSAGES[key]
    if isinstance(message, str):
        return replace_emojis(message).format(*format_args)
    if isinstance(message, list):
        return "\n".join([replace_emojis(m).format(*format_args) for m in message])
    raise ValueError(f"Invalid message format for key: {key}")


def get_card_by_title(title: str, match_case: bool = False) -> str:
    match_func = str if match_case else str.lower
    for card, data in CARDS.items():
        if match_func(data["title"]) == match_func(title):
            return card
    raise ValueError(f"Card with title '{title}' not found.")


def tooltip(card: str) -> str:
    if card not in CARDS:
        raise ValueError(f"Card '{card}' not found in CARDS.")
    return format_message("tooltip", CARDS[card]["title"], CARDS[card]["description"])
