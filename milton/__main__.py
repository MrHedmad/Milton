import logging

import discord
from discord.ext.commands.errors import ExtensionError

from milton.core.bot import _get_prefix
from milton.core.bot import Milton
from milton.core.config import CONFIG

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

essentials = ["cli", "error_handler", "debug"]

# Essential extensions
for cog in essentials:
    try:
        milton.load_extension(f"milton.core.cogs.{cog}")
    except ExtensionError as e:
        log.exception(e)
        continue

for cog in CONFIG.bot.startup_extensions:
    try:
        milton.load_extension(f"milton.cogs.{cog}")
    except ExtensionError as e:
        log.exception(e)
        continue

# Run the client
milton.run()
