"""Parses changelogs written in simple markdown

The markdown has to follow a certain pattern:

# Changelog Title                   <-⊣
                                       ⊦ Header
Introductory lines.                 <-⊣

## [version string] - YYYY-MM-DD      <-⊣
                                        ⊦ Page
### Chunk title             <-⊣         |
- Chunk line                   ⊦ Chunk  |
- !! Important chunk line   <-⊣         |
                                      <-⊣

The Header is ignored. The changelog can have multiple pages. Each page can
have multiple chunks inside. The version string has to be parseable by
.. rst: py:`Version.from_string` OR be `Unreleased`. The date is ignored if the
page title is Unreleased.

Each chunk has a title, which has to be inside of :class:ChunkType. Each chunk
has several lines inside. Lines starting with two exclamation marks are marked
as important.
"""
from __future__ import annotations

import datetime
import logging
import re
from collections.abc import Iterable
from enum import Enum
from pathlib import Path
from typing import Iterable
from typing import List
from typing import Match
from typing import Optional
from typing import Tuple
from typing import Union

from milton.utils.paginator import Paginator

log = logging.getLogger(__name__)


class Version:
    """Represents a version.

    It can be stringified into MAJOR.MINOR.PATCH-TAG-HASH with a `str` call.

    Args:
        major: The major value of the version
        minor: The minor value of the version
        patch: The patch value of the version
        hash_: An optional hash (like a git hash) to be bundled in the version.
        tag: An optional tag to be bundled in the version.

    .. todo: This needs to be checked - why did I choose to unpack the arguments
    like this and not just use default values??
    """

    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        hash_: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> None:
        self.major = major or 0
        self.minor = minor or 0
        self.patch = patch or 0
        self.hash = hash_ or ""
        self.tag = tag or ""

    def __str__(self) -> str:
        base = "".join([str(self.major), ".", str(self.minor), ".", str(self.patch)])
        if self.tag:
            base += f"-{self.tag}"
        if self.hash:
            base += f"-{self.hash}"
        return base

    @staticmethod
    def from_string(string: str) -> Version:
        """Returns a Version object by parsing a string

        The string has to be something like MAJOR.MINOR.PATCH[-TAG[-HASH]].

        Args:
            string: The string to be parsed

        Returns:
            The parsed Version object
        """
        elements = string.split(".")
        assert len(elements) >= 3, ValueError(f"Cannot parse this string {string}")
        if "-" not in elements[-1]:
            return Version(major=elements[0], minor=elements[1], patch=elements[2])

        additional = elements[-1].split("-")
        elements[-1] = additional[0]
        additional = additional[1:]
        if len(additional) == 1:
            return Version(
                major=elements[0],
                minor=elements[1],
                patch=elements[2],
                tag=additional[0],
            )
        elif len(additional) == 2:
            return Version(
                major=elements[0],
                minor=elements[1],
                patch=elements[2],
                tag=additional[0],
                hash_=additional[1],
            )

        raise ValueError("Too many additional elements to unpack")


class Line:
    """Represents a changelog line

    Implements different `__str__` methods based on importance.

    Args:
        content: The content of the line.
        important: Is the line important?
    """

    def __init__(self, content: str, important: bool = False) -> None:
        self.content = content
        self.important = important

    def __str__(self):
        if self.important:
            return f"-\u2757 **{self.content}**"
        return f"- {self.content}"


class ChunkType(Enum):
    """Enum containing the possible chunk types"""

    ADDED = 1
    CHANGED = 2
    DEPRECATED = 3
    REMOVED = 4
    FIXED = 5
    SECURITY = 6
    # Some more just for the game... eventually
    BALANCE = 7


def chunk_type_to_str(chunk_type: ChunkType):
    """Return the chunk type as a string."""
    return {
        1: "Added",
        2: "Changed",
        3: "Deprecated",
        4: "Removed",
        5: "Fixed",
        6: "Security",
        7: "Balance",
    }[chunk_type.value]


class Chunk:
    """Represents a changelog chunk.

    A chunk is a collection of lines under a single type.

    Args:
        lines: A list of :class:`Line` that are inside of this chunk.
        type_: The :class:`ChunkType` for this chunk.
    """

    def __init__(self, lines: List[Line], type_: ChunkType):
        self._type = type_
        self._lines = lines

    def __str__(self):
        result = f">> **{chunk_type_to_str(self._type)}**\n"
        result += "\n".join([str(x) for x in self._lines])
        return result + "\n"


class Page:
    """Represents a page of the changelog.

    A page is a dated collection of chunks associated with a version.
    If the version is unreleased, or omitted,

    Attrs:
        chunks: A list of :class:`Chunk` s of the chunks in the page.
        version: An optional  :class:`Version` that determines the version of
            the page. If left as `None`, it is assumed that the chunk is
            Unreleased.
        date: An optional :class:`datetime.date` of when the page was released.
    """

    def __init__(
        self,
        chunks: List[Chunk],
        version: Optional[Version] = None,
        date: Optional[datetime.date] = None,
    ) -> None:
        self.chunks = chunks
        self.version = version
        self.date = date

        if self.version and self.date is None:
            log.warn(
                (
                    "Version was given, but without a date."
                    " Setting the version to Unreleased."
                )
            )
            self.version = None

    def to_formatted_list(self) -> List[str]:
        """Represents the page as a formatted list of strings from chunks

        The first item in the list is the formatted version number with the
        release date (if present).

        Returns:
            A list of strings containing the rendered title and chunks.
        """
        if self.version:
            result = [f"**Version {self.version} - Released on {self.date}**\n"]
        else:
            result = ["**Unreleased Changes**\n"]
        result.extend([str(x) for x in self.chunks])
        return result

    def __str__(self):
        return "".join(self.to_formatted_list()).strip()


class Changelog:
    """Represents a changelog, with pages, chunks and lines.

    Args:
        title: The title to give the changelog :class:`Paginator` when
            paginating.

    Properties:
        latest_version: The version of the latest page marked as being the
            latest version in the changelog.

    .. todo: The determination of the latest version is a bit dicey.
    """

    def __init__(self, title: str = "") -> None:
        self.title = title
        self._pages: List[Page] = []
        self.__latest_version = Version(0, 0, 0)

    @property
    def latest_version(self):
        return self.__latest_version

    def add_page(self, page: Page, is_latest=True):
        """Adds a page to the changelog.

        Args:
            page: The :class:`Page` to be added in the changelog.
            is_latest: Is this the page for the latest version? If so, updates
                the changelog latest_version.
        """
        self._pages.append(page)
        if is_latest:
            self.__latest_version = page.version
        return page

    def to_paginator(self) -> Paginator:
        """Send the rendered page to a :class:Paginator"""
        out = Paginator(title=self.title)
        for page in self._pages:
            for line in page.to_formatted_list():
                out.add_line(line)
            out.close_page()
        return out


class LineParser:
    """Contains the logic to parse lines

    Is essentially a container for a lot of regex, and then finds the one that
    first matches a line to classify it as something.

    .. note: The order of the regexes in the dictionary is important, as the
        evaluation short-circuits on first match.
    """

    def __init__(self) -> None:
        self.regex = {
            "page_title": re.compile("^## \[(.+)\] - ([0-9]+)-([0-9]+)-([0-9]+)"),
            "unreleased_title": re.compile("^## \[(.+)\]"),
            "chunk_title": re.compile("^### (.+)"),
            "important_line": re.compile("^- !! (.+)"),
            "line": re.compile("^- (.+)"),
        }

    def match(self, line: str) -> Optional[Tuple[str, Match[str]]]:
        """Tests a line against the regexes of the parser.

        Returns:
            A tuple containing the match type and the match itself.
        """
        for key, regex in self.regex.items():
            if (match := regex.search(line)) :
                return key, match


class LineGobbler:
    """A class that can eat up lines and construct a :class:Changelog

    Several of the hidden attributes of the gobbler are sort of caches that
    are built up and then flushed as chunks and pages are constructed.
    These are `__values`, `__lines` and `__chunks`

    Parameters:
        pages: A list of pages created by the gobbler.
    """

    def __init__(self) -> None:
        self.__page_open = False
        self.__chunk_open = False
        self.__values = {}
        self.__chunks = []
        self.__lines = []
        self.pages = []

    def flush(self, *args):
        """Flush the state of gobbler.

        This clears the __values parameter or updates it with the named
        parameters passed to the function. This is useful if some
        parameter has to be preserved from being flushed.

        Also clears the __lines inside the gobbler.
        """
        if args is not None:
            for key in args:
                del self.__values[key]
        else:
            self.__values = {}
        self.__lines = []

    def close_page(self):
        """Close an open page, and store it

        Does nothing is a page is not open.

        Closes any open chunk, constructs a new page and stores it, then
        flushes the state of the gobbler, ready for a new page.

        Also clears the chunk list.
        """
        if not self.__page_open:
            return
        self.close_chunk()
        self.pages.append(
            Page(
                self.__chunks,
                version=self.__values.get("page_version"),
                date=self.__values.get("page_date"),
            )
        )
        self.__chunks = []
        self.__page_open = False
        self.flush()

    def close_chunk(self):
        """Close an open chunk, constructing a Chunk and storing it.

        Does nothing if a chunk is not open.

        Clears the internal state regarding chunks.
        """
        if not self.__chunk_open:
            return
        self.__chunks.append(Chunk(self.__lines, type_=self.__values.get("chunk_type")))
        self.__chunk_open = False
        self.flush("chunk_type")

    def _gobble(self, new: Optional[Tuple[str, Match[str]]]):
        """Gobbles up a new match and adds it to the cache.

        Handles closing and opening pages and chunks, and adding lines to
        chunks.

        Args:
            new: A tuple returned from a :class:LineParser. Any None is ignored.
        """
        if new is None:
            return
        key, match = new

        # I essentially perform things based on the possible match types that
        # are not yet handled, or move on.

        if self.__page_open is False and key not in ("page_title", "unreleased_title"):
            # This is a line that is not in a page, ignore it.
            return

        elif self.__page_open is False and key == "page_title":
            # Opening a new page
            self.__values.update(
                {
                    "page_version": Version.from_string(match.group(1)),
                    "page_date": datetime.date(
                        year=int(match.group(2)),
                        month=int(match.group(3)),
                        day=int(match.group(4)),
                    ),
                }
            )
            self.__page_open = True
            return

        elif self.__page_open is False and key == "unreleased_title":
            # Opening an unreleased page
            self.__page_open = True
            return

        # If we get here, we only get chunk title, lines, or new pages

        if self.__page_open and key in ("page_title", "unreleased_title"):
            # The current page has ended and a new one has to begin.
            self.close_page()
            self._gobble((key, match))
            return

        if key in ("line", "important_line") and self.__chunk_open is False:
            # This line doesn't belong in a chunk, ignore it.
            return

        if self.__chunk_open is False and key == "chunk_title":
            # Opening a chunk
            self.__values.update({"chunk_type": ChunkType[match.group(1).upper()]})
            self.__chunk_open = True
            return

        # If we get to here, we only get lines in a chunk or new chunks

        if self.__chunk_open and key == "chunk_title":
            # A new chunk has to be opened.
            self.close_chunk()
            self._gobble((key, match))
            return

        # If we get to here, we only get lines or important lines

        if key == "important_line":
            self.__lines.append(Line(match.group(1), important=True))
            return

        # If we get to here, we only get lines
        self.__lines.append(Line(match.group(1), important=False))

    def gobble(self, lines: Iterable[str]):
        """Gobbles up a iterable of strings.

        Automatically closes pages at the end, so it's best suited to gobble
        whole changelogs at once.
        """
        parser = LineParser()
        typed = [parser.match(x) for x in lines if x != ""]
        for item in typed:
            if item:
                self._gobble(item)
        self.close_page()


def parse_changelog(path: Union[str, Path]) -> List[Page]:
    """Gobble a changelog file and return the rendered list of pages.

    Args:
        path: Either a string or a Path that represents the path to the target
            changelog file.
    """
    gobbler = LineGobbler()

    with Path(path).open("r") as f:
        lines = f.readlines()
    gobbler.gobble(lines)
    return gobbler.pages


def make_changelog(path: Union[str, Path]) -> Changelog:
    """Make a changelog from a changelog file

    Args:
        path: Either a string or a Path that represents the path to the target
            changelog file.
    """
    pages = parse_changelog(path)
    changelog = Changelog(title="Milton Library Assistant - Changelog")

    if len(pages) == 1:
        changelog.add_page(pages[0])
        return changelog

    for i, page in enumerate(pages):
        if i == 1:
            changelog.add_page(page)
            continue
        changelog.add_page(page, is_latest=False)

    return changelog
