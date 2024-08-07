import enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional
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


@dataclass(frozen=True)
class Case:
    left_title: str
    right_title: str
    code: str
    position: Position

    def __str__(self):
        if self.left_title == "" and self.right_title == "":
            return self.code
        return self.title_str() + "\n" + self.code

    def title_str(self):
        return self.left_title + " ::" + self.right_title


@dataclass(frozen=True)
class SubSection:
    title: str
    description: str
    cases: dict[str, set[Case]]
    position: Position

    def get_all_cases(self) -> set[Case]:
        result = set()
        for case_set in self.cases.values():
            result.update(case_set)
        return result


class ParserState(enum.Enum):
    READING_TITLE = 0
    READING_DESCRIPTION = 1
    READING_CASES = 2


@dataclass
class ParsedPage:
    name: str
    sections: dict[str, SubSection]

    def get_all_section_numbers(self):
        return set(self.sections.keys())

    def __getitem__(self, item) -> Optional[SubSection]:
        assert isinstance(item, str), f"Expected string, got {type(item)}"
        return self.sections.get(item)


class Parser(ABC):
    name: str

    @abstractmethod
    def get_parsed_page(self) -> ParsedPage:
        pass


def add_case(cases: dict[str, set[Case]], case: Case):
    if cases.get(case.title_str()) is None:
        cases[case.title_str()] = {case}
    else:
        cases[case.title_str()].add(case)

@dataclass
class GenericParsedPage:
    name: str
    entries: Dictionnary


class GenericParser(ABC):
    name: str

    @abstractmethod
    def get_parsed_page(self) -> GenericParsedPage:
        pass

