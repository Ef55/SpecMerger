import enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from content_classes.dictionary import Dictionary


@dataclass(frozen=True)
class Path:
    uri: str
    is_dir: bool


class ParserState(enum.Enum):
    BEFORE_START = -1
    READING_TITLE = 0
    READING_DESCRIPTION = 1
    READING_CASES = 2
    READING_WILDCARD = 3


@dataclass
class ParsedPage:
    name: str
    entries: Dictionary


class Parser(ABC):
    name: str

    @abstractmethod
    def get_parsed_page(self) -> ParsedPage:
        pass

