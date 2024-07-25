from abc import ABC
from dataclasses import dataclass
from typing import Iterable

import frozenlist


@dataclass
class Content(ABC):
    pass


@dataclass
class String(Content):
    value: str
    line_diff: bool


@dataclass
class OrderedSeq(Content):
    sequence: Iterable[Content]


@dataclass
class Bag(Content):
    bag: set[Content]


@dataclass
class Dictionnary(Content):
    entries: dict[str, Content]
    prioritized_entries: bool
    # can be [] if prioritized entries is false
    entries_priorities: list[tuple[int, str]]

