import logging
import sys
import time
from pathlib import Path
from typing import Callable

import aiohttp
import aiosqlite
import discord
from box import Box
from discord.abc import PrivateChannel
from discord.ext import commands
from discord.ext.commands.bot import when_mentioned, when_mentioned_or
from discord.ext.commands.errors import ExtensionNotFound

from milton import ROOT
from milton.core.changelog_parser import Changelog, Version, make_changelog
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
    so anything passed there can be passed here too.

    Args:
        config: The parsed configuration for the bot.

    Attributes:
        started_on: The ISO timestamp when the bot instance was initiated.
        owner_id: The id snowflake for the owner of the bot.
        db: The aiosqlite connection to the milton DB.
        http_session: An aiohttp session that can be used to make HTTP requests.
        changelog: The changelog object of the bot.
        version: The version of the bot.
    """

    def __init__(self, config: Box, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config: Box = config  # Bundle the config inside the bot itself.
        self.started_on: float = time.time()
        self.owner_id: int = self.config.bot.owner_id
        self.http_session = None

        # move from here to the CHANGELOG file
        path = ROOT.parent
        path /= "CHANGELOG.md"
        self.changelog: Changelog = make_changelog(path)
        self.version: Version = self.changelog.latest_version

    async def setup_hook(self):
        # Add AIOHTTP session
        self.http_session = aiohttp.ClientSession()

        # Add cogs and extensions to be loaded
        log.debug("Loading default extensions")

        essentials = ["cli", "error_handler", "debug"]

        # Essential extensions
        for cog in essentials:
            try:
                await self.load_extension(f"milton.core.cogs.{cog}")
            except ExtensionNotFound as e:
                log.exception(e)
                continue

        for cog in CONFIG.bot.startup_extensions:
            try:
                await self.load_extension(f"milton.cogs.{cog}")
            except ExtensionNotFound as e:
                log.exception(e)
                continue

        await self.tree.sync()

        db_path = Path(CONFIG.database.path).expanduser().absolute()
        initialize_db = not db_path.exists()

        self.db: aiosqlite.Connection = await aiosqlite.connect(db_path)

        await self.migrate(initialize_db)

    async def on_ready(self):
        log.info(f"Logged in as {self.user}. Ready.")

    async def migrate(self, initialize=False):
        migrations = list((ROOT / "schemas").iterdir())
        migrations.remove([x for x in migrations if x.name == "__init__.py"][0])
        migrations.sort(key=lambda x: x.stem)

        if initialize:
            log.info("Initializing new empty DB.")
            initial_script = [x for x in migrations if x.name == "0.sql"][0]

            await self.db.executescript(initial_script.read_text())
            log.info("DB initialized.")

        async with self.db.execute("SELECT version FROM version") as cursor:
            db_version = await cursor.fetchone()
            db_version = db_version[0]

        latest_version = int(migrations[-1].stem)
        if db_version == latest_version:
            log.info("No migrations to apply.")
            return
        elif db_version > latest_version:
            log.info(
                f"The DB is in the future! db: {db_version}, migration: {latest_version}"
            )

        log.info("Found migrations to apply.")
        to_apply = migrations[(db_version + 1) :]
        log.info(f"Applying {len(to_apply)} migration(s).")
        for migration in to_apply:
            log.debug(f"Applying migration {migration}...")
            await self.db.executescript(migration.read_text())
            await self.db.commit()

        log.info("Done migrating database to new schema.")

    async def add_cog(self, cog: commands.Cog):
        await super().add_cog(cog)
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
        if self.http_session:
            log.info("Closing AIOHTTP session...")
            await self.http_session.close()

        log.info("Closing database connection...")
        await self.db.close()

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


def run_bot():
    log.debug("Making the Milton Bot instance")

    intents = discord.Intents.all()

    milton = Milton(
        config=CONFIG,
        command_prefix=_get_prefix,
        activity=discord.Game(name="with " + CONFIG.prefixes.guild + "help"),
        case_insensitive=True,
        intents=intents,
    )

    # Run the client
    milton.run()
