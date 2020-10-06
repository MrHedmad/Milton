"""This parses the changelog for the project"""
import datetime
import logging
import re
from enum import Enum
from pathlib import Path
from typing import AnyStr
from typing import List
from typing import Optional

from milton.utils.paginator import Paginator

log = logging.getLogger(__name__)


class Version:
    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        hash_: AnyStr = None,
        tag: AnyStr = None,
    ) -> None:
        self.major = major or 0
        self.minor = minor or 0
        self.patch = patch or 0
        self.hash = hash_ or ""
        self.tag = tag or ""

    def __str__(self):
        base = "".join([str(self.major), ".", str(self.minor), ".", str(self.patch)])
        if self.tag:
            base += f"-{self.tag}"
        if self.hash:
            base += f"-{self.hash}"
        return base

    @staticmethod
    def from_string(string):
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
    def __init__(self, content: AnyStr, important: bool) -> None:
        self.content = content
        self.important = important

    def __str__(self):
        """The line, in discordified markdown"""
        if self.important:
            return f"-❗ **{self.content}**"
        return f"- {self.content}"


class ChunkType(Enum):
    ADDED = 1
    CHANGED = 2
    DEPRECATED = 3
    REMOVED = 4
    FIXED = 5
    SECURITY = 6
    # Some more just for the game... eventually
    BALANCE = 7


def chunk_type_to_str(chunk_type: ChunkType):
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
    def __init__(self, lines: List[Line], type_: ChunkType):
        self._type = type_
        self._lines = lines

    def __str__(self):
        result = f">> **{chunk_type_to_str(self._type)}**\n"
        result += "\n".join([str(x) for x in self._lines])
        return result + "\n"


class Page:
    def __init__(
        self,
        chunks: List[Chunk],
        version: Optional[Version],
        date: Optional[datetime.date],
    ) -> None:
        self.chunks = chunks
        self.version = version
        self.date = date

    def to_formatted_list(self):
        """To a formatted list to be parsed by a paginator"""
        if self.version:
            result = [f"**Version {self.version} - Released on {self.date}**\n"]
        else:
            result = ["**Unreleased Changes**\n"]
        result.extend([str(x) for x in self.chunks])
        return result

    def __str__(self):
        return "".join(self.to_formatted_list()).strip()


class Changelog:
    def __init__(self) -> None:
        self._pages = []
        self.__latest_version = Version(0, 0, 0)

    @property
    def latest_version(self):
        return self.__latest_version

    def add_page(self, page: Page, is_latest=True):
        self._pages.append(page)
        if is_latest:
            self.__latest_version = page.version

        return page

    def to_paginator(self):
        out = Paginator(title="Milton Library Assistant - Changelog")
        for page in self._pages:
            for line in page.to_formatted_list():
                out.add_line(line)
            out.close_page()
        return out


class LineParser:
    def __init__(self) -> None:
        self.regex = {
            "page_title": re.compile("^## \[(.+)\] - ([0-9]+)-([0-9]+)-([0-9]+)"),
            "unreleased_title": re.compile("^## \[(.+)\]"),
            "chunk_title": re.compile("^### (.+)"),
            "important_line": re.compile("^- !! (.+)"),
            "line": re.compile("^- (.+)"),
        }

    def match(self, line):
        for key, regex in self.regex.items():
            if (match := regex.search(line)) :
                return key, match


class LineGobbler:
    def __init__(self) -> None:
        self.__page_open = False
        self.__chunk_open = False
        self.__values = {}
        self.__chunks = []
        self.__lines = []
        self.pages = []

    def flush(self, *args):
        if args is not None:
            for key in args:
                del self.__values[key]
        else:
            self.__values = {}
        self.__lines = []

    def close_page(self):
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
        self.__chunks.append(Chunk(self.__lines, type_=self.__values.get("chunk_type")))
        self.__chunk_open = False
        self.flush("chunk_type")

    def _gobble(self, new):
        """Gobbles up a new match and adds it to the glob"""
        key, match = new
        if self.__page_open is False and key not in ("page_title", "unreleased_title"):
            # This is a line that is not in a page, ignore it.
            return
        elif self.__page_open is False and key == "page_title":
            # Opening a page
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

    def gobble(self, iterable):
        for item in iterable:
            if item:
                self._gobble(item)
        self.close_page()


def parse_changelog(path: AnyStr) -> List[Page]:
    gobbler = LineGobbler()
    parser = LineParser()
    with Path(path).open("r") as f:
        lines = f.readlines()

    typed = [parser.match(x) for x in lines if x != ""]

    gobbler.gobble(typed)

    return gobbler.pages


def make_changelog(path: AnyStr) -> Changelog:
    pages = parse_changelog(path)
    changelog = Changelog()

    if len(pages) == 1:
        changelog.add_page(pages[0])
        return changelog

    for i, page in enumerate(pages):
        if i == 1:
            added_version = True
            changelog.add_page(page)
            continue
        changelog.add_page(page, is_latest=False)

    return changelog
