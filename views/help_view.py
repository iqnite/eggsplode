import discord


class HelpView(discord.ui.View):
    """
    A view for the help command in the game.
    """

    def __init__(self):
        """
        Initializes the HelpView.
        """
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Website",
                url="https://iqnite.github.io/eggsplode",
                style=discord.ButtonStyle.link,
                emoji="🌐",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Support & Community server",
                url="https://discord.gg/UGm36FkGDF",
                style=discord.ButtonStyle.link,
                emoji="💬",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="GitHub",
                url="https://github.com/iqnite/eggsplode",
                style=discord.ButtonStyle.link,
                emoji="🐙",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Invite to your server",
                url="https://discord.com/oauth2/authorize?client_id=1325443178622484590",
                style=discord.ButtonStyle.link,
                emoji="🤖",
            )
        )
