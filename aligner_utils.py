from abc import ABC, abstractmethod
from enum import Enum

from dataclasses import dataclass
from typing import Optional, Union

from error_warning_count import ErrorWarningCount


@dataclass(frozen=True)
class Position(ABC):
    @abstractmethod
    def html_str(self) -> str:
        pass


class ReportErrorType(Enum):
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
        return self != ReportErrorType.MATCHED_WILDCARDS

    def is_warning(self):
        return self == ReportErrorType.MATCHED_WILDCARDS


@dataclass(frozen=True)
class Content(ABC):
    position: Union[Optional[Position], tuple[Optional[Position], Optional[Position]]]

    @abstractmethod
    def to_text(self, indenting: int) -> str:
        pass

    @abstractmethod
    def to_html(self, is_in_error: bool) -> str:
        pass

    @abstractmethod
    def count_errors(self) -> ErrorWarningCount:
        pass

    def render_positions_html(self) -> str:
        if not self.position:
            return ""
        if isinstance(self.position, Position):
            return ", <div> POS: " + self.position.html_str() + "</div>"
        return ", <div> POS: " + ", ".join(
            self.position[i].html_str() for i in range(2) if self.position[i]) + "</div>"
