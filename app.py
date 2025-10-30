"""
Eggsplode Discord Bot Application

This module contains the main application logic for the Eggsplode Discord bot.
"""

import logging
from logging.handlers import RotatingFileHandler
import discord
from eggsplode.commands import EggsplodeApp
from eggsplode.strings import discord_token, app_config, app_info

if not discord_token:
    raise TypeError("DISCORD_TOKEN must be set in .env file.")

logger = logging.getLogger("discord")
log_path = app_config.get("log_path", "")
if log_path != "":
    handler = RotatingFileHandler(
        log_path,
        maxBytes=int(app_config.get("log_bytes", 5242880)),  # Default 5 MB
        backupCount=int(app_config.get("log_backups", 9)),  # Default 9 backups
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(
        getattr(logging, app_config.get("log_level", "INFO").upper(), logging.INFO)
    )

status_activity = discord.CustomActivity(
    name=app_config.get("custom_status", "/start"),
)
app = EggsplodeApp(
    activity=status_activity,
    logger=logger,
)

if __name__ == "__main__":
    if log_path != "":
        logger.info("Program version %s started.", app_info["version"])
    app.run(discord_token)
