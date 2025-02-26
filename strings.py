"""
Common strings used by modules.
"""

import json

VERSION = "v0.5.3"

with open("messages.json", encoding="utf-8") as f:
    MESSAGES = json.load(f)
with open("cardtypes.json", encoding="utf-8") as f:
    CARDS = json.load(f)
