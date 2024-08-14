import enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from comparer_utils import Dictionnary, OrderedSeq, String, Bag, Content


@dataclass(frozen=True)
class Path:
    uri: str
    is_dir: bool


@dataclass(frozen=True)
class Position(ABC):
    @abstractmethod
    def html_str(self) -> str:
        pass


class ParserState(enum.Enum):
    BEFORE_START = -1
    READING_TITLE = 0
    READING_DESCRIPTION = 1
    READING_CASES = 2
    READING_WILDCARD = 3


@dataclass
class GenericParsedPage:
    name: str
    entries: Dictionnary


class GenericParser(ABC):
    name: str

    @abstractmethod
    def get_parsed_page(self) -> GenericParsedPage:
        pass

