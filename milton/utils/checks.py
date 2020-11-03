"""Implements custom checks to be used as decorators"""
from discord.ext.commands import check

from milton.config import CONFIG


def in_guild(id):
    """A Check that sees if the guild is the same as specified."""

    def predicate(ctx):
        return ctx.guild.id == id

    return check(predicate)


def in_channel(id):
    """A Check that sees if the channel is the same as specified."""

    def predicate(ctx):
        return ctx.channel.id == id

    return check(predicate)


def in_test_guild():
    """A Check that sees if the channel is the same as specified."""

    def predicate(ctx):
        return ctx.guild.id == CONFIG.bot.test_server_id

    return check(predicate)
