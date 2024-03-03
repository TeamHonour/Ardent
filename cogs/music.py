# Imports.
from __future__ import annotations

from typing import TYPE_CHECKING, List, Self

from decouple import config
from disnake import CommandInter, Option, OptionType
from disnake.ext import commands
from mafic import NodePool, Player, Playlist, Track

from core import Inferno

if TYPE_CHECKING:
    from disnake.abc import Connectable


# The class for handling guild playback.
class MusicPlayer(Player):
    def __init__(self, bot: Inferno, channel: Connectable) -> None:
        super().__init__(bot, channel)

        self.bot = bot
        self.queue: List[Track] = []


# The music cog.
class Music(commands.Cog):
    def __init__(self: Self, bot: Inferno) -> None:
        self.bot = bot

        self.pool = NodePool(self.bot)
        self.bot.loop.create_task(self._add_nodes())

    async def _add_nodes(self: Self) -> None:
        await self.bot.wait_until_ready()
        await self.pool.create_node(
            host=config('LAVA_ADDR', cast=str),
            port=config('LAVA_PORT', cast=int),
            label='MAIN',
            password=config('LAVA_PASS', cast=str),
        )

    async def cog_before_slash_command_invoke(self, inter: CommandInter) -> None:
        inter.player = inter.guild.voice_client
        await inter.response.defer()

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
        name='play',
        description='Plays a song.',
        options=[
            Option('query', 'The song to play.', OptionType.string, required=True),
        ],
        dm_permission=False,
    )
    async def play(self: Self, inter: CommandInter, query: str) -> None:
        if not inter.player:
            inter.player = await self.join(inter)

        tracks = await inter.player.fetch_tracks(query)

        if not tracks:
            return await inter.send('No tracks found.')

        if isinstance(tracks, Playlist):
            tracks = tracks.tracks

            if len(tracks) > 1:
                inter.player.queue.extend(tracks[1:])

        track = tracks[0]
        await inter.player.play(track)
        await inter.send(f'Playing: **{track.title}**')

    @commands.slash_command(
        name='leave',
        description='Stop the player and disconnect from the voice channel.',
        dm_permission=False,
    )
    async def stop(self: Self, inter: CommandInter) -> None:
        if not inter.player:
            return await inter.send("I'm not in a voice channel.")

        await inter.guild.voice_client.disconnect()
        await inter.send('Disconnected.')

    @commands.slash_command(
        name='volume',
        description='Set the volume of the player.',
        options=[
            Option(
                'volume',
                'The volume to set.',
                OptionType.integer,
                min_value=1,
                max_value=150,
                required=True,
            ),
        ],
        dm_permission=False,
    )
    async def volume(self: Self, inter: CommandInter, volume: int) -> None:
        if not inter.player:
            return await inter.send("I'm not in a voice channel.")

        await inter.player.set_volume(volume)
        await inter.send(f'Set the volume to {volume}.')


# Load the cog and the logger.
def setup(bot: Inferno) -> None:
    from logging import INFO, getLogger

    bot.add_cog(Music(bot))
    getLogger('mafic').setLevel(INFO)
