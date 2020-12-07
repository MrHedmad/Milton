"""This file loads the configuration for the bot.

This is heavily based on the discord python server bot.
"""
import logging
from pathlib import Path

import yaml
from box import Box

from milton.utils.tools import recursive_update

log = logging.getLogger(__name__)

try:
    with Path("./milton/default-config.yml").open("r") as stream:
        _DEFAULT_CONFIG = yaml.safe_load(stream)
except FileNotFoundError as err:
    log.error("Cannot find the default config file (default-config.yml)")
    raise

try:
    with Path("./config.yml").open("r") as stream:
        log.info("Searching and loading config file")
        CONFIG = yaml.safe_load(stream)
except FileNotFoundError as err:
    log.info("No config file found. Using default parameters")
    CONFIG = {}

# I use a box to avoid accidentally updating + using the cool class attribute
# access which in my opinion makes perfect sense for static variables.
CONFIG: Box = Box(recursive_update(_DEFAULT_CONFIG, CONFIG), frozen_box=True)
