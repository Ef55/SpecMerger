import enum
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass(frozen=True)
class Path:
    uri: str
    is_dir: bool


@dataclass(frozen=True)
class Position:
    @abstractmethod
    def html_str(self) -> str:
        pass


@dataclass(frozen=True)
class Case:
    left_title: str
    right_title: str
    code: str

    def __str__(self):
        if self.left_title == "" and self.right_title == "":
            return self.code
        return self.left_title + " ::" + self.right_title + "\n" + self.code


@dataclass(frozen=True)
class SubSection:
    title: str
    description: str
    cases: set[Case]
    position: Position


class ParserState(enum.Enum):
    READING_TITLE = 0
    READING_DESCRIPTION = 1
    READING_CASES = 2


class Parser(ABC):
    def get_section(self, section) -> str:
        subsection = self.get_section_for_comparison(section)
        result = subsection.title + "\n" + subsection.description + "\n"
        for case in subsection.cases:
            result += str(case) + "\n"
        return result

    @abstractmethod
    def get_section_for_comparison(self, section) -> SubSection:
        pass
