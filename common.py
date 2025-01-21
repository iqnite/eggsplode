"""
Common variables and functions used by the bot.
"""

import json

with open("messages.json", encoding="utf-8") as f:
    MESSAGES = json.load(f)
with open("cardtypes.json", encoding="utf-8") as f:
    CARDS = json.load(f)
