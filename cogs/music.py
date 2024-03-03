# Imports.
from __future__ import annotations

import asyncio
import itertools
import random
from typing import TYPE_CHECKING, Any, Self

from decouple import config
from disnake import CommandInter
from disnake.ext import commands
from mafic import Node, NodePool, Player

from core import Inferno

if TYPE_CHECKING:
    from disnake.abc import Connectable


# The class which acts as the primary queue system.
class SongQueue(asyncio.Queue):
    def __getitem__(self, item: Any) -> Any | list:
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self) -> Any:
        return self._queue.__iter__()

    def __len__(self) -> int:
        return self.qsize()

    def clear(self) -> None:
        self._queue.clear()

    def shuffle(self) -> None:
        random.shuffle(self._queue)

    def remove(self, index: int) -> None:
        del self._queue[index]


# The class for handling guild playback.
class MusicPlayer(Player):
    def __init__(self, bot: Inferno, channel: Connectable) -> None:
        super().__init__(bot, channel)

        self.bot = bot
        self.queue: SongQueue = SongQueue()


# The music cog.
class Music(commands.Cog):
    def __init__(self: Self, bot: Inferno) -> None:
        self.bot = bot

        self.pool = NodePool(self.bot)
        self.bot.loop.create_task(self._add_nodes())

    async def _add_nodes(self: Self) -> None:
        await self.bot.wait_until_ready()
        await self.pool.create_node(
            host=config("LAVA_ADDR", cast=str),
            port=config("LAVA_PORT", cast=int),
            label="MAIN",
            password=config("LAVA_PASS", cast=str),
        )

    async def cog_before_slash_command_invoke(self, inter: CommandInter) -> None:
        player: MusicPlayer = inter.guild.voice_client
        inter.player = player
        await inter.response.defer()

    @commands.slash_command(
        name="stats",
        description="Returns the music node status for the server.",
        dm_permission=False,
    )
    async def ping(self: Self, inter: CommandInter) -> None:
        node: Node = self.pool.get_node(guild_id=inter.guild_id, endpoint="MAIN")

        await inter.send(
            f"Memory: {node.stats.memory.used}MB / {node.stats.memory.free}MB\n CPU: {node.stats.cpu.system_load} / {node.stats.cpu.lavalink_load}\n"
        )

    @commands.slash_command(
        name="join", description="Joins your voice channel.", dm_permission=False
    )
    async def join(self: Self, inter: CommandInter) -> None:
        if not inter.user.voice or not inter.user.voice.channel:
            return await inter.response.send_message("You're not in a voice channel.")

        channel = inter.user.voice.channel
        await channel.connect(cls=MusicPlayer)
        await inter.send(f"Joined {channel.mention}.")

    @commands.slash_command(
        name="leave",
        description="Stop the player and disconnect from the voice channel.",
        dm_permission=False,
    )
    async def stop(self: Self, inter: CommandInter) -> None:
        if not inter.player:
            return await inter.send("I'm not in a voice channel.")

        await inter.guild.voice_client.disconnect()
        await inter.send("Disconnected.")


# Load the cog and the logger.
def setup(bot: Inferno) -> None:
    from logging import INFO, getLogger

    bot.add_cog(Music(bot))
    getLogger("mafic").setLevel(INFO)
