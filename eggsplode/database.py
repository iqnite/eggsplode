"""
Contains methods and classes for interacting with the database.
"""

from tortoise import Tortoise, fields
from tortoise.models import Model

from eggsplode.strings import database_path


class User(Model):
    user_id = fields.IntField(pk=True)
    games_played = fields.IntField(default=0)
    games_won = fields.IntField(default=0)


async def init():
    await Tortoise.init(
        db_url=f"sqlite://{database_path}",
        modules={"models": [__name__]},
    )
    await Tortoise.generate_schemas()


async def close():
    await Tortoise.close_connections()


async def get_user(user_id: int) -> User:
    user, _ = await User.get_or_create(user_id=user_id)
    return user


async def increase_games_played(user_id: int):
    user = await get_user(user_id)
    user.games_played += 1
    await user.save()


async def increase_games_won(user_id: int):
    user = await get_user(user_id)
    user.games_won += 1
    await user.save()
