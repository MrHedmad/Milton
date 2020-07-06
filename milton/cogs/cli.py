"""Provide a cli for additional control"""

from milton.bot import Bot
from typing import AnyStr, Coroutine, Mapping, Optional

from aioconsole import ainput
from discord.ext import tasks, commands
import logging

from milton.utils.tools import initialize_empty

log = logging.getLogger(__name__)


class Prompter:
    """A very simple implementation of a prompt"""

    def __init__(self, prompt: AnyStr = ">> ") -> None:
        log.debug("initiating a prompter")


class CommandInterface(commands.Cog):
    """A cog to add the command line interface to the bot"""

    global prompt

    def __init__(self, bot: Bot, prompt: AnyStr = ">> ") -> None:
        self.bot: Bot = bot
        self._actions: Mapping = {}
        self._descriptions: Mapping = {}
        self._prompt: AnyStr = prompt

        self.add_option(self.help_option, trigger="help", desc="Print this list")

        self.provide_cli.start()

    def cog_unload(self):
        self.provide_cli.cancel()

    async def help_option(self) -> None:
        """Implement the default help message"""
        print("Here are the aviable commands:")
        for command, desc in self._descriptions.items():
            print("\t" + command, "-", desc)

    def add_option(
        self,
        action: Coroutine,
        desc: Optional[AnyStr] = None,
        trigger: Optional[AnyStr] = None,
    ) -> None:
        trigger = trigger or action.__name__
        desc = desc or action.__doc__ or "N/A"

        log.debug(f'Prompter added an option with trigger "{trigger}"')

        if trigger in self._actions:
            log.warn(f"{trigger} was overwritten.")

        self._actions[trigger] = action
        self._descriptions[trigger] = desc

    async def run(self) -> None:
        log.debug("Starting the CLI service")
        while True:
            command = await ainput(self._prompt)
            command = command.lower()
            log.debug(f'Got a CLI command, "{command}"')
            try:
                await self._actions[command]()
            except KeyError as err:
                print(f'{command} is not a valid command. Try "help"')

    @tasks.loop(seconds=1)
    async def provide_cli(self):
        await self.run()

    @provide_cli.before_loop
    async def before_cli(self):
        await self.bot.wait_until_ready()


def setup(bot):
    """Setup this extension."""
    interface = CommandInterface(bot)

    @interface.add_option
    async def shutdown():
        """Gently shuts down the bot instance, cleaning up everything"""
        log.info("Milton is shutting down.")
        # TODO: Check if we need to close down the SQL instance too
        log.info("Closing loop")
        await bot.close()

    @interface.add_option
    async def flush_log():
        """Deletes the (latest) log file, for debug purposes"""
        initialize_empty(bot.config.logs.path, "")
        log.info("Log was flushed from CLI")

    bot.add_cog(interface)
