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


class Achievement(Model):
    id = fields.IntField(pk=True)
    code_name = fields.CharField(max_length=64, unique=True)


class UserAchievement(Model):
    user = fields.ForeignKeyField("models.User", related_name="achievements")
    achievement = fields.ForeignKeyField("models.Achievement")
    unlocked_at = fields.DatetimeField(auto_now_add=True)

    class Meta:  # type: ignore
        unique_together = (("user", "achievement"),)


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


@db_operation
async def get_user_achievements(user_id: int) -> list[Achievement]:
    user = await get_user(user_id)
    achievements = (
        await UserAchievement.filter(user=user).prefetch_related("achievement").all()
    )
    return [ua.achievement for ua in achievements]


@db_operation
async def unlock_achievement(user_id: int, code_name: str):
    user = await get_user(user_id)
    achievement = await Achievement.get(code_name=code_name)
    await UserAchievement.get_or_create(user=user, achievement=achievement)
