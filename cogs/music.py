# Imports.
from __future__ import annotations

from typing import TYPE_CHECKING, List, Self

from decouple import config
from disnake import CommandInter
from disnake.ext import commands
from disnake.ext.commands import Param
from mafic import (
    NodePool,
    Player,
    Playlist,
    Track,
    TrackEndEvent,
)

from core import Core

if TYPE_CHECKING:
    from disnake.abc import Connectable


# The class for handling guild playback.
class MusicPlayer(Player):
    def __init__(self, bot: Core, channel: Connectable) -> None:
        super().__init__(bot, channel)

        self.bot = bot
        self.queue: List[Track] = []


# The music cog.
class Music(commands.Cog):
    def __init__(self: Self, bot: Core) -> None:
        self.bot = bot

        self.pool = NodePool(self.bot)
        self.bot.loop.create_task(self._add_nodes())

        bot._add_logger(logger_name='mafic', file_name='music.log')

    async def _add_nodes(self: Self) -> None:
        await self.bot.wait_until_ready()
        await self.pool.create_node(
            host=config('LAVA_ADDR', cast=str),
            port=config('LAVA_PORT', cast=int),
            label='MAIN',
            password=config('LAVA_PASS', cast=str),
            secure=config('LAVA_SECURE', cast=bool, default=True),
        )

    async def cog_before_slash_command_invoke(self, inter: CommandInter) -> None:
        inter.player = inter.guild.voice_client
        await inter.response.defer()

    @commands.Cog.listener()
    async def on_track_end(self, event: TrackEndEvent[MusicPlayer]):
        if event.player.queue:
            await event.player.play(event.player.queue.pop(0))

    @commands.slash_command(
        name='join', description='Joins your voice channel.', dm_permission=False
    )
    async def join(self: Self, inter: CommandInter) -> MusicPlayer | None:
        if not inter.user.voice or not inter.user.voice.channel:
            return await inter.response.send_message("You're not in a voice channel.")

        channel = inter.user.voice.channel
        player = await channel.connect(cls=MusicPlayer)
        await inter.send(f'Joined {channel.mention}.')
        return player

    @commands.slash_command(
        name='queuesize',
        description='Shows the size of the queue.',
        dm_permission=False,
    )
    async def queuesize(self: Self, inter: CommandInter) -> None:
        if not inter.player:
            return await inter.send("I'm not in a voice channel.")

        await inter.send(f'The queue has {len(inter.player.queue)} tracks.')

    @commands.slash_command(
        name='play',
        description='Plays a song.',
        dm_permission=False,
    )
    async def play(
        self: Self,
        inter: CommandInter,
        query: str = Param(
            description='The description to play.',
        ),
    ) -> None:
        if not inter.player:
            inter.player = await self.join(inter)

        tracks = await inter.player.fetch_tracks(query)
        IS_FROM_LIST: bool = isinstance(tracks, Playlist)
        DEFAULT_INDICATOR: str = 'Playing'

        if not tracks:
            return await inter.send('No tracks were found.')

        if IS_FROM_LIST:
            tracks = tracks.tracks

        track = tracks[0]

        if not inter.player.current:
            await inter.player.play(track)
        else:
            DEFAULT_INDICATOR = 'Enqueued'
            inter.player.queue.append(track)

        if IS_FROM_LIST and len(tracks) > 1:
            inter.player.queue.extend(tracks[1:])
            await inter.send(
                f'{DEFAULT_INDICATOR}: **{track.title}** and {len(tracks) - 1} more tracks.'
            )
        else:
            await inter.send(f'{DEFAULT_INDICATOR}: **{track.title}**')

    @commands.slash_command(
        name='skip',
        description='Skips the current track.',
        dm_permission=False,
    )
    async def skip(self: Self, inter: CommandInter) -> None:
        if not inter.player:
            return await inter.send("I'm not in a voice channel.")

        await inter.player.stop()
        await inter.send('Skipped the current track.')

    @commands.slash_command(
        name='stop',
        description='Stops the player and clears the queue.',
        dm_permission=False,
    )
    async def stop(self: Self, inter: CommandInter) -> None:
        if not inter.player:
            return await inter.send("I'm not in a voice channel.")

        inter.player.queue.clear()
        await inter.player.stop()
        await inter.send('Stopped playback.')

    @commands.slash_command(
        name='leave',
        description='Stop the player and disconnect from the voice channel.',
        dm_permission=False,
    )
    async def leave(self: Self, inter: CommandInter) -> None:
        if not inter.player:
            return await inter.send("I'm not in a voice channel.")

        await inter.player.disconnect()
        await inter.send('Disconnected.')

    @commands.slash_command(
        name='volume',
        description='Set the volume of the player.',
        dm_permission=False,
    )
    async def volume(
        self: Self,
        inter: CommandInter,
        volume: int = Param(
            description='The volume to set.',
            min_value=1,
            max_value=100,
        ),
    ) -> None:
        if not inter.player:
            return await inter.send("I'm not in a voice channel.")

        await inter.player.set_volume(volume)
        await inter.send(f'Set the volume to {volume}.')


# Load the cog and the logger.
def setup(bot: Core) -> None:
    bot.add_cog(Music(bot))
