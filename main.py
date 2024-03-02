# Imports.
from decouple import config
from disnake import Intents

from core import Inferno

# Initialize the bot.
bot = Inferno(
    intents=Intents.all(),
    initial_extensions=[
        "cogs.music",
    ],
)


# Run the bot.
bot.run(config("DISCORD_TOKEN", cast=str))
