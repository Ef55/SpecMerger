from abc import ABC, abstractmethod
from enum import Enum

from dataclasses import dataclass
from typing import Optional, Union
from typing import TypeVar, Generic

T = TypeVar('T', bound='Content', covariant=True)


@dataclass(frozen=True)
class GenericPosition(ABC):
    @abstractmethod
    def html_str(self) -> str:
        pass


class GenericReportErrorType(Enum):
    NOT_SAME_STRING = 0
    NOT_SAME_ELEM_IN_SEQ = 1
    MISSING_IN_BAG = 3
    MISSING_ENTRIES = 4
    NOT_SAME_PRIORITIES = 5
    MATCHED_WILDCARDS = 6
    MISMATCHED_TYPES = 7
    MISSPELLED_ENTRY = 8
    REORDERED_ENTRIES = 9
    UNKNOWN_ERROR = 10

    def __str__(self):
        return " ".join(map(lambda word: "" if len(word) == 0 else word[0] + word[1:].lower(), self.name.split("_")))

    def is_error(self):
        return self != GenericReportErrorType.MATCHED_WILDCARDS

    def is_warning(self):
        return self == GenericReportErrorType.MATCHED_WILDCARDS


@dataclass(frozen=True)
class Content(ABC):
    position: Union[Optional[GenericPosition], tuple[Optional[GenericPosition], Optional[GenericPosition]]]


@dataclass(frozen=True)
class String(Content):
    value: str
    chars_useless: str = " \xa0"

    def real_string(self):
        s = self.value
        for c in self.chars_useless:
            s = s.replace(c, "")
        return s

    def __eq__(self, other):
        return isinstance(other, String) and self.real_string() == other.real_string()

    def __hash__(self):
        return hash(self.real_string())

    def __len__(self):
        return len(self.value)

    def __add__(self, other):
        if isinstance(other, String):
            return String(self.position, self.value + other.value)
        if isinstance(other, str):
            return String(self.position, self.value + other)


@dataclass(frozen=True)
class OrderedSeq(Generic[T], Content):
    sequence: list[T]

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.sequence[item]

    def __eq__(self, other):
        return isinstance(other, OrderedSeq) and self.sequence == other.sequence

    def __hash__(self):
        return hash(self.sequence)


@dataclass(frozen=True)
class Bag(Generic[T], Content):
    # represents a set but stored as list to avoid non-determinism
    bag: list[T]

    def __eq__(self, other):
        return isinstance(other, Bag) and set(self.bag) == set(other.bag)

    def __hash__(self):
        return hash(self.bag)


@dataclass(frozen=True)
class Dictionnary(Generic[T], Content):
    entries: dict[str, T]

    def __getitem__(self, item):
        return self.entries.get(item)

    def __eq__(self, other):
        return isinstance(other, Dictionnary) and self.entries == other.entries

    def __hash__(self):
        return hash(self.entries)


@dataclass(frozen=True)
class OrderedDictionnary(Generic[T], Content):
    entries: dict[str, T]
    entries_list: list[str]

    def __getitem__(self, item):
        return self.entries.get(item)

    def __eq__(self, other):
        return (isinstance(other, OrderedDictionnary) and
                self.entries == other.entries and
                self.entries_list == other.entries_list)

    def __hash__(self):
        return hash((self.entries, self.entries_list))


@dataclass(frozen=True)
class WildCard(Generic[T], Content):
    pass

    def __eq__(self, other):
        return other is WildCard

    def __hash__(self):
        return hash(WildCard)


# These classes are used for the alignment and comparison, please do not use them in the parser
@dataclass(frozen=True)
class AlignmentError(Content):
    value: Content
    warning: GenericReportErrorType


@dataclass(frozen=True)
class AlignmentNotPossible(Content):
    left: Optional[Content]
    right: Optional[Content]
    error: GenericReportErrorType
