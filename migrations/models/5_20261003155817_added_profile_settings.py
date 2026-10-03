from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "is_profile_public" INT NOT NULL DEFAULT 1;
        ALTER TABLE "user" ADD "color" INT NOT NULL DEFAULT 16685060;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "is_profile_public";
        ALTER TABLE "user" DROP COLUMN "color";"""


MODELS_STATE = (
    "eJztWdtu4zYQ/ZXATynQFo7j2Nl9s92kTXfXBnIpCiwWBC3RMhGJ1JJUvcHW/94hdbMkyo"
    "1S26kDPSU+nOHlzIWj4fdOwF3iy58nWLid9yffOwwHBP4p4D+edHAY5qgGFJ77RtBJJeZS"
    "CewowBbYlwQgl0hH0FBRzgBlke9rkDsgSJmXQxGjXyOCFPeIWhIBA5+/AEyZS74Rmf4MH9"
    "GCEr+4TQc2hMwPkDDDSD2FZmiyxOLaKOhV58jhfhSwilL4pJacZVqwN416hBGBFXE3jqN3"
    "m5w6heKdA6BERLItuzngkgWOfLVx/DnKsQ5C09k9uru6R6jTgDCHM002ZUoaNgL8DfmEeW"
    "oJPwf9dbxOTkcspRf8Y3Q7+W10ezro/6AX5GCx2IzTZKRnhtZmCqxwPElmg8VjCZhj53EF"
    "HoAKI7l9IkmE9pBIYo/IqpHGif71h1viY3Pwqk0SX3yAubQ/Pui5XmKkFMitlHvqAcy0Tv"
    "0wRRM3WWsieY/XUVsdCnpBGcEMSHGTtfVKG6TZAtvgWwM7SiVeJbD16oi6Fo+h3g1T9sDe"
    "UCq5kGa75DFJhP5/o9rTW/jpXa93fj7sdc8Hlxf94fDisnsJsma/1aHhltAf3/x6M70vRr"
    "0GbLGe24FKFAq+oD5BYTT3qWOxCOc+wcxuEqt+yThzmGBf8ZxabH/xbOV6NvuoZw6k/OrH"
    "5JeYnz58Gl/dnp6ZNAxCVBUMsnnD+VxUSa+NgUz+3yNgVxyfDcABu4PufgOhd9Yf9i/PB/"
    "3M/zNkm9tXGfXgL3ilj5+IJb/UEltWOxy/x0XsKr7DG7G6st77LaWdJZbIWRJz+maJt6R5"
    "wJSbIcebcyOpeIAEcSisgBxRY4D6JFw7QeviZbIDLhViXPNEGcJI8FUDpmu0W5ptmQTSLH"
    "J8LCV10IoCQ5HSG4ey+QXJZftkbb5pkG/gM4/BLsCFPcZFo0xjU22dv0ywIDIkjoLyDdu+"
    "KWvZrei11GpqX9QK0m0g1PaBXrEPlJNW0xAqsLq9M5Q19XbfIvqctZ5Mb/nLc1tGjSL7jX"
    "WJ/mOmrO//gCmAtSgm5pncFnTajFn5utDBbHPWLS8Wucpu3iteOQXu58XikN3jYyD5YA3k"
    "Sj1QtETVDNdQqkLB+oE8GVPcwL4xc2wfDqXniiMzQd1VD7DAq+wO23Q9ODucmMSfCpPR3W"
    "T0y1Wnkj92QGn6tPtGKd1ImXZK62vWfdZhIyKos7QVYMnI1soL5zKv8irXllh7KLH+IkJS"
    "W9O8vh7YUHmD9UDv4uIZBQFI1VYEZqxYEuigasBwIv4G2T3rdp/BLkjVsmvGyq+UTBHbR8"
    "Lvd7Np3UNlplJi2aWOOvn7xKfyGMuuLeRqMgotw5TT00+jP8t0Tz7OxoYcLpUnzCxmgnGz"
    "BszuL7P1P3RzNUU="
)
