"""
Common strings used by modules.
"""

import os
import json
import random
from dotenv import load_dotenv

MAX_COMPONENTS = 40

load_dotenv()
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

with open("resources/info.json", encoding="utf-8") as f:
    INFO: dict = json.load(f)
try:
    with open("resources/config.json", encoding="utf-8") as f:
        CONFIG: dict = json.load(f)
except FileNotFoundError:
    CONFIG = {}
with open("resources/messages.json", encoding="utf-8") as f:
    MESSAGES: dict = json.load(f)
with open("resources/cards.json", encoding="utf-8") as f:
    CARDS: dict = json.load(f)
with open("resources/recipes.json", encoding="utf-8") as f:
    RECIPES: dict = json.load(f)
try:
    with open("resources/emojis.json", encoding="utf-8") as f:
        EMOJIS: dict = json.load(f)
except FileNotFoundError:
    EMOJIS = {}

TEST_GUILD_ID: int = int(CONFIG.get("test_guild_id", 0))
GAME_TIMEOUT: int = int(CONFIG.get("game_timeout", 1800))


def replace_emojis(text: str) -> str:
    for name, emoji in EMOJIS.items():
        text = text.replace(name, emoji)
    return text


def format_message(
    key: str, *format_args, random_from_list: bool = False, **format_kwargs
) -> str:
    message = MESSAGES[key]
    if isinstance(message, str):
        return replace_emojis(message.format(*format_args, **format_kwargs))
    if isinstance(message, list):
        if random_from_list:
            return replace_emojis(random.choice(message).format(*format_args, **format_kwargs))
        return replace_emojis("\n".join(message).format(*format_args, **format_kwargs))
    raise ValueError(f"Invalid message format for key: {key}")


def get_card_by_title(title: str, match_case: bool = False) -> str:
    match_func = str if match_case else str.lower
    for card, data in CARDS.items():
        if match_func(data["title"]) == match_func(title):
            return card
    raise ValueError(f"Card with title '{title}' not found.")


def tooltip(card: str, emoji=True) -> str:
    if card not in CARDS:
        raise ValueError(f"Card '{card}' not found in CARDS.")
    return (
        replace_emojis(CARDS[card]["emoji"]) + " "
        if emoji and "emoji" in CARDS[card]
        else ""
    ) + format_message("tooltip", CARDS[card]["title"], CARDS[card]["description"])
