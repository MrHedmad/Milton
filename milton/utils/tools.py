"""Collection of utility functions used around the bot"""
import logging
import random
from datetime import datetime
from datetime import time
from datetime import timedelta
from difflib import get_close_matches
from pathlib import Path
from typing import List
from typing import Mapping
from typing import Union

import async_timeout
from aiohttp import ClientSession

log = logging.getLogger(__name__)

# Yanked from the python discord bot
def recursive_update(original: Mapping, new: Mapping) -> Mapping:
    """Recursively update nested dictionaries

    Helper method which implements a recursive `dict.update`
    method, used for updating the original configuration with
    configuration specified by the user.

    Args:
        original: A mapping to be updated recursively.
        new: A mapping used to update the original with, recursively.

    Returns:
        The updated mapping.
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


def get_random_line(path: Union[str, Path]) -> str:
    """Returns a random line in a file. Ignores empty lines.

    The implementation has to load the whole file into memory, therefore is not
    suited for very very large files.

    Args:
        path: Either a string or a :class:`pathlib.Path` that represents the
            path to the file to open.

    Returns:
        The line retrieved from the file as a string.
    """
    with Path(path).open("r") as f:
        items = [a for a in f if a != ""]
    return random.choice(items)


def initialize_empty(path: Union[str, Path], content: str = "{}") -> True:
    """Create an empty file to target path.

    Args:
        path: Either a string or a :class:`pathlib.Path` that represents the
            path to the file to open.

    Returns:
        True
    """
    log.debug(f"Creating an empty file @ {path} with {content} content")
    with Path(path).open("w+") as f:
        f.write(content)
    return True


def glob_word(query: str, words: List[str], *args, **kwargs):
    """Return the closests matching word in a list to a query

    Other parameters are sent to the get_close_matches function.

    Args:
        query: The string to search for close matched
        words: The list of possible matches

    Returns:
        The matched string or None if nothing is found.
    """
    globbed = get_close_matches(query, words, 1, *args, **kwargs) or None
    # Need to do this in two steps as `get_close_matches` can return
    # an empty list
    if isinstance(globbed, list):
        globbed = globbed[0]

    assert isinstance(globbed, str)
    return globbed


async def fetch(session: ClientSession, url: str, params: Mapping = {}):
    """Fetch a result from an url using an aiohttp client session

    Args:
        session: The session to be used for the http call.
        url: The url to be fetched.
        params: Any params that are passed to the request.

    Returns:
        The fetched string.
    """
    async with async_timeout.timeout(10):
        async with session.get(url, params=params) as response:
            return await response.text()


def timediff(now: time, then: time) -> timedelta:
    """Calculates the difference between two times.

    Returns:
        The time difference between now and then.
    """
    # You cannot subtract times directly, so I just do this horribleness
    today = datetime.now().date()
    now = datetime.combine(today, now)
    then = datetime.combine(today, then)

    return now - then
