import logging

import discord
from discord.ext.commands.errors import ExtensionError

from milton.bot import _get_prefix
from milton.bot import Milton
from milton.config import CONFIG

log = logging.getLogger(__name__)

log.debug("Making the Milton Bot instance")

intents = discord.Intents.all()

milton = Milton(
    config=CONFIG,
    command_prefix=_get_prefix,
    activity=discord.Game(name="with " + CONFIG.prefixes.guild + "help"),
    case_insensitive=True,
    intents=intents,
)

# Add cogs and extensions to be loaded

log.debug("Loading default extensions")

to_load = [
    # Essential extensions
    "cli",
    "error_handler",
    "debug",
    # Other extensions
    "meta",
    "toys",
    "birthday",
    "penguins",
]

for cog in to_load:
    try:
        milton.load_extension(f"milton.cogs.{cog}")
    except ExtensionError as e:
        log.exception(e)
        continue

# Run the client
milton.run()
