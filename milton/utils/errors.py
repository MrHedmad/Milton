"""Adds some errors that will be handled by the error handler"""
from typing import Optional


class MiltonError(Exception):
    """Class that is parent of all other Milton-specific errors.

    Args:
        msg: An optional message that describes the error.
    """

    def __init__(self, msg: Optional[str] = None) -> None:
        self.msg = msg


class UserInputError(MiltonError):
    """Raised when an user sent the wrong input."""

    pass
