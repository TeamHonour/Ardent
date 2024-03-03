# Imports.
from __future__ import annotations

from typing import TYPE_CHECKING, List, Self

from decouple import config
from disnake import CommandInter, Option, OptionType
from disnake.ext import commands
from mafic import NodePool, Player, Playlist, Track, TrackEndEvent

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
        options=[
            Option('query', 'The song to play.', OptionType.string, required=True),
        ],
        dm_permission=False,
    )
    async def play(self: Self, inter: CommandInter, query: str) -> None:
        # very basic voice safety ngl
        if not inter.player:
            inter.player = await self.join(inter)

        # query for tracks at the very start
        tracks = await inter.player.fetch_tracks(query)
        IS_FROM_LIST: bool = False
        IS_PLAYING_FROM_LIST: bool = False

        # checks if there are any tracks
        if not tracks:
            return await inter.send('No tracks were found.')

        # checks if the query was a playlist or not
        # if yes then set IS_FROM_LIST to True for later use
        if isinstance(tracks, Playlist):
            IS_FROM_LIST = True
            tracks = tracks.tracks

        # get the first track
        track = tracks[0]

        # if the player is not playing then play the track
        if not inter.player.current:
            if IS_FROM_LIST:  # if the query was a playlist
                IS_PLAYING_FROM_LIST = True  # identify that the music is playing from a playlist

            await inter.player.play(track)  # play the track

        # if IS_FROM_LIST is True and the length of the tracks is greater than 1
        # then extend the queue with the rest of the tracks
        if IS_FROM_LIST and (tracks) > 1:
            inter.player.queue.extend(tracks[1:] if IS_PLAYING_FROM_LIST else tracks)
            await inter.send(f'Playing: **{track.title}** and {len(tracks) - 1} more tracks.')
        else:
            await inter.send(f'Playing: **{track.title}**')

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
                max_value=200,
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
