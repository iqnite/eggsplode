from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "most_nopes_in_a_row" INT NOT NULL DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "most_nopes_in_a_row";"""


MODELS_STATE = (
    "eJztWVtv2jAY/SuIp07aJhqu2xuwdmNtQaLtNKmqLJOYYDWxqe2Moo7/Ptu5kRuDDsqKeG"
    "pz/H2+nO+SE/NcdqmFHP6xC5lV/lx6LhPoIvlPAn9fKsPpNEYVIODI0YZmaDHigkFTSGwM"
    "HY4kZCFuMjwVmBKJEs9xFEhNaYiJHUMewY8eAoLaSEwQkwN39xLGxEJPiIeP0wcwxshJbt"
    "OUGwL6QVroYSDmUz3UnUB2rh3UqiNgUsdzScZpOhcTSiIvuTeF2oggBgWylo6jdhucOoT8"
    "nUtAMA9FW7ZiwEJj6Dli6fgjEGNlAPqDG3B9dgNAeQPCTEoU2ZgIrtlw4RNwELHFRD42ag"
    "t/nZgO30ot+KM97H5rD08atXdqQSoj5oexH4wYemihp4AC+pNEMRg/pIARNB9mMgNAYiSO"
    "j8cRUxnicWgjng1SJ/A/vxgiB+qDZ2MS5OKtnEvl462a6yVBCoE4SnGmvkKYFmEehmiQJg"
    "tFJDVoEbXZIddw0wgkkhQrWFuttERaXmFrfGVhe6HFXgpbrQ6wlZMx2O4RkV/YS06pFFJs"
    "pzImqND/t6pttYUPnwyjWm0alWqjVa81m/VWpSVt9X6zQ80Vpd/pfe31b5JVr4C8Wo/jYM"
    "u/HEwdOEc5wSiMRNrt7+HYVgFXdhsO47TWrLWqjVoUhQhZRX5IdJrYmd/wNmJ1ltskj5SW"
    "J5ADc4L06bN9g1IHQZJPbMozRe1Iuu6K2wjZ3QsntxkMBpdqZpfzR8fvDqnW0L+96pwNT0"
    "61TpBGWKB81k2PC+oChkwsVwAmKwhAYVYXT3BM8TTZLuUCEKp4wgRAwOhsA6YLvI80K5pf"
    "pG+VtgVHcbtHcRuTVqByE6yulrvRl8r2de9dpKf1B/P9ujo4TwIX1veBSd9/7JrFolaGQr"
    "Lm+cSsyW3C59gxMypAFXNesq64holdtnMJs+cWuJtrmNf8JH4LJL/aV3FGDyQjkQ3DOWUI"
    "2+QCzXUoenLfkJh5l4ypO5g3FoKiV72EGZxF77Dl1JNnlydG/idEt33dbX85K2f6xxYoDe"
    "+rD5TSpZaZT2mxZt2lDmsjhs1JngALRlYqLxjb7OWq8SixdiCxfiHGcd7lVrEeWHI5QD1g"
    "1OtrCAJpVagI9FhSEqii2oDhwPwA2T2tVNZgV1oVsqvHUpqWEoHyPhK+Xw/6RT8tRi4pli"
    "1sitLvkoP5W5RdK8hVZCSuEkNOT67aP9N0dy8HHU0O5cJmehY9QWezC5jtv8wWfwCQ7ewa"
)
