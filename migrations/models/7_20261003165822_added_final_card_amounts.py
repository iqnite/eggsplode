from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "most_cards_won_classic" INT NOT NULL DEFAULT 0;
        ALTER TABLE "user" ADD "has_won_classic_without_cards" INT NOT NULL DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "most_cards_won_classic";
        ALTER TABLE "user" DROP COLUMN "has_won_classic_without_cards";"""


MODELS_STATE = (
    "eJztmltvIjcUgP9KxFMqtRUhBLL7BjRp090FKZeq0mplGY8ZrMzYrO0pG2357z02zN1DMy"
    "mQEs1TwrGP7fnOZezj+d4KhUcD9fMIS6/1/uR7i+OQwj85+Y8nLbxYpFIj0Hga2I4k7jFV"
    "WmKiQTbDgaIg8qgiki00ExykPAoCIxQEOjLup6KIs68RRVr4VM+phIbPX0DMuEe/URX/XD"
    "yiGaNBfpkEFoTsD+hhm5F+Wtim0RzLa6tgZp0iIoIo5CWlxZOeC55owdqM1KecSqypl3kc"
    "s9rNU8ei9cpBoGVEkyV7qcCjMxwFOvP4U5TKWgiNJ/fo7uoeoVYNYERwA5txrSyNEH9DAe"
    "W+nsPPXne1nifFse5lJvxjcDv6bXB72uv+YCYUYLG1Gceblo5tWtkhsMbrQRIbzB4Lgikm"
    "j0vwAJRrSe0TKSqNh0QK+1SVjTTc6F9/uKUBtg9etsnGFx9gLOOPD2aslxgpFqRWSj31AG"
    "ZaxX4YSzdusjIgRUdUoS03hZ2wKMEcoHibuc1MGWiuwLbyrYEdxT1eJbDN7Ih5Do9h/g3X"
    "7sDOKBVcyNAueMwmQv+/Ue2bJfz0rtM5P+932ue9y4tuv39x2b6Evna95ab+ltAf3vx6M7"
    "7PR70RuGI9tQNTaCHFjAUULaJpwIjDIkIEFHO3SZz6BeNMYYB9xXNssf3Fs5P1ZPLRjBwq"
    "9TVYwy+QHz98Gl7dnp7ZNAydmM4ZJPuGC4QsQ6+MgaT/v0fArhif9cAB2732fgOhc9btdy"
    "/Pe93E/xPJNrcvE/XhL3hlgJ+oI79Ugi2qHY7vcYFdrt/htagune/9BmlrjhUic2qfvl7i"
    "LWgeMOUmkuPNuZHSIkSSEgYzICIrDFCdhCsHaFy8CDsUSiMuDCfGEUZSLGuQrtBuMLsyCa"
    "RZRAKsFCNoyYBQpM3CYdv8guSyfbAm39TIN1U4zcnZdWh+iWmSsRrL1LCMTS8WXRZq3fzk"
    "HKBJUUXYSyw5zAeZ3OdC1nrhulQbwEXAkqoFJRpOMdhVWqmkW9Jr0BbRambOMYrgMKzluC"
    "W9Bq1B+6Jis0mzqKk0v2KlOYVWUXLOUd1ee06uDXZfhP6cFLft7dWX5xalayXNN1aH/o+Z"
    "srrCDKYAatEazDPZ5nSajFmqX5hgdjnrljvRVGU3N6KvnAL3cyd6yPupY4B8sCuq0n4gb4"
    "myGa7hFABngQ/0yZriBtaNOXGVJgoXokdmgqpXPYglXibvsKzrwbPDE9P1kXc0uBsNfrlq"
    "lfLHDpDGH4+8UaSZlOlGWr1n3ec+bEAlI3PXBmzTsnXnhdM+r3Lv32yx9rDF+otKxVzXct"
    "X7gYzKG9wPdC4unrEhgF6VOwLblt8SmKCqQXjT/Q3SPWu3n0EXelXStW3F7yC4pq5Dwu93"
    "k3HVpxCJSoGyx4g++fskYOoYt11b4BoYudJ3zPT00+DPIu7Rx8nQwhFK+9KOYgcY1ivA7P"
    "5ltvoHIemd9Q=="
)
