from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "warnings_ignored" INT NOT NULL DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "warnings_ignored";"""


MODELS_STATE = (
    "eJztWVtP2zAU/iuoT0zaptIWyvbWdrAxoJW4TJMQslzHpBaJXWJnBbH+9x07tyZxupa1MF"
    "CfIJ/P8eU7F5/jPtZ84VBPfuzhwKl93nqscexT+CeHv9+q4fE4QzWg8NAzgiSRGEoVYKIA"
    "u8GepAA5VJKAjRUTHFAeep4GBQFBxt0MCjm7CylSwqVqRAMYuLoGmHGH3lOZfI5v0Q2jXn"
    "6bBDaEzAdImGGkHsZmqDfCwaFR0KsOERFe6POS0vhBjQRPtWBvGnUppwFW1Jk5jt5tfOoE"
    "inYOgApCmm7ZyQCH3uDQUzPHH6IMqyHUH1yg84MLhGpLEEYE12QzrqRhw8f3yKPcVSP43G"
    "tNo3UyOiIpveCPzlnvW+dse6/1Ti8owGKRGfvxSMMMTc0UWOFoktQGN7cFYIjJ7QQ8AOVG"
    "MvuEkgbaQ0KJXSrLRurG+ofHZ9TD5uBlm8S+eAlzaX+81HM9xUgJkFkp89RnMNM08cMEjd"
    "1kqokUDVFFbXnIb/hFBHMgxYnX1ivNkGYLbIPPDewwkXiRwNarI+ZYPIa5R1zZA3tGqeBC"
    "mu2Cx8QR+v9Gtau38OFTo9Fsthv15t7+bqvd3t2v74Os2W95qD0n9LtHX4/6F/mo14At1j"
    "M7uPBXorGHH6jFGJWWKKr93RyrCuD6es3R2Gm1W/vNvVZqhRSZR35CdJHYSZTwlmJ1Yk2S"
    "G0prIywRGVFz+nLeEMKjmNuJLWgWqB2C6rq4TZH1XTjWZDAYnOiZfSnvvCg7FFJD//K0e3"
    "C2vWPqBBBiitpZJ6FUwkcBJQxWQCSoMEClV1dPsHHxItm+kApxoXliHGEUiMkSTFdob2i2"
    "ZRJIs4h4WEpG0IQBQ6HSG4ca4wnJZf5km3yzRL6BmpjDLsCFXS6CpTKNTXXj/JrgJzV3ur"
    "FDm87uBTu7jLSKFi/H6vxeL23TV9/0XaXNpHktul60CbT1f5XB/cb6vn+8y6o7OjAFsBZG"
    "xCzIbU5nkzFLJbAOZpuzznmDzFRW8wL5wilwPW+Qz/ke9BpIfrYnoVI9kLdE2QyHUE9BVX"
    "VMH4wpjmDfmBNbdVt4gHxlJqi66gEO8CS9w2ZdD84OJ6ZRPdvrnPc6Xw5qpfyxAkqTH2ve"
    "KKUzKdNOaXXNus46rEMDRka2AiwemVt54UzmRd7ZNyXWGkqsXzSQzPayW10PzKi8wXqgsb"
    "u7QEEAUpUVgRnLlwQ6qJZgOBZ/g+zu1OsLsAtSleyasUJNK7iitibh+/mgX/W7eqpSYNlh"
    "RG393vKYfI1l1xxyNRm5d62E0+3Tzs8i3b2TQdeQI6RyAzOLmaC73APM6i+z6R9I0uNd"
)
