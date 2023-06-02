"""This file loads the configuration for the bot.

This is heavily based on the discord python server bot.
"""
import logging
import tomllib as tml
from pathlib import Path

from box import Box

from milton.utils.tools import recursive_update

log = logging.getLogger(__name__)

DEFAULTS = {
    "bot": {
        "token": None,
        "pagination_timeout": 300,
        "test_server_id": None,
        "startup_extensions": [
            "meta",
            "toys",
            "birthday",
            "math_render",
            "rss",
            "pdf_render",
        ],
    },
    "database": {"path": "~/.milton/database.sqlite"},
    "logs": {"path": "~/.milton/logs/mla.log", "file_level": 10, "stdout_level": 30},
    "prefixes": {"guild": "!!"},
    "emojis": {
        "trash": "\u274c",
        "next": "\u25b6",
        "back": "\u25c0",
        "last": "\u23e9",
        "first": "\u23ea",
        "stop": "\u23f9",
    },
    "birthday": {"when": 10},
    "announcements": {"email": None, "app_password": None},
}

try:
    with Path("~/.config/milton/milton.toml").expanduser().open("rb") as stream:
        log.info("Searching and loading config file (/.config/milton/milton.toml).")
        CONFIG = tml.load(stream)
except FileNotFoundError as err:
    log.info("No config file found. Using default parameters.")
    CONFIG = DEFAULTS
except tml.TOMLDecodeError as e:
    log.error("Failed to parse TOML configuration file: {e}")
    log.warning("Failed to load custom config. Using default parameters.")
    CONFIG = DEFAULTS

# I use a box to avoid accidentally updating + using the cool class attribute
# access which in my opinion makes perfect sense for static variables.
CONFIG: Box = Box(recursive_update(DEFAULTS, CONFIG), frozen_box=True)
