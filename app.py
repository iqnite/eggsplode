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
    raise TypeError("DISCORD_TOKEN must be set in .env file.")

logger = logging.getLogger("discord")


def handle_exception(exc_type, value, traceback):
    logger.exception("Uncaught exception", exc_info=(exc_type, value, traceback))


log_path = CONFIG.get("log_path", "")
if log_path != "":
    handler = RotatingFileHandler(
        log_path,
        maxBytes=int(CONFIG.get("log_bytes", 5242880)),  # Default 5 MB
        backupCount=int(CONFIG.get("log_backups", 99)),  # Default 99 backups
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    sys.excepthook = handle_exception

app = EggsplodeApp(
    activity=discord.Activity(type=discord.ActivityType.watching, name="you")
)

if __name__ == "__main__":
    if CONFIG.get("log_path", "") != "":
        logger.info("PROGRAM STARTED!")
    print("PROGRAM STARTED!")
    app.run(DISCORD_TOKEN)
