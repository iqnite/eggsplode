from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "card" (
    "code_name" VARCHAR(64) NOT NULL PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS "user" (
    "user_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "games_played" INT NOT NULL,
    "games_won" INT NOT NULL,
    "has_cheated" INT NOT NULL,
    "custom_recipes_created" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "usercardusage" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "use_count" INT NOT NULL,
    "card_id" VARCHAR(64) NOT NULL REFERENCES "card" ("code_name") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "user" ("user_id") ON DELETE CASCADE,
    CONSTRAINT "uid_usercardusa_user_id_993608" UNIQUE ("user_id", "card_id")
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztWVtv2jAU/isoT520TTRctzdg7cbagkTbaVJVWSYxwWqwaeyMoo7/Ptu5kcRh0EFZEU"
    "9tvnOOL985x/lino0JtZHLPnagZxufS88GgRMk/knh70sGnE4TVAIcDl3laEUeQ8Y9aHGB"
    "jaDLkIBsxCwPTzmmRKDEd10JUks4YuIkkE/wo48Apw7iY+QJw929gDGx0RNi0eP0AYwwct"
    "PLtMSCgHoQHsoM+HyqTJ0x9M5VgJx1CCzq+hOSC5rO+ZiSOEqsTaIOIsiDHNlL25GrDXcd"
    "QcHKBcA9H8VLthPARiPou3xp+0OQYAYAvf4NuD67AcDYgDCLEkk2JpwpNibwCbiIOHwsHu"
    "vVRTBPQkfgJSf80Rp0vrUGJ/XqOzkhFRkL0tgLLaYyLdQQkMNgkDgHo4cMMITWw0xUAEhZ"
    "kvz4DHmyQnwGHcTySWqH8ecXA+RCtfF8TsJavBVjyXq8lWO9JEkRkGQpqdRXSNMiqsMIDc"
    "tkIYmkJi2iNm+amJMsAokgxQ7nljMtkaZrbIWvbGw/8thLY8vZAbY1FYOdLuH6xl4KypSQ"
    "ZDtTMWGH/r9d7cglfPhkmpVKwyxX6s1atdGoNctN4avWmzc1VrR+u/u127tJd70EdL2e5M"
    "ERfxmYunCONMkozEQ27O/p2FYDl3ebDvO02qg2K/VqnIUYWUV+RHSW2Flw4G3E6kx7SB4p"
    "NcaQAWuM1O7z5walLoJET2wmMkPtUITuitsY2d0LR3sY9PuXcuQJY49ucDpkjobe7VX7bH"
    "ByqnSCcMIc6Vm3fMbpBHjIwmIGYHkFCSis6uIBjiUuyX6R8JKiCxxV1x5VV0JagfxKsbpa"
    "h8USevuC7C4WeupL7n5dgabTZoUtfmCa7B/fWMVqS6RCsOYHxKzJbSrmeGLmXk+ymXXFuu"
    "J+IAnZzu3Ano/A3dwPvOa32lsg+dU+13J6IJ2JfBrOqYewQy7QXKWiK9YNiaW7/cpcDryx"
    "FBS96gXswVn8DlsuPbF3sWMUaNtO67rT+nJm5M6PLVAaXaQeKKVLR6ae0mLNuksd1kIets"
    "Y6ARZaViovmPjs5Q7sKLF2ILF+IY9h3a1LsR5YCjlAPWDWamsIAuFVqAiULS0JZFNtwHDo"
    "foDsnpbLa7ArvArZVbaMpqWEI91Hwvfrfq/oN684JMOyjS1e+l1yMXuLsmsFuZKM1B1XxO"
    "nJVetnlu7OZb+tyKGMO54aRQ3Q3uwCZvsvs8Uf+055gw=="
)
