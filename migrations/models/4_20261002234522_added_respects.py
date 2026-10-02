from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "respects_paid" INT NOT NULL DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "respects_paid";"""


MODELS_STATE = (
    "eJztWltv2jAU/isVT520TZTS0u0NWLt1F5B6mSZNk2UcN1hNbGY7Y9XGf9+xcyOJw0oH7V"
    "rlCfL5HF++c8k5hl+tUHg0UC+HWHqt1zu/WhyHFL4U8Oc7LTyb5agBNJ4EVpCkEhOlJSYa"
    "sCscKAqQRxWRbKaZ4IDyKAgMKAgIMu7nUMTZ94giLXyqp1TCwNdvADPu0Z9UpY+za3TFaF"
    "DcJoENIfsAEnYY6ZuZHRpOsTyxCmbVCSIiiEJeUZrd6KngmRbszaA+5VRiTb2l45jdJqdO"
    "oXjnAGgZ0WzLXg549ApHgV46/gTlWAuh0fgCnR9fINRagzAiuCGbca0sGyH+iQLKfT2Fx8"
    "PuIl4npyOWMgt+7p8N3/XPdg+7z8yCAiwWm3GUjHTs0MJOgTWOJ8lscHVdAiaYXM/BA1Bh"
    "JLdPpKg0HhIp7FNVNdIg0T/5cEYDbA9etUnii5cwl/HHSzPXXYyUArmVck+9BzMtUj9M0c"
    "RNFoZI0RF11FaHwk5YRjAHUrxkbbPSEmmuwLb4ysCOUokHCWyzOmKew2OYf8q1O7CXlEou"
    "ZNgueUwSof9vVPtmCy9edTr7+71Oe//w6KDb6x0ctY9A1u63OtRbEfqD07eno4ti1BvAFe"
    "u5HXz4VGgW4BvqMEatJcpqfzfHpgK4vV1zdPa6ve7R/mE3s0KGrCI/JbpM7DxOeGuxOncm"
    "yYbS1hQrRKbUnr6aN4QIKOZuYkuaJWonoLotbjNkey8cZzIYjz+amUOlvgdxdiilhtHlp8"
    "Hx2e6erRNAiGnqZp1ESosQSUoYrICIrDFArVfXT9C4eJnsUCiNuDA8MY4wkmK+BtM12g3N"
    "rkwCaRaRACvFCJozYCjSZuNQY9whuayerMk3a+QbqIk57AJc2OdCrpVpXKqN85cJllTNKN"
    "FQvmFXAV7LbkWvodZQe6e+2fTMqGmaH7Bpzkmr6Z4LrK5uo7MbkM3301+zPt1exH27bX+9"
    "VmQ/sZb6HzNlfbMMpgDWopiYW3Jb0GkyZqW7MMHsctYV17u5ymYudx84BW7nevc+r9oeA8"
    "n3dttWqQeKlqia4QRKVShYP9Aba4pT2DfmxNU4lO52H5kJ6l71AEs8z95hy64HZ4cT07hV"
    "GPbPh/03x61K/tgApenvYE+U0qWU6aa0vmbdZh3Wp5KRqasAS0ZWVl44l3mQnzCaEmsLJd"
    "YPKhVzXZrX1wNLKk+wHugcHNyiIACp2orAjhVLAhNUazCciD9Bdvfa7VuwC1K17NqxUk0r"
    "uKauJuH9+XhU95eFTKXEsseI3vm9EzD1GMuuFeQaMgpXhimnu5/6X8p0Dz+OB5YcobQv7S"
    "x2gsF6FzCbf5kt/gD2blDn"
)
