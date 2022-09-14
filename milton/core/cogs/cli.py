"""Provide a cli for additional control"""
import logging
from inspect import cleandoc
from typing import Coroutine
from typing import Mapping
from typing import Optional

from aioconsole import ainput
from discord.errors import HTTPException
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands.errors import ExtensionAlreadyLoaded
from discord.ext.commands.errors import ExtensionNotFound
from discord.ext.commands.errors import ExtensionNotLoaded
from discord.ext.commands.errors import NoEntryPointError
from tabulate import tabulate

from milton.core.bot import Milton
from milton.utils.tools import glob_word
from milton.utils.tools import initialize_empty

log = logging.getLogger(__name__)


def clean_docstring(docs: str) -> str:
    """Cleans the docstring of some command

    Cleans the indentation with `cleandoc` from `inspect`, and
    then removes all newline characters. For use in the CLI help command.

    TODO: Make this better
    """
    docs = cleandoc(docs)
    return docs.replace("\n", " ")


class CommandInterface(commands.Cog):
    """A cog to add the command line interface to the bot"""

    global prompt  # I know, I know - who cares

    def __init__(self, bot: Milton, prompt: str = ">> ") -> None:
        self.bot: Milton = bot
        self._actions: Mapping = {}
        self._descriptions: Mapping = {}
        self._prompt: str = prompt

        self.add_option(self.help_option, trigger="help", desc="Print this list")

        self.bot.loop.create_task(self.run())

    def cog_unload(self):
        self.run.cancel()

    async def help_option(self) -> None:
        """Implement the default help message"""
        print("Here are the available commands:")
        for command, desc in self._descriptions.items():
            print("\t" + command, "-", clean_docstring(desc))

    def add_option(
        self,
        action: Coroutine,
        desc: Optional[str] = None,
        trigger: Optional[str] = None,
    ) -> None:
        trigger = trigger or action.__name__
        desc = desc or cleandoc(action.__doc__) or "N/A"

        log.debug(f'Prompter added an option with trigger "{trigger}"')

        if trigger in self._actions:
            log.warn(f"{trigger} was overwritten.")

        self._actions[trigger] = action
        self._descriptions[trigger] = desc

        # This return is to reuse the function in other functions
        return action

    async def run(self) -> None:
        await self.bot.wait_until_ready()
        log.debug("Starting the CLI service")
        while True:
            command = await ainput(self._prompt)

            if len(command) == 0:
                continue

            log.debug(f'Got a CLI command, "{command}"')
            command = command.lower().split()

            globbed = glob_word(command[0], self._actions) or command[0]

            if globbed is None:
                print(f"Command `{command}` not recognized. Try `help`")
                continue

            if globbed != command[0]:
                print(f'Globbed from "{command[0]}" to "{globbed}".')

            try:
                await self._actions[globbed](*command[1:])
            except KeyError:
                print(f'{globbed} is not a valid command. Try "help"')
            except TypeError as e:
                print(e)
                print(f"Wrong number of arguments given to {command[0]}")


async def setup(bot):
    """Setup this extension."""
    interface = CommandInterface(bot)

    @interface.add_option
    async def shutdown():
        """Gently shuts down the bot instance, cleaning up everything"""
        log.info("The CLI has told Milton to shutdown.")
        await bot.close()

    @interface.add_option
    async def flush_log():
        """Deletes the (latest) log file, for debug purposes"""
        initialize_empty(bot.config.logs.path, "")
        log.info("Log was flushed from CLI")

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
            await interface.bot.load_extension(ext_path)
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
            await interface.bot.unload_extension(ext_path)
        except ExtensionNotLoaded:
            print(f'The extension "{ext_path}" was not loaded')
        except Exception as e:
            log.exception("Unexpected exception while loading extension")
        else:
            print(f"Successfully unloaded extension {ext_path}")

    @interface.add_option
    async def reloadext(ext_path):
        """Reload an extension. For instance, 'milton.cogs.tests'"""
        if ext_path.startswith("milton.core"):
            print(f"Cannot reload a core cog ({ext_path}).")
            return
        await unloadext(ext_path)
        await loadext(ext_path)

    @interface.add_option
    async def reloadallcogs():
        """Reloads all the cogs in the bot - for testing"""
        print("Reloading all cogs...")
        # Iterating over the ext while they reload is not a good idea
        current_ext = [
            x for x in interface.bot.extensions if not x.startswith("milton.core")
        ]
        for ext in current_ext:
            print(f"Attempting to reload {ext}")
            try:
                await interface.bot.reload_extension(ext)
            except Exception as e:
                log.exception("Unexpected exception while reloading extension")
            else:
                print(f"Successfully reloaded extension {ext}")
        print("Finished reloading extensions")
    
    @interface.add_option
    async def sync():
        """Sync all app commands with Discord"""
        print("Syncing all app commands...")
        try:
            await interface.bot.tree.sync()
        except Exception as e:
            print("Sync failed: {}", e)

    @interface.add_option
    async def listguilds():
        """List the guild that the bot is currently in"""
        print("Guilds MLA is currently in:")
        guilds = list(interface.bot.guilds)
        data = (
            [len(x.members) for x in guilds],
            [x.id for x in guilds],
            [x.name for x in guilds],
        )
        print(
            tabulate(
                # Data has to be rotated 90 degrees
                [list(x) for x in zip(*data[::-1])],
                headers=("Display Name", "Snowflake", "Member Count"),
                tablefmt="grid",
            )
        )

    @interface.add_option
    async def leaveguild(id=None):
        """Leave a guild Milton is in"""
        if id is None:
            print("Did not specify an ID")
            return

        try:
            id = int(id)
        except ValueError:
            print("Cannot cast id to int - is it numeric?")

        guilds = list(interface.bot.guilds)
        ids = [x.id for x in guilds]
        if id not in ids:
            print("Id not recognized. Is it an ID of a guild Milton is in?")

        target = interface.bot.get_guild(id)
        try:
            await target.leave()
        except HTTPException:
            print("Leaving guild failed. Milton might be the owner of the guild.")
        print(f"Left guilds {target.name} with snowflake {target.id}")

    await bot.add_cog(interface)
