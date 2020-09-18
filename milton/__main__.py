import logging

import discord

from milton.bot import _get_prefix
from milton.bot import Milton
from milton.config import CONFIG

log = logging.getLogger(__name__)

log.debug("Making the Milton Bot instance")

milton = Milton(
    config=CONFIG,
    command_prefix=_get_prefix,
    activity=discord.Game(name="with " + CONFIG.prefixes.guild + "help"),
    case_insensitive=True,
)

# Add cogs and extensions to be loaded

log.debug("Loading default extensions")

to_load = [
    # Essential extensions
    "milton.cogs.cli",
    "milton.cogs.error_handler",
    "milton.cogs.debug",
    # Other extensions
    "milton.cogs.meta",
    "milton.cogs.toys",
    "milton.cogs.birthday",
]

for cog in to_load:
    milton.load_extension(cog)

# Run the client
milton.run()
