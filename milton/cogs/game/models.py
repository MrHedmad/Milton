"""This module hosts all the models used by the game"""
from typing import Any

import motor.motor_asyncio as aiomotor


class UniqueDocument:
    # The struct contains a dict of the attributes and respective default values.
    struct: dict = None
    # The collection is the collection used to acces the DB
    collection: aiomotor.AsyncIOMotorCollection = None

    def __init__(self, id_) -> None:
        """Represents a database entity.

        This class can be used to more flexibly modify documents in the
        database. All unique documents have an ID and a collection. When they
        are opened, the document is fetched from the collection based on its
        id. If it is not present in the collection, it is created.

        When the document is closed, it is resent to the database to be saved.

        To avoid errors, only values in the `struct` class parameter can be
        accessed and changed. Every other parameter will cause an AttributeError
        like usual.
        """
        self.__id: int = id_
        self.__data = None

    async def __aenter__(self):
        pass

    async def __aexit__(self):
        pass

    def __getattr__(self, name: str) -> Any:
        if self.__data is None:
            raise EnvironmentError(
                "Cannot access attributes before entering a context manager"
            )

        if name in self.struct:
            return self.__data.get(name, self.struct[name])
        else:
            raise AttributeError("Cannot find specified attribute in struct.")
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        pass
