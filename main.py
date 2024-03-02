# Imports.
from decouple import config
from disnake import Intents

from core import Inferno


# Initialize the bot.
bot = Inferno(
    intents=Intents(guilds=True, voice_states=True),
    initial_extensions=[
        'cogs.music',
    ],
)


# Run the bot.
bot.run(config("DISCORD_TOKEN", cast=str))