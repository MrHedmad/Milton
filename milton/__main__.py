import discord
from discord.abc import PrivateChannel
from discord.ext.commands import when_mentioned_or

from milton.bot import Bot
from milton.config import CONFIG


async def _get_prefix(bot, message):
    """Retrieve the prefix for this context"""
    if isinstance(message.channel, PrivateChannel):
        return when_mentioned_or(CONFIG.prefixes.direct)(bot, message)
    return when_mentioned_or(CONFIG.prefixes.guild)(bot, message)


milton = Bot(
    config=CONFIG,
    command_prefix=_get_prefix,
    activity=discord.Game(name="with " + CONFIG.prefixes.guild + "help"),
    case_insensitive=True,
)

# Add cogs and extensions
milton.load_extension("milton.cogs.cli")

# Run the client
milton.run()
