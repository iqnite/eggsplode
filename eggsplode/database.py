"""
Contains methods and classes for interacting with the database.
"""

import logging
from functools import wraps

from aerich import Command
from tortoise import Tortoise, fields
from tortoise.models import Model

from eggsplode.strings import all_achievements, tortoise_orm_config

logger = logging.getLogger(__name__)


class User(Model):
    user_id = fields.BigIntField(pk=True)
    games_played = fields.IntField(default=0)
    games_won = fields.IntField(default=0)
    has_cheated = fields.BooleanField(default=False)
    custom_recipes_created = fields.IntField(default=0)


class Card(Model):
    code_name = fields.CharField(pk=True, unique=True, max_length=64)


class UserCardUsage(Model):
    user = fields.ForeignKeyField("models.User", related_name="card_usages")
    card = fields.ForeignKeyField("models.Card")
    use_count = fields.IntField(default=0)

    class Meta:  # type: ignore
        unique_together = (("user", "card"),)


def db_operation(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error in database operation %s: %s", func.__name__, e)
            return None

    return wrapper


async def init():
    logger.info("Initializing database...")
    await Tortoise.init(config=tortoise_orm_config, _enable_global_fallback=True)
    command = Command(tortoise_config=tortoise_orm_config, app="models")
    await command.init()
    await command.upgrade(run_in_transaction=False)


@db_operation
async def close():
    await Tortoise.close_connections()


@db_operation
async def get_user(user_id: int) -> User:
    user, _ = await User.get_or_create(user_id=user_id)
    return user


class Achievement:
    def __init__(self, code_name: str, progress: int = 0):
        self.code_name = code_name
        self.title = all_achievements[code_name]["title"]
        self.flavor = all_achievements[code_name]["flavor"]
        self._locked_message = all_achievements[code_name].get("locked", "Locked")
        self._unlocked_message = all_achievements[code_name]["unlocked"]
        self.emoji = all_achievements[code_name]["emoji"]
        self.target = all_achievements[code_name].get("target", 1)
        self.progress = progress

    @property
    def is_unlocked(self) -> bool:
        return self.progress >= self.target

    @property
    def message(self) -> str:
        if self.is_unlocked:
            return (
                self._unlocked_message
                if self.target == 1
                else self._unlocked_message.format(self.target)
            )
        return (
            self._locked_message
            if self.target == 1
            else self._locked_message.format(self.progress, self.target)
        )

    @classmethod
    def empty(cls) -> "Achievement":
        return cls("empty")


@db_operation
async def get_user_achievements(user_id: int) -> list[Achievement]:
    user = await get_user(user_id)
    return [
        Achievement("50_wins", progress=user.games_won),
        Achievement("expert", progress=await get_unique_user_card_count(user_id)),
        Achievement("cheater", progress=1 if user.has_cheated else 0),
        Achievement("tweaker", progress=user.custom_recipes_created),
        Achievement("1_wins", progress=user.games_won),
        Achievement("1_games", progress=user.games_played),
    ]


@db_operation
async def increase_games_played(user_id: int):
    user = await get_user(user_id)
    user.games_played += 1
    await user.save()
    return user.games_played


@db_operation
async def increase_games_won(user_id: int):
    user = await get_user(user_id)
    user.games_won += 1
    await user.save()
    return user.games_won


@db_operation
async def increase_user_custom_recipes(user_id: int):
    user = await get_user(user_id)
    user.custom_recipes_created += 1
    await user.save()
    return user.custom_recipes_created


@db_operation
async def get_user_card_usage(user_id: int, code_name: str) -> UserCardUsage:
    user = await get_user(user_id)
    card, _ = await Card.get_or_create(code_name=code_name)
    usage, _ = await UserCardUsage.get_or_create(user=user, card=card)
    return usage


@db_operation
async def increase_user_card_usage(user_id: int, code_name: str):
    usage = await get_user_card_usage(user_id, code_name)
    usage.use_count += 1
    await usage.save()
    return usage.use_count


@db_operation
async def set_user_cheated(user_id: int, cheated: bool = True):
    user = await get_user(user_id)
    user.has_cheated = cheated
    await user.save()


@db_operation
async def get_unique_user_card_count(user_id: int) -> int:
    user = await get_user(user_id)
    return await UserCardUsage.filter(user=user).distinct().count()
