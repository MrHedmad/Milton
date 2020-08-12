"""This extension handles errors rising from other commands and cogs

Mostly based on (aka completely yanked from) this example:
https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612
"""
import logging
import sys
import traceback

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        log.debug("Some command errored")

        trace = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        trace = trace.strip()

        if hasattr(ctx.command, "on_error"):
            log.debug("Invoked, but will not override command's own error handler")
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                log.debug("Invoked, but will not override cog's own error handler")
                return

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, "original", error)

        ignored = (commands.CommandNotFound,)

        if isinstance(error, ignored):
            log.debug(f"Ignored exception {type(error)} - {error}")
            return

        # Check for specific exceptions to be handled
        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f"{ctx.command} has been disabled.")

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(
                    f"{ctx.command} can not be used in Private Messages."
                )
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.errors.CheckFailure):
            log.debug(f"A command was called, but a check failed. Trace: \n{trace}")

        else:
            # All other Errors not returned come here.

            # Skip the prompt line
            if "CommandInterface" in self.bot.cogs:
                print("")

            log.error(f"Ignoring exception in command {ctx.command}:\n" f"{trace}")

            # Re-print the handle for the CLI cog
            if "CommandInterface" in self.bot.cogs:
                print(">> ", end="")


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
