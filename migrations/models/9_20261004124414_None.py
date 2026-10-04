from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "card" (
    "code_name" VARCHAR(64) NOT NULL PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS "user" (
    "user_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "is_profile_public" INT NOT NULL,
    "color" INT NOT NULL,
    "games_played" INT NOT NULL,
    "games_won" INT NOT NULL,
    "has_cheated" INT NOT NULL,
    "custom_recipes_created" INT NOT NULL,
    "most_nopes_in_a_row" INT NOT NULL,
    "has_won_classic_without_defuse" INT NOT NULL,
    "has_won_classic_without_cards" INT NOT NULL,
    "most_cards_won_classic" INT NOT NULL,
    "warnings_ignored" INT NOT NULL,
    "respects_paid" INT NOT NULL,
    "times_scammed" INT NOT NULL,
    "largest_player_count_won" INT NOT NULL
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
    "eJztmltvIjcUgP9KxFMqtRUhBLL7BjRp090FKZeq0mplmRkzWPHYrO0pG2357z02c2FmPD"
    "STAinRPCUc+/jynYtv870VCp8w9fMIS7/1/uR7i+OQwD85+Y8nLbxYZFIj0HjKbEUvqTFV"
    "WmJPg2yGmSIg8onyJF1oKjhIecSYEQoPKlIeZKKI068RQVoERM+JhILPX0BMuU++EZX8XD"
    "yiGSUsP0wPBoTsD6hhi5F+Wtii0RzLa6tgep0iT7Ao5CWlxZOeC55qwdiMNCCcSKyJvzEd"
    "M9p41oloPXIQaBmRdMh+JvDJDEdMb0x/ijJZC6Hx5B7dXd0j1KoBzBPcwKZcK0sjxN8QIz"
    "zQc/jZ667W/WQ41rVMh38Mbke/DW5Pe90fTIcCLLY24zgu6diilW0Ca7xuJLXB7LEgmGLv"
    "cQkegHIlmX0iRaTxkEjhgKiykYax/vWHW8KwnXjZJrEvPkBbxh8fTFsvMVIiyKyUeeoBzL"
    "RK/DCRxm6yMiBFR1ShLReFnbAowRyg+HHfpqcNaK7AtvKtgR0lNV4lsE3viPoOj6HBDdfu"
    "wN5QKriQoV3wmDhC/79RHZgh/PSu0zk/73fa573Li26/f3HZvoS6drzlov6W0B/e/Hozvs"
    "9HvRG4Yj2zA1VoIcWMMoIW0ZRRz2ERIRjB3G0Sp37BOFNoYF/xnFhsf/HsZD2ZfDQth0p9"
    "ZWv4BfLjh0/Dq9vTM5uGoRLVOYNsrnBMyDL0yhhI6/97BOyK8VkPHLDda+83EDpn3X738r"
    "zXTf0/lWxz+zLRAP6CVzL8RBz5pRJsUe1wfI8L7HK9hteiunSu+w3S1hwr5M2JnX29xFvQ"
    "PGDKTSXHm3MjpUWIJPEo9IA8WWGA6iRc2UDj4kXYoVAacWE4UY4wkmJZg3SFdoPZlUkgzS"
    "KPYaWoh5YUCEXaDBy2zS9ILtsba/JNjXxThdOcnF2H5peYJm2rsUwNy9j0YtFtQq2bn5wN"
    "NCmqCHuJJYf+IJMHXMhaC65LtQFcBCyJWhBPwykGu65WKumW9Bq0RbSamnOM8nAY1nLckl"
    "6DtoiWYRkQyKL26C2BXcR1zVPmtiYa4Ab4i273zbqGmqv9V7zaz6BV3PHnqG6/7E/faXZ/"
    "6/85fU2wz4VfnvsKUGuVemMX//8xf1Zf6YMp1hmwBtucTpMxSxdGJphdzrrlETpT2c0T9C"
    "unwP08Qh/yQfAYIB/sTbC0H8hbomyGazh2weHrA3mypriBcWPuue6CCi/QR2aCqqUexBIv"
    "0zVs0/Vg7jBjsr5jGA3uRoNfrlql/LEDpMnXOm8U6UbKdCOt3rPucx82IJJ6c9cGLC7Zuv"
    "PCWZ1X+dCi2WLtYYv1F5GKuk6o1fuBDZU3uB/oXFw8Y0MAtSp3BLYsvyUwQVWDcFz9DdI9"
    "a7efQRdqVdK1ZcUPT7gmrkPC73eTcdW3J6lKgbJPPX3y9wmj6hi3XVvgGhi5t4aE6emnwZ"
    "9F3KOPk6GFI5QOpG3FNjCsdwGz+8Vs9Q+MehTl"
)
