"""
Eggsplode Discord Bot Application

This module contains the main application logic for the Eggsplode Discord bot.
"""

import logging
from logging.handlers import RotatingFileHandler
import discord
from eggsplode.commands import EggsplodeApp
from eggsplode.strings import DISCORD_TOKEN, CONFIG

if not DISCORD_TOKEN:
    raise TypeError("DISCORD_TOKEN must be set in .env file.")

logger = logging.getLogger("discord")
log_path = CONFIG.get("log_path", "")
if log_path != "":
    handler = RotatingFileHandler(
        log_path,
        maxBytes=int(CONFIG.get("log_bytes", 5242880)),  # Default 5 MB
        backupCount=int(CONFIG.get("log_backups", 9)),  # Default 9 backups
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(
        getattr(logging, CONFIG.get("log_level", "INFO").upper(), logging.INFO)
    )

app = EggsplodeApp(
    activity=discord.Activity(type=discord.ActivityType.watching, name="you"),
    logger=logger,
)

if __name__ == "__main__":
    if log_path != "":
        logger.info("Program started.")
    app.run(DISCORD_TOKEN)
