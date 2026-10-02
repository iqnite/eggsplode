"""
Common strings used by modules.
"""

import json
import os
import random
from pathlib import Path

from dotenv import load_dotenv

MAX_COMPONENTS = 40
NOPE_TIMEOUT = 7
EXPLICIT_NOPE_TIMEOUT = 15
OK_DELAY = 2

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
with open("resources/achievements.json", encoding="utf-8") as f:
    all_achievements: dict = json.load(f)
try:
    with open("resources/emojis.json", encoding="utf-8") as f:
        app_emojis: dict = json.load(f)
except FileNotFoundError:
    app_emojis = {}

test_guild_id: int = int(app_config.get("test_guild_id", 0))
game_timeout: int = int(app_config.get("game_timeout", 1800))
current_dir = Path(__file__).resolve().parent
database_path = app_config.get("database_path", "../data/eggsplode.db")
database_path = (
    str(database_path)
    if os.path.isabs(database_path)
    else str(current_dir / database_path)
)
database_path = database_path.replace("\\", "/")

tortoise_orm_config = {
    "connections": {"default": f"sqlite://{database_path}"},
    "apps": {
        "models": {
            "models": ["eggsplode.database", "aerich.models"],
            "default_connection": "default",
        }
    },
}


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


def achievement_unlocked_message(achievement: str) -> str:
    return format_message(
        "achievement_unlocked",
        all_achievements.get(achievement, {}).get("emoji", "❔"),
    )
