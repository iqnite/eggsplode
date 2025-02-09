"""
Common variables and functions used by the bot.
"""

import json

VERSION = "v0.5.0"

with open("messages.json", encoding="utf-8") as f:
    MESSAGES = json.load(f)
with open("cardtypes.json", encoding="utf-8") as f:
    CARDS = json.load(f)
