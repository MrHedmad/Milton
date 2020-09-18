"""Collection of utility functions"""
import logging
import random
from ast import Str
from difflib import get_close_matches
from itertools import zip_longest
from pathlib import Path
from typing import AnyStr
from typing import List
from typing import Mapping
from typing import Union

import async_timeout
from aiohttp import ClientSession
from discord import TextChannel
from discord.client import Client

log = logging.getLogger(__name__)

# Yanked from the python discord bot
def recursive_update(original: Mapping, new: Mapping) -> None:
    """Recursively update nested dictionaries

    Helper method which implements a recursive `dict.update`
    method, used for updating the original configuration with
    configuration specified by the user.
    """

    for key, value in original.items():
        if key not in new:
            continue

        if isinstance(value, Mapping):
            if not any(isinstance(subvalue, Mapping) for subvalue in value.values()):
                original[key].update(new[key])
            recursive_update(original[key], new[key])
        else:
            original[key] = new[key]

    return original


def get_random_line(file: Union[AnyStr, Path]) -> AnyStr:
    """Returns a random line in a file. Ignores empty lines."""
    with Path(file).open("r") as f:
        items = [a for a in f if a != ""]
    return random.choice(items)


def initialize_empty(path: Union[AnyStr, Path], content: AnyStr = "{}") -> True:
    """Create empty .json file to target path."""
    log.debug(f"Creating an empty file @ {path} with {content} content")
    with Path(path).open("w+") as f:
        f.write(content)
    return True


def fn(number: Union[int, float], threshold: int = 100_000, decimals: int = 2) -> str:
    """Short for 'format number'.

    Takes a number and formats it into human-readable form.
    If it's larger than threshold, formats it into a more compact form.

    Args:
        number: float or int
            Number to format
        threshold: int
            Threshold under which not to format. Defaults at 100_000
        decimals: int
            Number of decimal places to give to the number before formatting.

    Returns:
        String with formatted number.
    """
    if number < threshold:
        return str(round(float(number), decimals))
    return str(number, decimals)


async def push(channel: TextChannel, message: List[str]):
    """Push a message to a channel.

    channel
        Channel to forward message to.
    message
        List of strings to send to channel (from a MsgBuilder probably)
    """
    log.debug(f"Pushing a message of lenght {len(message)} to {channel.id}")
    for item in message:
        await channel.send(item)


class MsgBuilder:
    """Class to build messages to push to chat.

    Parses lists containing messages to send to chat.
    It contains them inside a list of lists for easier parsing.
    """

    def __init__(self):
        # When adding to msg, remember to only add lists of one or more strings
        self.msg = []

    def add(self, line: str):
        """Add a new line to be parsed."""
        if isinstance(line, str):
            line = [line]
        self.msg.append(line)

    def append(self, line: str, sep: str = ""):
        """Appends line to the end of last string in the message.

        Args:
            line: str
                String to append.
            sep: str
                Separator between string and string to be appended.
        """
        if not self.msg:
            self.add(line)
        else:
            self.msg[-1][-1] += sep + line

    def prepend(self, line: str, sep: str = ""):
        """Prepends line to the start of last string in the message.

        Args:
            line: str
                String to append.
            sep: str
                Separator between string and string to be prepended.
        """
        if not self.msg:
            self.add(line)
        else:
            self.msg[-1][-1] = line + sep + self.msg[-1][-1]

    def parse(self):
        """Parses itself as a list of the fewest number of strings possible.

        Doesn't exceed 2000 characters while creating strings to push to chat
        in order to follow Discord's 2000 character limit per message.
        """
        messages = []
        formatted = ""
        for row in self.msg:
            if len(formatted + " ".join(row)) <= 2000:
                formatted += " ".join(row) + "\n"
            else:
                messages.append(formatted.rstrip())
                formatted = " ".join(row) + "\n"
        messages.append(formatted.rstrip())
        log.debug(f"Parsed a message of length {len(messages)}")
        return messages

    def pretty_parse(self, padding=2):
        """Pretty parse the list of words as columns.

        Handles giving each string the correct number of spaces,
        plus adds the back-ticks to mark this message as code (otherwise
        it kind of defeats the purpose of adding the spaces).

        WARNING: This does not check for the 2k character limit like parse()
        does.

        Args:
            padding: int
                Spaces to add in addition to those to make columns equal.
                Defaults to 2
        """
        # Improvement: This doesn't check for the 2k character limit.
        col_widths = [
            max(map(len, col)) for col in zip_longest(*self.msg, fillvalue="")
        ]
        formatted = ""
        for row in self.msg:
            formatted += ("" + padding * " ").join(
                (val.ljust(width) for val, width in zip(row, col_widths))
            )
            formatted += "\n"
        if len(formatted) > 2000:
            log.warning("Formatted string from prettyparse exceeds 2k char limit")
        log.debug("Parsed a pretty message")
        return ["```" + formatted.rstrip() + "```"]


class MsgParser:
    """Small utility to parse messages"""

    def __init__(self, message: str):
        message = message.split()  # This splits @ one or more whitespaces
        self.command = message[0]
        self.args = message[1:]


def glob_word(word: AnyStr, words: List[AnyStr], *args, **kwargs):
    """Return the closests matching word in a list

    If not found, returns the original word. Other parameters are sent to
    the get_close_matches function.
    """
    globbed = get_close_matches(word, words, 1, *args, **kwargs) or word
    # Need to do this in two steps as `get_close_matches` can return
    # an empty list
    if isinstance(globbed, list):
        globbed = globbed[0]

    assert isinstance(globbed, str)
    return globbed


async def fetch(session: ClientSession, url: str, params: Mapping):
    async with async_timeout.timeout(10):
        async with session.get(url, params=params) as response:
            return await response.text()
