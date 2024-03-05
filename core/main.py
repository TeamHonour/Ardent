# Imports.
from __future__ import annotations

import traceback
from typing import Any, List, Self

import disnake
from disnake import CommandInter
from disnake.ext import commands


# Set up the base bot class.
class Core(commands.AutoShardedInteractionBot):
    def __init__(self: Self, *args: Any, initial_extensions: List[str], **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        for extension in initial_extensions:
            self.load_extension(extension)

    async def _update_presence(self: Self) -> None:
        """
        Updates the rich presence of IgKnite.
        """

        await self.change_presence(
            status=disnake.Status.dnd,
            activity=disnake.Activity(
                type=disnake.ActivityType.listening,
                name=f'commands inside {len(self.guilds)} server(s)!',
            ),
        )

    async def on_connect(self: Self) -> None:
        print(f'\nConnected to Discord as: {self.user}')

    async def on_ready(self: Self) -> None:
        await self._update_presence()
        print("Flight controls OK, we're online and ready.")

    async def on_guild_join(self: Self, _: disnake.Guild) -> None:
        await self._update_presence()

    async def on_guild_remove(self: Self, _: disnake.Guild) -> None:
        await self._update_presence()

    async def on_message(self: Self, message: disnake.Message) -> None:
        if message.author == self.user:
            return

    async def on_slash_command_error(self: Self, inter: CommandInter, error: Exception) -> None:
        traceback.print_exception(type(error), error, error.__traceback__)
        await inter.send(f'An error occurred: {error}')
