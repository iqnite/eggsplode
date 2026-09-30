"""
Contains methods and classes for interacting with the database.
"""

import logging

from tortoise import Tortoise, fields
from tortoise.models import Model

from eggsplode.strings import database_path

logger = logging.getLogger(__name__)


class User(Model):
    user_id = fields.BigIntField(pk=True)
    games_played = fields.IntField(default=0)
    games_won = fields.IntField(default=0)


def db_operation(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error in database operation %s: %s", func.__name__, e)
            return None

    return wrapper


@db_operation
async def init():
    await Tortoise.init(
        db_url=f"sqlite://{database_path}",
        modules={"models": [__name__]},
        _enable_global_fallback=True,
    )
    await Tortoise.generate_schemas()


@db_operation
async def close():
    await Tortoise.close_connections()


@db_operation
async def get_user(user_id: int) -> User:
    user, _ = await User.get_or_create(user_id=user_id)
    return user


@db_operation
async def increase_games_played(user_id: int):
    user = await get_user(user_id)
    user.games_played += 1
    await user.save()


@db_operation
async def increase_games_won(user_id: int):
    user = await get_user(user_id)
    user.games_won += 1
    await user.save()
