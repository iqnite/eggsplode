"""
Contains a class for paginating through a list of items.
"""

import discord

from eggsplode.strings import MAX_COMPONENTS, format_message
from eggsplode.ui.base import BaseView


class PaginatedView(BaseView):
    MAX_SECTIONS = (MAX_COMPONENTS - 5) // 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_items = []
        self.page_number = 0
        self.page_container = discord.ui.Container()
        self.pagination_row = discord.ui.ActionRow()

    @property
    def page_count(self) -> int:
        return (len(self.page_items) + self.MAX_SECTIONS - 1) // self.MAX_SECTIONS

    def update_pagination(self, items: list[discord.ui.ViewItem]):
        self.page_items = items
        if self.page_count:
            self.page_number = min(self.page_number, self.page_count - 1)
        else:
            self.page_number = 0
        if self.page_container in self.children:
            self.remove_item(self.page_container)
        self.page_container = discord.ui.Container()
        start = self.page_number * self.MAX_SECTIONS
        end = (self.page_number + 1) * self.MAX_SECTIONS
        for item in self.page_items[start:end]:
            self.page_container.add_item(item)
        if self.page_items:
            self.add_item(self.page_container)
        if self.pagination_row in self.children:
            self.remove_item(self.pagination_row)
        self.pagination_row = discord.ui.ActionRow()
        if self.page_count > 1:
            if self.page_count > 2 or self.page_number == 0:
                self.create_page_button(1)
            if self.page_count > 2 or self.page_number == 1:
                self.create_page_button(-1)
            self.add_item(self.pagination_row)

    def create_page_button(self, step: int):
        to_page = self.page_number + step
        if to_page < 0:
            to_page = self.page_count - 1
        elif to_page >= self.page_count:
            to_page = 0

        async def callback(interaction: discord.Interaction):
            self.page_number = to_page
            self.update_pagination(self.page_items)
            await interaction.edit(view=self)

        button = discord.ui.Button(
            label=format_message("page_button", to_page + 1),
            style=discord.ButtonStyle.secondary,
            emoji="◀️" if step < 0 else "▶️",
        )
        button.callback = callback
        self.pagination_row.add_item(button)
