"""Provide a cli for additional control"""
import copy
import logging
from asyncio.tasks import current_task
from difflib import get_close_matches
from inspect import cleandoc
from typing import AnyStr
from typing import Coroutine
from typing import Mapping
from typing import Optional

from aioconsole import ainput
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands.errors import ExtensionAlreadyLoaded
from discord.ext.commands.errors import ExtensionNotFound
from discord.ext.commands.errors import ExtensionNotLoaded
from discord.ext.commands.errors import NoEntryPointError

from milton.bot import Milton
from milton.utils.database import DB
from milton.utils.tools import glob_word
from milton.utils.tools import initialize_empty

log = logging.getLogger(__name__)


def clean_docstring(docs: AnyStr) -> AnyStr:
    """Cleans the docstring of some command

    Cleans the indentation with `cleandoc` from `inspect`, and
    then removes all newline characters. For use in the CLI help command.

    TODO: Make this better
    """
    docs = cleandoc(docs)
    return docs.replace("\n", " ")


class CommandInterface(commands.Cog):
    """A cog to add the command line interface to the bot"""

    global prompt

    def __init__(self, bot: Milton, prompt: AnyStr = ">> ") -> None:
        self.bot: Milton = bot
        self._actions: Mapping = {}
        self._descriptions: Mapping = {}
        self._prompt: AnyStr = prompt

        self.add_option(self.help_option, trigger="help", desc="Print this list")

        self.run.start()

    def cog_unload(self):
        self.run.cancel()

    async def help_option(self) -> None:
        """Implement the default help message"""
        print("Here are the aviable commands:")
        for command, desc in self._descriptions.items():
            print("\t" + command, "-", clean_docstring(desc))

    def add_option(
        self,
        action: Coroutine,
        desc: Optional[AnyStr] = None,
        trigger: Optional[AnyStr] = None,
    ) -> None:
        trigger = trigger or action.__name__
        desc = desc or cleandoc(action.__doc__) or "N/A"

        log.debug(f'Prompter added an option with trigger "{trigger}"')

        if trigger in self._actions:
            log.warn(f"{trigger} was overwritten.")

        self._actions[trigger] = action
        self._descriptions[trigger] = desc

    @tasks.loop(seconds=1)
    async def run(self) -> None:
        log.debug("Starting the CLI service")
        while True:
            command = await ainput(self._prompt)

            log.debug(f'Got a CLI command, "{command}"')
            command = command.lower().split()

            globbed = glob_word(command[0], self._actions)

            if globbed != command[0]:
                print(f'Globbed from "{command[0]}" to "{globbed}".')

            try:
                await self._actions[globbed](*command[1:])
            except KeyError:
                print(f'{globbed} is not a valid command. Try "help"')
            except TypeError as e:
                print(f"Wrong number of arguments given to {command[0]}")

    @run.before_loop
    async def before_cli(self):
        await self.bot.wait_until_ready()


def setup(bot):
    """Setup this extension."""
    interface = CommandInterface(bot)

    @interface.add_option
    async def shutdown():
        """Gently shuts down the bot instance, cleaning up everything"""
        log.info("Milton is shutting down.")
        log.info("Closing loop")
        await bot.close()

    @interface.add_option
    async def flush_log():
        """Deletes the (latest) log file, for debug purposes"""
        initialize_empty(bot.config.logs.path, "")
        log.info("Log was flushed from CLI")

    @interface.add_option
    async def save():
        """Save the database to the file specified in the config"""
        log.info("Database save triggered from CLI")
        DB.save()

    @interface.add_option
    async def update(*args):
        """Update a map in the dictionary.

        Same as using DB.update(). The order of the args must be map, value and
        operation.
        """
        log.info(
            (
                "The CLI sent a DB update order. "
                f"Updating the map {args[0]} with value {args[1]} and operation {args[2]}"
            )
        )
        DB.update(*args)

    @interface.add_option
    async def extensions():
        """Lists all the extensions and cogs currently loaded in the bot"""
        print("Currently loaded extensions:")
        for ext in interface.bot.extensions:
            print("\t" + ext)
        print("Currently loaded cogs:")
        for cog in interface.bot.cogs:
            print("\t" + cog)

    @interface.add_option
    async def loadext(ext_path):
        """Load an extension. For instance, 'milton.cogs.tests'"""
        print(f"Attempting to load extension {ext_path}")
        try:
            interface.bot.load_extension(ext_path)
        except ExtensionNotFound:
            print(f'The extension "{ext_path}" could not be found')
        except ExtensionAlreadyLoaded:
            print(f'The extension "{ext_path}" is already loaded')
        except NoEntryPointError:
            print(
                f'The extension "{ext_path}" has no entrypoint. Define a `setup` function'
            )
        except Exception as e:
            log.exception("Unexpected exception while loading extension")
        else:
            print(f"Successfully loaded extension {ext_path}")

    @interface.add_option
    async def unloadext(ext_path):
        """Unload an extension. For instance, 'milton.cogs.tests'"""
        print(f"Attempting to unload extension {ext_path}")
        try:
            interface.bot.unload_extension(ext_path)
        except ExtensionNotLoaded:
            print(f'The extension "{ext_path}" was not loaded')
        except Exception as e:
            log.exception("Unexpected exception while loading extension")
        else:
            print(f"Successfully unloaded extension {ext_path}")

    @interface.add_option
    async def reloadcogs():
        """Reloads all the cogs in the bot - for testing"""
        print("Reloading all cogs...")
        # Iterating over the ext while they reload is not a good idea
        current_ext = [x for x in interface.bot.extensions]
        for ext in current_ext:
            print(f"Attempting to reload {ext}")
            try:
                interface.bot.reload_extension(ext)
            except Exception as e:
                log.exception("Unexpected exception while reloading extension")
            else:
                print(f"Successfully reloaded extension {ext}")
        print("Finished reloading extensions")

    bot.add_cog(interface)
