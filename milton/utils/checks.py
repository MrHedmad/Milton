"""Implements custom checks to be used as decorators"""
from typing import Callable

from discord.ext.commands import check

from milton.core.config import CONFIG


def in_guild(id) -> Callable:
    """A Check that sees if the guild is the same as specified.

    Args:
        id: The id of the guild to check for
    """

    def predicate(ctx):
        return ctx.guild.id == id

    return check(predicate)


def in_channel(id) -> Callable:
    """A Check that sees if the channel is the same as specified.

    Args:
        id: The id of the channel to check for
    """

    def predicate(ctx):
        return ctx.channel.id == id

    return check(predicate)


def in_test_guild() -> Callable:
    """A Check that sees if the message was sent in the test guild.

    The test guild is the one specified in the configuration.

    TODO: What if no guild is specified? This just crashes
    """

    def predicate(ctx):
        return ctx.guild.id == CONFIG.bot.test_server_id

    return check(predicate)
