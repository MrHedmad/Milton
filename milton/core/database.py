import copy
import logging
from math import floor
from typing import Any
from typing import Hashable
from typing import Tuple
from typing import Type

import motor.motor_asyncio as aiomotor
import ujson

from milton.core.config import CONFIG

CLIENT: aiomotor.AsyncIOMotorClient = aiomotor.AsyncIOMotorClient()
DB: aiomotor.AsyncIOMotorDatabase = CLIENT[CONFIG.database.identifier]

log = logging.getLogger(__name__)


class Struct:
    """Represents a struct, which enables better support for the future

    This class takes, modifies, and spits out dictionaries based on some
    signature. The signature is a dictionary with instructions on how to
    handle the incoming dictionary.

    By default, keys in the updating dictionary that are not in the blueprint
    are ignored.

    Possible values in the blueprint are of type {operator: value} or None.
    If None, the value attached to this key won't be manipulated, and
    defaults to `None`.

    Possible operators:
        `$default$`:
            `value` will be the default value for this key. If not specified,
            keys will default to `None`.
        `$maximum$`:
            `value` will be the maximum value for this key, and must be of
            a comparable type of the default/stored value.
        `$minimum$`:
            Opposite to `$maximum$`.
        `$round$`: A bool indicating if the value should be rounded (down) to
            the nearest integer. Raises errors if the value cannot be rounded
            down.

    Args:
        blueprint:
            A dictionary with as keys the keys of the output dictionary,
            and as values the dictionary containing instructions on how to
            handle the incoming values.
        keep_undefined:
            If True, updating keys not in the struct are kept

    Attributes:
        resolved: The resolved dictionary after any and all `update`s.
    """

    def __init__(self, blueprint, keep_undefined: bool = False) -> None:
        log.debug(f"Making a new Struct with blueprint {blueprint}")
        self.blueprint = blueprint
        self.defaults = {}
        self.keep_undefined = keep_undefined
        # Sanity check for operators
        valid_operators = ("$default$", "$maximum$", "$minimum$", "$round$", "$type$")

        # Make the default dictionary
        for key, operators in blueprint.items():
            assert (
                isinstance(operators, dict) or operators is None
            ), f"Invalid blueprint operator set '{operators}'"

            if operators is None or not operators:
                log.debug(f"'{key}' has no operators. Setting to None")
                self.defaults.update({key: None})
                continue

            for operator in operators:
                assert operator in valid_operators, f"Invalid operator {operator}"

            for operator, inner in operators.items():
                if operator == "$default$":
                    log.debug(f"'{key}' has for default '{inner}'")
                    self.defaults.update({key: inner})
                    break
            else:
                # No default operator was found here
                log.debug(f"'{key}' has no default. Setting to None")
                self.defaults.update({key: None})

        self.resolved = copy.deepcopy(self.defaults)

    @staticmethod
    def _update(key: Hashable, value: Any, operators: dict) -> dict:
        """Helper to update a single key based on some operator

        Args:
            key: The key to be updated
            value: The value to update
            operators: The operator dictionary to use. See the class docstring
        """
        for operator, setting in operators.items():
            if operator == "$maximum$" and value > setting:
                value = setting
            elif operator == "$minimum$" and value < setting:
                value = setting
            elif operator == "$round$":
                value = floor(setting)
        return {key: value}

    def flush(self) -> None:
        """Resets the resolved value to the default dictionary

        Discards any changes made since instantiation
        """
        self.resolved = copy.deepcopy(self.defaults)

    def update(self, other: dict) -> None:
        """Update the dictionary with new data

        Args:
            other: the dictionary to update with.
        """
        for key, value in other.items():
            try:
                operators = self.blueprint[key]
            except KeyError:
                if self.keep_undefined:
                    self.resolved.update({key, value})
                    continue
                else:
                    log.error(f"Ignoring key '{key}' not in struct blueprint")
                    continue
            if "$default$" in operators and not isinstance(
                operators["$default$"], type(value)
            ):
                log.warn(
                    (
                        "Detected a type different that what specified in the"
                        f" structure for key '{key}'. Expect possible errors."
                    )
                )
            self.resolved.update(self._update(key, value, operators))

    def __getitem__(self, key) -> Any:
        try:
            return self.resolved[key]
        except KeyError:
            raise KeyError(f"KeyError: '{key}'")

    def __setitem__(self, key, value) -> None:
        if key not in self.resolved:
            raise KeyError(f"This struct is frozen. Keyerror: '{key}'")
        self.update({key: value})

    def __repr__(self) -> str:
        return ujson.dumps(self.resolved)


def NotInitializedError(BaseException):
    pass


class Document:
    """Represents a (unique) document in a mongo collection.

    Values are fetched dynamically with an async context manager, and
    returned to the database when the context manager is closed.

    This is a parent class that needs to be derived, and the corresponding
    `collection`, and most probably `struct` class attributes overridden
    to the corresponding collections and structures needed by the specific
    documents.

    Args:
        id_: The id of the document. This is usually the discord snowflake of
            the corresponding document.
            This **must** be a string or MongoDB will complain.

    Attributes:
        data: Either `None` if data was not retrieved from the DB, or an
            instance of `Struct`. You can expect a `Struct` when inside the
            context manager.

    Class Attributes:
        struct: A `Struct` with the blueprint for the document.
            See ..class `struct`. Keys not in the document will be rejected
            and cause a `KeyError`
        collection: The collection to store and retrieve the document to/from

    Example Usage:
        class MiltonSomething(Document):
            struct = Struct({}) # Give it some valid struct. See Struct
            collection = DB.some_collection

        async with MiltonSomething(some_snowflake) as document:
            # Get a value:
            result = document['some_key']
            # Set a value:
            document['some_key'] = value

        # To iterate over the documents in some collection, use the helper
        # function `get_all_from` like such:

        async for id_, document in get_all_from(MiltonSomething):
            # Note how the class was NOT instantiated above!!
            async with document as doc:
                doc['somekey'] = value
                result = doc['somekey']
    """

    struct: Struct = Struct({})
    collection: aiomotor.AsyncIOMotorCollection = None

    def __init__(self, id_: str) -> None:
        assert self.collection is not None, "Cannot istantiate without a collection"
        # The original implementation tried to update __dict__. It's a mess.
        # just keep it like this and use the subscription operator.
        id_ = str(id_)
        self.__id = id_
        self.__signature = {"__id": {"$eq": self.__id}}
        self.data = None

    async def __aenter__(self):
        self.__old = self.__dict__
        retrieved = await self.collection.find_one(self.__signature) or {}
        self.data = self.struct
        self.data.update(retrieved)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.collection.replace_one(
            self.__signature, self.data.resolved, upsert=True
        )
        self.__dict__ = self.__old

    def __getitem__(self, key) -> Any:
        if self.data is None:
            raise NotInitializedError(
                "Document was not initialized. Am I in a context manager?"
            )
        try:
            return self.data[key]
        except KeyError:
            raise KeyError(f"KeyError: '{key}'")

    def __setitem__(self, key, value) -> None:
        if self.data is None:
            raise NotInitializedError(
                "Document was not initialized. Am I in a context manager?"
            )
        if key not in self.data.resolved.keys():
            raise KeyError(f"Keyerror: '{key}'")
        self.data.update({key: value})


######## HOW TO CHANGE THE STRUCTURES OF THE DEFAULT CLASSES ##############
# First, add a new entry in the struct. If it needs a default, maximum
# or minimum, refer to the documentation for ..class`Struct`.
#
# THINK before adding a key - it cannot be changed later!
#
# Something unique would be optimal. If you need to make a TON of new keys,
# It is a good idea to make a custom document with a new collection.
######################### END OF DISCLAIMER ###############################


class MiltonUser(Document):
    """A standard document class for users (discord.Members)"""

    struct: Struct = Struct({})
    collection: aiomotor.AsyncIOMotorCollection = DB.users


class MiltonChannel(Document):
    """A standard document class for Channels (discord.Channel)"""

    struct: Struct = Struct({})
    collection: aiomotor.AsyncIOMotorCollection = DB.channels


class MiltonGuild(Document):
    """A standard document class for Guilds (discord.Guild)"""

    struct: Struct = Struct({"bday_shout_channel": {}, "birthdays": {"$default$": {}}})
    collection: aiomotor.AsyncIOMotorCollection = DB.guilds


class MiltonRoles(Document):
    """A standard document class for Roles (discord.Role)"""

    struct: Struct = Struct({})
    collection: aiomotor.AsyncIOMotorCollection = DB.roles


async def get_all_from(doc: Type[Document]) -> Tuple[str, Document]:
    """An iterator to get all documents in a collection

    Returns tuples of (id, Document) with all the documents.
    Note that the document is already an instance of the corresponding
    document type - no need to call it or pass an id.
    """
    cursor = doc.collection.find()  # Get a cursor with all the things
    async for item in cursor:
        _id = item["_id"]
        yield (_id, doc(_id))


async def milton_users():
    """A wrapper for get_all_from for the User class"""
    return get_all_from(MiltonUser)


async def milton_channels():
    """A wrapper for get_all_from for the Channel class"""
    return get_all_from(MiltonChannel)


async def milton_guilds():
    """A wrapper for get_all_from for the Guilds class"""
    return get_all_from(MiltonGuild)


async def milton_roles():
    """A wrapper for get_all_from for the Roles class"""
    return get_all_from(MiltonRoles)
