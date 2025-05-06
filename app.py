"""
Eggsplode Discord Bot Application

This module contains the main application logic for the Eggsplode Discord bot.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
import discord
from eggsplode.commands import EggsplodeApp
from eggsplode.strings import DISCORD_TOKEN, CONFIG

if not DISCORD_TOKEN:
    raise TypeError("DISCORD_TOKEN must be set in .env file. ")

logger = logging.getLogger("discord")
if CONFIG.get("log_path", "") != "":
    handler = RotatingFileHandler(
        CONFIG.get("log_path"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    sys.excepthook = logger.error

app = EggsplodeApp(
    activity=discord.Activity(type=discord.ActivityType.watching, name="you")
)

if __name__ == "__main__":
    if CONFIG.get("log_path", "") != "":
        logger.info("PROGRAM STARTED!")
    print("PROGRAM STARTED!")
    app.run(DISCORD_TOKEN)
