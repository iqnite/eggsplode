from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "times_scammed" INT NOT NULL DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "times_scammed";"""


MODELS_STATE = (
    "eJztWVtvIjcU/isRT6nUVoQQyO4b0KRNdxekXKpKq5VlPGawMmOztqdstOW/99jMhZnx0E"
    "wKpETzlPD5HF++c5nj4++tUHg0UD+PsPRa70++tzgOKfyTw388aeHFIkMNoPE0sIIkkZgq"
    "LTHRgM1woChAHlVEsoVmggPKoyAwoCAgyLifQRFnXyOKtPCpnlMJA5+/AMy4R79RlfxcPK"
    "IZo0F+mwQ2hOwPkLDDSD8t7NBojuW1VTCrThERQRTyktLiSc8FT7Vgbwb1KacSa+ptHMfs"
    "Nj51Aq13DoCWEU237GWAR2c4CvTG8acow1oIjSf36O7qHqFWDcKI4IZsxrWybIT4Gwoo9/"
    "Ucfva6q/U6GR1rKbPgH4Pb0W+D29Ne9wezoACLrc04jkc6dmhlp8AarydJbTB7LABTTB6X"
    "4AEoN5LZJ1JUGg+JFPapKhtpGOtff7ilAbYHL9sk9sUHmMv444OZ6yVGSoDMSpmnHsBMq8"
    "QPEzR2k5UhUnREFbXlobATFhHMgRQvXtustEGaK7AtvjWwo0TiVQLbrI6Y5/AY5t9w7Q7s"
    "DaWCCxm2Cx4TR+j/N6p9s4Wf3nU65+f9Tvu8d3nR7fcvLtuXIGv3Wx7qbwn94c2vN+P7fN"
    "QbwBXrmR2YQgspZiygaBFNA0YcFhEioJi7TeLULxhnChPsK54Ti+0vnp1cTyYfzcyhUl+D"
    "NfkF5scPn4ZXt6dnNg2DENM5g2x+4QIhy6RXxkAq/+8RsCuOz3rggO1ee7+B0Dnr9ruX57"
    "1u6v8pss3ty4z68Be8MsBP1JFfKoktqh2O3+Midrn+htdiden87jeUtuZYITKn9vT1Em9B"
    "84ApN0WON+dGSosQSUoYrICIrDBAdRKunKBx8SLZoVAacWF4YhxhJMWyBtMV2g3NrkwCaR"
    "aRACvFCFoyYCjSZuNQNr8guWyfrMk3NfINXPM47AJc2OdC1so0LtXG+YsES6oWlGgo37Dr"
    "TlnJbkmvobZIrWamgFMEh2Etxy3pNdQaal/UZTMdNtS02F6xxZaRVtFry7G6vemW9kt333"
    "37nHb1bNv+y3O7cbWS5htrwP3HTFndWgNTAGvRmphncpvTaTJm6eJmgtnlrFsegzKV3TwF"
    "vXIK3M9j0CEb88dA8sF686V6IG+Jshmu4RYAd4EP9Mma4gb2jTlx3ckKL0FHZoKqTz3AEi"
    "/Tb9im68HZ4cR0fQsbDe5Gg1+uWqX8sQNKk1fzN0rpRsp0U1pds+6zDhtQycjcVYDFI1sr"
    "L5zJvMqDZ1Ni7aHE+otKxVzvEdX1wIbKG6wHOhcXzygIQKqyIrBj+ZLABFUNhmPxN8juWb"
    "v9DHZBqpJdO1Z8AOaaui4Jv99NxlVvwKlKgWWPEX3y90nA1DGWXVvINWTkurEJp6efBn8W"
    "6R59nAwtOUJpX9pZ7ATDeg2Y3X/MVv8Ac8yiqg=="
)
