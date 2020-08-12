import logging
import sys
import time

import discord
from box import Box
from discord.abc import PrivateChannel
from discord.ext import commands
from discord.ext.commands.bot import when_mentioned
from discord.ext.commands.bot import when_mentioned_or

from milton.config import CONFIG
from milton.utils.database import DB
from milton.utils.intro import make_intro

log = logging.getLogger(__name__)


class Milton(commands.Bot):
    """The normal discord bot, with some extra logging sprinkled in."""

    def __init__(self, config: Box, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = config  # Bundle the config inside the bot itself.
        self.started_on = time.time()
        self.owner_id = CONFIG.bot.owner_id

    async def on_ready(self):
        logon_str = f"Logged in as {self.user}"
        print(logon_str)
        log.info(logon_str)

    def add_cog(self, cog):
        super().add_cog(cog)
        log.info(f"Added cog {cog.qualified_name}")

    def run(self, *args, **kwargs):
        """Runs the bot with the token from the config"""
        if self.config.bot.token is None:
            raise ValueError("Bot cannot start without a token")
        log.info("Milton is starting.")
        make_intro()

        super().run(self.config.bot.token, *args, **kwargs)

    async def close(self):
        await super().close()
        log.info("The bot instance is closing. Goodbye!")

    async def on_error(self, event_method, *args, **kwargs):
        """Pass the error to the logger instead of the normal behavior"""
        # Skip the prompt line
        if "CommandInterface" in self.cogs:
            print("")

        info = sys.exc_info()
        log.exception("Ignoring exception at the bot level", exc_info=info)

        # Re-print the handle for the CLI cog
        if "CommandInterface" in self.cogs:
            print(">> ", end="")


async def _get_prefix(bot, message):
    """Retrieve the prefix for this context"""
    if isinstance(message.channel, PrivateChannel):
        return when_mentioned(bot, message)
    return when_mentioned_or(CONFIG.prefixes.guild)(bot, message)
