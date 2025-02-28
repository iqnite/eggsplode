"""
Eggsplode Discord Bot Application

This module contains the main application logic for the Eggsplode Discord bot.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
import discord
from commands import Eggsplode
from strings import DISCORD_TOKEN, LOG_PATH

if not DISCORD_TOKEN:
    raise TypeError("DISCORD_TOKEN must be set in .env file. ")

eggsplode_app = Eggsplode(
    activity=discord.Activity(type=discord.ActivityType.watching, name="you")
)

logger = logging.getLogger("discord")
if LOG_PATH:
    handler = RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    sys.excepthook = logger.error

if __name__ == "__main__":
    if LOG_PATH:
        logger.info("PROGRAM STARTED!")
    else:
        print("PROGRAM STARTED!")
    eggsplode_app.run(DISCORD_TOKEN)
