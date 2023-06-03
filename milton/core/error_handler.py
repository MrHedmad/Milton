"""This extension handles errors rising from other commands and cogs

Mostly based on (aka completely yanked from) this example:
https://github.com/PaulMarisOUMary/Discord-Bot/blob/main/cogs/errors.py
"""
import logging

import discord
from discord import app_commands
from discord.ext import commands

from milton.core.bot import Milton
from milton.core.errors import MiltonInputError

log = logging.getLogger(__name__)


class Errors(commands.Cog, name="errors"):
    """Cog to handle errors.

    This cog hadles all errors that are not caught in the single cogs.
    This means that we want it to:
        - Handle very common errors, like commands not found or
          missing/invalid arguments;
        - Handle internal bot errors that could arise;
        - Handle informing the user of what went wrong if an unhandled
          error does eventually arise.

    The cog handles both shlash commands and normal commands.
    """

    def __init__(self, bot: Milton) -> None:
        self.bot = bot
        bot.tree.error(coro=self.__dispatch_to_app_command_handler)

        self.crash_emoji = "💀"
        self.handled_emoji = "🔥"

        self.default_error_message = (
            self.crash_emoji + " An undefined error occured. "
            "If I find out more, I'll update this message."
        )

    async def __dispatch_to_app_command_handler(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        self.bot.dispatch("app_command_error", interaction, error)

    async def __respond_to_interaction(self, interaction: discord.Interaction) -> bool:
        try:
            await interaction.response.send_message(
                content=self.default_error_message, ephemeral=True
            )
            return True
        except discord.errors.InteractionResponded:
            return False

    @commands.Cog.listener("on_error")
    async def get_error(self, event, *args, **kwargs):
        """Error handler"""
        log.error(
            f"! Unexpected Internal Error: (event) {event}, (args) {args}, (kwargs) {kwargs}."
        )

    @commands.Cog.listener("on_command_error")
    async def get_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        """This function handles errors coming from commands."""
        # Handle HybridCommand cogs
        try:
            if ctx.interaction:
                await self.__respond_to_interaction(ctx.interaction)
                edit = ctx.interaction.edit_original_message
                if isinstance(error, commands.HybridCommandError):
                    error = error.original  # Access to the original error
            else:
                discord_message = await ctx.send(self.default_error_message)
                edit = discord_message.edit

            log.exception(error)

            async def comm(msg, include_emoji=True):
                msg = self.handled_emoji + " " + msg if include_emoji else msg
                await edit(content=msg)

            raise error

        except MiltonInputError as e:
            await comm(f"Sorry, I cannot parse your input: {e}")

        except Exception as e:
            match e:
                case commands.ConversionError:
                    await comm(e)
                case commands.UserInputError:
                    await comm(
                        f"Missing Input: `{ctx.clean_prefix}{ctx.command.name}` <{'><'.join(ctx.command.clean_params)}"
                    )
                case commands.MemberNotFound | commands.UserNotFound:
                    await comm(f"Member `{str(e).split(' ')[1]}` not found.")
                case commands.BadArgument | commands.BadUnionArgument | commands.BadLiteralArgument | commands.ArgumentParsingError:
                    await comm(f"{e}")
                case commands.CommandNotFound:
                    await comm(f"Command {e.split(' ')[1]} not found.")
                case commands.PrivateMessageOnly:
                    await comm(
                        f"This command cannot be used in a server. Send me a direct message instead!"
                    )
                case commands.NoPrivateMessage:
                    await comm(
                        "This command cannot be used in private messages, only a server."
                    )
                case commands.NotOwner:
                    await comm("You must be the owner of the bot to use this command.")
                case commands.MissingPermissions:
                    await comm(
                        f"You cannot run this command. You require the following permissions: `{'` `'.join(e.missing_permissions)}`"
                    )
                case commands.BotMissingPermissions:
                    await comm(
                        f"I miss permissions in order to run this: `{'` `'.join(e.missing_permissions)}`"
                    )
                case commands.CheckAnyFailure | commands.MissingRole | commands.BotMissingRole | commands.MissingAnyRole | commands.BotMissingAnyRole:
                    await comm(f"{e}")
                case commands.NSFWChannelRequired:
                    await comm(f"This must only be used in a NSFW channel.")
                case commands.DisabledCommand:
                    await comm(f"This command is disabled. Sorry!")
                case commands.CommandInvokeError:
                    await comm(f"Ivalid invoke: {e.original}")
                case commands.CommandOnCooldown:
                    await comm(
                        f"Command is on cooldown, wait `{str(d_error).split(' ')[7]}`!"
                    )
                case commands.MaxConcurrencyReached:
                    await comm(
                        (
                            "Max concurrency reached."
                            f"Max concurrent invokers allowed: `{e.number}` per `{e.per}`."
                        )
                    )
                case commands.HybridCommandError:
                    await self.get_app_command_error(ctx.interaction, e)
                case _:
                    # Do not log the exception here. It is already logged above.
                    await comm(f"Unrecognized error!\n{e}")

    @commands.Cog.listener("on_app_command_error")
    async def get_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        """App command Error Handler
        doc: https://discordpy.readthedocs.io/en/master/interactions/api.html#exception-hierarchy
        """
        try:
            await self.__respond_to_interaction(interaction)
            edit = interaction.edit_original_response

            async def comm(msg, include_emoji=True):
                msg = self.handled_emoji + " " + msg if include_emoji else msg
                await edit(content=msg)

            log.exception(error)

            raise error

        except MiltonInputError as e:
            await comm(f"Cannot parse your input: {e}")

        except Exception as e:
            match type(e):
                case app_commands.CommandInvokeError:
                    if isinstance(e.original, discord.errors.InteractionResponded):
                        await comm(f"{e.original}")
                    elif isinstance(e.original, discord.errors.Forbidden):
                        await comm(f"`{type(e.original).__name__}` : {e.original.text}")
                    else:
                        await comm(f"`{type(e.original).__name__}` : {e.original}")
                case app_commands.CheckFailure:
                    if isinstance(e, app_commands.errors.CommandOnCooldown):
                        await comm(
                            f"Command is on cooldown, wait `{str(e).split(' ')[7]}` !"
                        )
                    else:
                        await comm(f"`{type(e).__name__}` : {e}")
                case app_commands.CommandNotFound:
                    await comm(
                        (
                            "Wait a moment... That command does not exist! "
                            "I might be out of sync. It should solve itself out, "
                            "but if it does not, please let the devs know!"
                        )
                    )
                case _:
                    # Do not log.exception(e) here, it is already done above.
                    pass

    @commands.Cog.listener("on_view_error")
    async def get_view_error(
        self, interaction: discord.Interaction, error: Exception, item: any
    ):
        """View Error Handler"""
        try:
            raise error
        except discord.errors.Forbidden:
            pass
        except Exception as e:
            log.exception(e)

    @commands.Cog.listener("on_modal_error")
    async def get_modal_error(self, interaction: discord.Interaction, error: Exception):
        """Modal Error Handler"""
        try:
            raise error
        except discord.errors.Forbidden:
            pass
        except Exception as e:
            log.exception(e)


async def setup(bot: Milton):
    await bot.add_cog(Errors(bot))
