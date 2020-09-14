"""Adds some errors that will be handled by the error handler"""
from typing import AnyStr
from typing import Optional


class MiltonError(Exception):
    """Class that is parent of all other Milton-specific errors

    Takes an optional message which can be used further in processing.
    """

    def __init__(self, msg: Optional[AnyStr] = None) -> None:
        self.msg = msg


class UserInputError(MiltonError):
    """Raised when an user sent the wrong input.

    It is parsed by the Error Handler.
    """

    pass
