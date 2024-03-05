# Imports.
from decouple import config
from disnake import CommandInter, OptionChoice
from disnake.ext import commands
from disnake.ext.commands import Param

from core import Core

# Required environment variables.
DISCORD_OWNER_ID = config('DISCORD_OWNER_ID', cast=int)


# The Dev cog.
class Dev(commands.Cog):
    EXTENSIONS = []

    def __init__(self, bot: Core) -> None:
        self.bot = bot

        for ext in bot.extensions:
            self.EXTENSIONS.append(ext)

    @commands.slash_command(name='ping', description='Pong!', dm_permission=False)
    async def ping(self, inter: CommandInter) -> None:
        await inter.send(f'Pong! ({self.bot.latency * 1000:.0f}ms)')

    @commands.slash_command(
        name='reload',
        description='Reload a cog.',
        dm_permission=False,
    )
    @commands.check(lambda inter: inter.author.id == DISCORD_OWNER_ID)
    async def reload(
        self,
        inter: CommandInter,
        name: str = Param(
            description='The name of the cog.',
            choices=[OptionChoice(ext, ext) for ext in EXTENSIONS],
        ),
    ) -> None:
        try:
            self.bot.reload_extension(name)
        except Exception as e:
            await inter.send(f'Failed to reload cog: {e}')
        else:
            await inter.send('Cog reloaded.')


# Load the cog.
def setup(bot: Core) -> None:
    bot.add_cog(Dev(bot))