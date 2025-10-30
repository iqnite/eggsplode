"""
Common strings used by modules.
"""

import os
import json
import random
from dotenv import load_dotenv

MAX_COMPONENTS = 40

load_dotenv()
discord_token: str = os.getenv("DISCORD_TOKEN", "")

with open("resources/info.json", encoding="utf-8") as f:
    app_info: dict = json.load(f)
try:
    with open("resources/config.json", encoding="utf-8") as f:
        app_config: dict = json.load(f)
except FileNotFoundError:
    app_config = {}
with open("resources/messages.json", encoding="utf-8") as f:
    app_messages: dict = json.load(f)
with open("resources/cards.json", encoding="utf-8") as f:
    available_cards: dict = json.load(f)
with open("resources/recipes.json", encoding="utf-8") as f:
    default_recipes: dict = json.load(f)
try:
    with open("resources/emojis.json", encoding="utf-8") as f:
        app_emojis: dict = json.load(f)
except FileNotFoundError:
    app_emojis = {}

test_guild_id: int = int(app_config.get("test_guild_id", 0))
game_timeout: int = int(app_config.get("game_timeout", 1800))


def replace_emojis(text: str) -> str:
    for name, emoji in app_emojis.items():
        text = text.replace(name, emoji)
    return text


def format_message(
    key: str, *format_args, random_from_list: bool = False, **format_kwargs
) -> str:
    message = app_messages[key]
    if isinstance(message, str):
        return replace_emojis(message.format(*format_args, **format_kwargs))
    if isinstance(message, list):
        if random_from_list:
            return replace_emojis(
                random.choice(message).format(*format_args, **format_kwargs)
            )
        return replace_emojis("\n".join(message).format(*format_args, **format_kwargs))
    raise ValueError(f"Invalid message format for key: {key}")


def get_card_by_title(title: str, match_case: bool = False) -> str:
    match_func = str if match_case else str.lower
    for card, data in available_cards.items():
        if match_func(data["title"]) == match_func(title):
            return card
    raise ValueError(f"Card with title '{title}' not found.")


def tooltip(card: str, emoji=True) -> str:
    if card not in available_cards:
        raise ValueError(f"Card '{card}' not found in CARDS.")
    return (
        replace_emojis(available_cards[card]["emoji"]) + " "
        if emoji and "emoji" in available_cards[card]
        else ""
    ) + format_message(
        "tooltip", available_cards[card]["title"], available_cards[card]["description"]
    )
