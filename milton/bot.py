import logging
import sys

from discord.ext import commands
from box import Box

from milton.config import CONFIG

log = logging.getLogger(__name__)


class Bot(commands.Bot):
    """The normal discord bot, with some extra logging sprinkled in."""

    def __init__(self, config: Box, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.config = config  # Bundle the config inside the bot itself.

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
        super().run(self.config.bot.token, *args, **kwargs)

    async def close(self):
        await super().close()
        log.info("The bot instance is closing. Goodbye!")

    async def on_error(self, event_method, *args, **kwargs):
        """Pass the error to the logger instead of the normal behavior"""
        _, exception, _ = sys.exc_info()
        log.error(exception)
