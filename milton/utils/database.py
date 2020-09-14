"""Where Milton's memory resides

This is neither good nor optimal, it's just fast enough for my own needs.

Eventually we'll migrate to something with balls, like Postgres
"""
import logging
import operator
import os
from collections import defaultdict
from functools import reduce
from pathlib import Path
from typing import Callable
from typing import List
from typing import Union

import ujson
from mpmath import mpf
from mpmath import nstr

from milton.config import CONFIG
from milton.utils.tools import initialize_empty


log = logging.getLogger("milton.memory")

log.info("Memory module is initializing")


def makehash():
    """Fractal dicts, for the win

    I'm sure this won't come bite me in the ass later.
    """
    return defaultdict(makehash)


class Serializer:
    """Object to handle writing and reading from files"""

    def __init__(self, path: Union[Path, str], *args, **kwargs):
        """
        path
            path to json

        Any additional arguments are passed onto to the dumps method
        from the ujson module.
        """
        log.debug(f"Serializer instanced - points to {path}")
        self.path = Path(path)
        self.__kwargs = kwargs

        if not self.path.parent.exists():
            os.makedirs(self.path.parent)

        if not self.path.exists():
            initialize_empty(self.path)

    def write(self, clean: dict):
        """Dirties and writes to file the database"""
        log.debug("Writing dictionary to file.")

        def preprocess(clean: dict) -> dict:
            """Makes a dict dirty to be dumped to file"""
            dirty = {}
            for key, value in clean.items():
                key_tail = key[-4:]
                assert key_tail not in [
                    "_mpf",
                    "_int",
                ], "Key to become dirty has illegal end tag"
                if isinstance(value, dict):
                    value = preprocess(value)
                # I need to remember the types of the values
                elif isinstance(value, mpf):
                    log.debug("Making a mpf dirty")
                    value = nstr(value)
                    key += "_mpf"
                elif isinstance(value, int):
                    log.debug("Making an int dirty")
                    value = str(value)
                    key += "_int"
                dirty.update({key: value})
            return dirty

        def default_to_regular(dictionary):
            if isinstance(dictionary, defaultdict):
                dictionary = {k: default_to_regular(v) for k, v in dictionary.items()}
            return dictionary

        log.debug("Making dictionary dirty")
        dirty = preprocess(default_to_regular(clean))
        log.debug("Dumping dirty dictionary to file")
        with self.path.open("w+") as file:
            ujson.dump(
                dirty,
                file,
                sort_keys=True,
                indent=4,
                escape_forward_slashes=False,
                **self.__kwargs,
            )
        return True

    def read(self) -> defaultdict:
        """Reads and cleans database from file"""
        log.info("Loading dict from file")

        def cleanup(dirty: dict) -> dict:
            """Cleans up a dirty dictionary for usage"""
            clean = {}
            for key, value in dirty.items():
                if isinstance(value, dict):
                    value = cleanup(value)
                elif key.endswith("_mpf"):
                    log.debug("Loading an mpf")
                    key = key[:-4]
                    value = mpf(value)
                elif key.endswith("_int"):
                    log.debug("Loading an int")
                    key = key[:-4]
                    value = int(value)
                clean.update({key: value})

            return defaultdict(makehash, clean)

        log.debug("Reading from file")
        with self.path.open("r") as file:
            dirty = ujson.load(file)
        log.debug("Cleaning dirty dictionary")
        return cleanup(dirty)


class Database:
    """Very basic data storage. Serializes to JSON

    serializer
        serializer object that handles writing and reading from disk
    max_cached_operations
        number of operations before dumping database to memory. If set to None,
        saves every time.
    """

    def __init__(self, serializer: Serializer, max_cached_operations: int = 100):
        log.debug("A database instance is starting")
        self.data = serializer.read()
        self.operations = 0
        self.serializer = serializer
        self.max_cached_operations = max_cached_operations

    def save(self):
        """Save database to file using the Serializer

        Resets the operations counter back to 0
        """
        self.serializer.write(self.data)
        self.operations = 0
        return True

    def count_op(self):
        """Count one operation. If exceeding threshold, save to file"""
        if self.max_cached_operations is None:
            return True

        self.operations += 1
        if self.operations > self.max_cached_operations:
            self.save()
            # The `save` operation takes care of resetting the counter

        return True

    def find(self, map_list: Union[str, List[str]]):
        """Find a value from the dictionary using a map.

        map_list
            A dot-divided or list of strings with the keys to traverse
            the dictionary.
        """
        if isinstance(map_list, str):
            map_list = map_list.split(".")
        return reduce(operator.getitem, map_list, self.data)

    def update(
        self,
        map_list: Union[str, List[str]],
        value,
        operation: Union[str, Callable] = "set",
    ):
        """Update a value in the dictionary using a map

        map_list
            A dot-divided or list of strings with the keys to traverse
            the dictionary. The last value in the map is the key that will
            get updated.

        operation
            Either a string with a common function or a function that takes
            two parameters, the value of the dictionary and the value given
            to the function, and returns a new value that will be used to
            update the database with.

            'set' -> Replaces old value with new value
            'increase' -> old += new
            'decrease' -> old -= new
            'sum' -> same as 'increase'
        """
        log.debug(
            f"Database is updating map: {map_list} with value {value} -"
            f" operation is {operation}"
        )
        if isinstance(map_list, str):
            map_list = map_list.split(".")

        default = mpf(0)

        if operation == "set":
            self.find(map_list[:-1])[map_list[-1]] = value

        elif operation == "increase":
            if self.find(map_list) == makehash():
                self.update(map_list, value=default)
                log.warning(
                    "The database was asked to increase a dict with "
                    f"map {map_list}. The dict was erased and replaced with "
                    f"the default value of {default}."
                )
            self.find(map_list[:-1])[map_list[-1]] += value

        elif operation == "decrease":
            if self.find(map_list) == makehash():
                self.update(map_list, value=default)
                log.warning(
                    "The database was asked to decrease a dict with "
                    f"map {map_list}. The dict was erased and replaced with "
                    f"the default value of {default}."
                )
            self.find(map_list[:-1])[map_list[-1]] -= value

        elif callable(operation):
            update = operation(self.find(map_list), value)
            self.find(map_list[:-1])[map_list[-1]] = update

        else:
            raise ValueError("Unrecognized operation")

        self.count_op()
        return True


DB = Database(Serializer(CONFIG["database"]["path"]))


# What follows is legacy code. Ignore it.


class Localization:
    """Packages tools to switch between locales"""

    def __init__(self, path: Path, default_loc: str = "en"):
        with path.open("r") as file:
            self.data = ujson.load(file)
        self.aviable_locales = list(self.data)
        assert (
            default_loc in self.aviable_locales
        ), "Default locale not aviable in locale.json"
        self.loc = default_loc
        log.info(f"Localization loaded from {path}")

    def find(self, map_list: Union[str, List[str]]):
        """Find a value from the currently selected locale using a map.

        Affected by the locale set in self.switch_loc()

        map_list
            A dot-divided or list of strings with the keys to traverse
            the dictionary.
        """
        if isinstance(map_list, str):
            map_list = map_list.split(".")
        return reduce(operator.getitem, map_list, self.data[self.loc])

    def switch_loc(self, new_loc):
        """Switch the set localization over to another locale

        Affects the calls to self.find() from here on out
        """
        assert (
            new_loc in self.aviable_locales
        ), "Selected locale not aviable in locale.json"
        self.loc = new_loc


# log.info('Loading localization')
# LOC = Localization(Path(CONFIG['locale_path']))
