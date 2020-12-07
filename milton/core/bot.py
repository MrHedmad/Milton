import logging
import sys
import time
from pathlib import Path
from typing import Callable

import aiohttp
import discord
import motor.motor_asyncio as aiomotor
from box import Box
from discord.abc import PrivateChannel
from discord.ext import commands
from discord.ext.commands.bot import when_mentioned
from discord.ext.commands.bot import when_mentioned_or

from milton import ROOT
from milton.core.changelog_parser import Changelog
from milton.core.changelog_parser import make_changelog
from milton.core.changelog_parser import Version
from milton.core.config import CONFIG

log = logging.getLogger(__name__)

INTRO = r"""
__/\\\\____________/\\\\_______/\\\___________________/\\\\\\\\\____________
__\/\\\\\\________/\\\\\\______\/\\\_________________/\\\\\\\\\\\\\_________
___\/\\\//\\\____/\\\//\\\______\/\\\________________/\\\/////////\\\_______
____\/\\\\///\\\/\\\/_\/\\\______\/\\\_______________\/\\\_______\/\\\______
_____\/\\\__\///\\\/___\/\\\______\/\\\_______________\/\\\\\\\\\\\\\\\_____
______\/\\\____\///_____\/\\\______\/\\\_______________\/\\\/////////\\\____
_______\/\\\_____________\/\\\______\/\\\_______________\/\\\_______\/\\\___
________\/\\\_____________\/\\\______\/\\\\\\\\\\\\\\____\/\\\_______\/\\\__
_________\///______________\///_______\//////////////_____\///________\///__

Welcome to the Milton Library Assistant!
"""


class Milton(commands.Bot):
    """There is only me, and you, and an eternity of doubt.

    This is the Bot instance of Milton. It inherits from :class:`commands.Bot`
    so anything passed there can be passed here.

    Args:
        config: The parsed configuration for the bot.

    Attributes:
        started_on: The ISO timestamp when the bot instance was initiated.
        owner_id: The id snowflake for the owner of the bot.
        DbClient: The client to use to call the MongoDB instance. This
            shouldn't be used, in most cases.
        DB: The database related to Milton as set in the configs.
            This should be used to access collections inside the database.
        http_session: An aiohttp session that can be used to make HTTP requests.
        changelog: The changelog object of the bot.
        version: The version of the bot.
    """

    def __init__(self, config: Box, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config: Box = config  # Bundle the config inside the bot itself.
        self.started_on: float = time.time()
        self.owner_id: int = self.config.bot.owner_id
        self.http_session: aiohttp.ClientSession = aiohttp.ClientSession()

        # move from here to the CHANGELOG file
        path = ROOT.parent
        path /= "CHANGELOG.md"
        self.changelog: Changelog = make_changelog(path)
        self.version: Version = self.changelog.latest_version

    async def on_ready(self):
        logon_str = f"Logged in as {self.user}"
        print(logon_str)
        log.info(logon_str)

    def add_cog(self, cog: commands.Cog):
        super().add_cog(cog)
        log.info(f"Added cog {cog.qualified_name}")

    def run(self, *args, **kwargs):
        """Runs the bot with the token from the config.

        Anything passed to :class:`commands.Bot` can be passed here too.
        """
        if self.config.bot.token is None:
            raise ValueError("Bot cannot start without a token")
        log.info("Milton is starting.")
        print(INTRO)

        super().run(self.config.bot.token, *args, **kwargs)

    async def close(self):
        """Gently closes down the bot instance.

        Also handles closing down the various async processes attached to the
        bot that need to be explicitly closed.
        """
        # This may get called twice due to some internal thing in discord.py.
        # I cannot do much other than sit and watch it doing twice.
        log.info("Closing AIOHTTP session...")
        await self.http_session.close()

        log.info("Closing bot loop...")
        await super().close()

    async def on_error(self, event_method, *args, **kwargs):
        """Handle unexpected errors raised at the bot level.

        Every unhandled exception not in a cog ends up here.
        """
        # Skip the prompt line
        if "CommandInterface" in self.cogs:
            print("")

        info = sys.exc_info()
        log.exception("Ignoring exception at the bot level", exc_info=info)

        # Re-print the handle for the CLI cog
        if "CommandInterface" in self.cogs:
            print(">> ", end="")


async def _get_prefix(bot: Milton, message: discord.Message) -> Callable:
    """Returns the function to correctly get the prefix based on context.

    Attributes:
        bot: The bot to get the prefox for
        message: The message that is triggering the prefix retrieving.

    Returns:
        A callable function that returns the prefix.
    """
    if isinstance(message.channel, PrivateChannel):
        return when_mentioned(bot, message)
    return when_mentioned_or(CONFIG.prefixes.guild)(bot, message)
