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


class Parser(ABC):
    name: str

    def get_section(self, section) -> str:
        subsection = self.get_section_for_comparison(section)
        result = subsection.title + "\n" + subsection.description + "\n"
        for case in subsection.cases:
            result += str(case) + "\n"
        return result

    @abstractmethod
    def get_section_for_comparison(self, section) -> SubSection:
        pass

    @abstractmethod
    def get_all_section_numbers(self) -> set[str]:
        pass


def add_case(cases: dict[str, set[Case]], case: Case):
    if cases.get(case.title_str()) is None:
        cases[case.title_str()] = {case}
    else:
        cases[case.title_str()].add(case)
