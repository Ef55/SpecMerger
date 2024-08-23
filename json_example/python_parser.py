import re
from typing import Optional
from dataclasses import dataclass
import os

from spec_merger.aligner_utils import Position
from spec_merger.content_classes.bag import Bag
from spec_merger.content_classes.dictionary import Dictionary
from spec_merger.content_classes.ordered_dictionary import OrderedDictionnary
from spec_merger.content_classes.string import String
from spec_merger.content_classes.wildcard import WildCard
from spec_merger.utils import Parser, ParsedPage


@dataclass(frozen=True)
class PythonPosition(Position):
    lines_num: tuple[int, int]
    file_name: str

    def html_str(self) -> str:
        return f"<a download href='file://{os.path.abspath(self.file_name)}'><b>{self.file_name.split('/')[-1]}</b>: {self.lines_num[0]}-{self.lines_num[1]}</a>"


def is_special_comment(comment: str):
    r = re.compile(r"# << .*? >>( TITLE| WILDCARD| INPUTS|)")
    return r.match(comment)


def strip_special_comment(comment: str) -> tuple[str, Optional[str]]:
    without_start = comment.replace("# << ", "")
    if not without_start.endswith(">>"):
        special = without_start[without_start.index(">>") + 3:]
    else:
        special = None
    return (without_start[:without_start.index(" >>")], special)


class PythonParser(Parser):
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.parsed_page: Optional[ParsedPage] = None
        self.name = "PythonParser"
        self.regex_algorithm = re.compile(r"([0-9][a-z]?\.)(?: (.*)|)")

    def parse(self):
        current_section_title = ""
        in_algo = False
        current_enum = []
        sections = {}
        current_section = {}
        line_start = 0
        instructions = {}
        instruction_orders = []
        with open(self.file_name, "r") as f:
            lines = f.read().splitlines(keepends=False)
        for i, line in enumerate(lines):
            real_line = line.lstrip(" ").rstrip(" \n")
            if not real_line.startswith("#") or not is_special_comment(real_line):
                continue
            comment, speciality = strip_special_comment(real_line)
            if speciality == "TITLE":
                pos = PythonPosition((line_start, i), self.file_name)
                if current_section_title == "":
                    current_section_title = comment
                    continue
                if instructions != {}:
                    current_section["algorithm"] = OrderedDictionnary(None, instructions, instruction_orders)
                    instructions = {}
                    instruction_orders = []
                if current_enum != []:
                    first_line = min(current_enum, key=lambda s: s[1])[1]
                    strings = list(map(lambda x: x[0], current_enum))
                    current_section["bulletpoints"] = Bag(PythonPosition((first_line, i), self.file_name), strings)
                    current_enum = []
                line_start = i
                sections[current_section_title] = Dictionary(pos, current_section)
                current_section_title = comment
                current_section = {}
            # There are only wildcards in the instructions
            elif speciality == "WILDCARD":
                pos = PythonPosition((line_start, i), self.file_name)
                is_a_match = self.regex_algorithm.match(comment)
                instruction_orders.append(is_a_match.group(1))
                instructions[is_a_match.group(1)] = WildCard(None)
            elif speciality == "INPUTS":
                inputs = dict(map(lambda x: (x.split(":")[0], String(None, x.split(":")[1])), comment.split(", ")))
                current_section["inputs"] = Dictionary(PythonPosition((i, i), self.file_name), inputs)
            else:
                if comment.startswith("-"):
                    s = String(PythonPosition((i, i), self.file_name), comment[2:])
                    current_enum.append((s, i))
                    continue
                is_a_match = self.regex_algorithm.match(comment)
                if not is_a_match:
                    current_section["description"] = String(PythonPosition((i, i), self.file_name), comment)
                    continue
                else:
                    instr_title = is_a_match.group(1)
                    instruction_orders.append(instr_title)
                    instructions[instr_title] = String(None, is_a_match.group(2))
        pos = PythonPosition((line_start, len(lines)), self.file_name)
        if instructions != {}:
            current_section["algorithm"] = OrderedDictionnary(None, instructions, instruction_orders)
        if current_enum != []:
            first_line = min(current_enum, key=lambda s: s[1])[1]
            strings = list(map(lambda x: x[0], current_enum))
            current_section["bulletpoints"] = Bag(PythonPosition((first_line, i), self.file_name), strings)
        sections[current_section_title] = Dictionary(pos, current_section)
        return ParsedPage(self.name, Dictionary(None, sections))

    def get_parsed_page(self) -> ParsedPage:
        if self.parsed_page is None:
            self.parsed_page = self.parse()
        return self.parsed_page
