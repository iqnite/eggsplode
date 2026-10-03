from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "has_won_classic_without_defuse" INT NOT NULL DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "has_won_classic_without_defuse";"""


MODELS_STATE = (
    "eJztWVtP2zAU/itVnpi0TSUtlO2t7WBjsFbiMk1CyHIdN7VI7BI7K4j1v892bk3ihJa1MF"
    "CfIJ/P8eU7F5/jPlg+c7DHP/Zh4FifGw8WhT6W/+Tw9w0LTqcZqgABR54WRInEiIsAIiGx"
    "MfQ4lpCDOQrIVBBGJUpDz1MgQ1KQUDeDQkpuQwwEc7GY4EAOXF1LmFAH32GefE5vwJhgL7"
    "9NJDcE9IeU0MNA3E/1UH8CgyOtoFYdAcS80Kclpem9mDCaasm9KdTFFAdQYGfhOGq38akT"
    "KNq5BEQQ4nTLTgY4eAxDTywcfwQyzAJgMLwA54cXAFgrEIYYVWQTKrhmw4d3wMPUFRP5ud"
    "+eR+tkdERSasGf3bP+t+7Zzn77nVqQSYtFZhzEI7YemuspoIDRJKkNxjcFYATRzUx6AMiN"
    "ZPYJOQ6Uh4QcupiXjdSL9Y9OzrAH9cHLNol98VLOpfzxUs31FCMlQGalzFOfwUzzxA8TNH"
    "aTuSKS2ayK2vKQb/tFBFJJihOvrVZaIM0U2BqvDewwkXiRwFarA+IYPIa4x1SYA3tBqeBC"
    "iu2Cx8QR+v9Gtau28OGTbbdaHbvZ2j/Ya3c6ewfNAymr91se6tSEfu/46/HgIh/1CjDFem"
    "YHV/7lYOrBe2wwRqUlimqPm2NdAdzcrDns3XanfdDab6dWSJE68hOii8TOooS3EqszY5Lc"
    "UmpNIAdogvXpy3mDMQ9Daia2oFmgdiRVN8VtimzuwjEmg+HwVM3sc37rRdmhkBoGlz96h2"
    "c7u7pOkEJEYDPrKOSC+SDAiMgVAAoqDFDp1dUTbF28SLbPuACUKZ4IBRAEbLYC0xXaW5pN"
    "mUSmWYA8yDlBYEYkQ6FQG5c1xhOSS/1k23zzSL55Uu+h+g6wbTxesPHISKvoQHKs1rciaR"
    "e5/p7kKu119GPG9bI9iqk9qcy9b6wt+cdUW91wSFNI1sKImCW5zelsb7NShaaC2eSsNU9k"
    "mcp6HsheOAVu5onsOZ8rXgPJz/ZiUaoH8pYom+GIBZi49ATfa1Mcy31DikzFV+F97JWZoO"
    "qql3AAZ+kdtuh68uzyxDgqt/rd8373y6FVyh9roDT5LeGNUrqQMs2UVtesm6zDujggaGIq"
    "wOKR2soLZjIv8gy8LbE2UGL9xgEnpofH6npgQeUN1gP23t4SBYGUqqwI9Fi+JFBBtQLDsf"
    "gbZHe32VyCXSlVya4eK9S0jApsahK+nw8HVT/7pioFlh2CRONPwyP8NZZdNeQqMnLPLgmn"
    "Oz+6v4p090+HPU0O48IN9Cx6gt5qDzDrv8zmfwGMy3NO"
)
