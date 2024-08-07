from dataclasses import dataclass
from typing import List, Dict, Tuple
from alectryon.literate import coq_partition, Comment, StringView
import re
import os

from utils import Path, SubSection, Parser, Case, ParserState, Position, ParsedPage, GenericParsedPage
from comparer_utils import GenericPosition, Dictionnary, String, WildCard, OrderedSeq


@dataclass(frozen=True)
class CoqLine:
    file_name: str
    line_number: int
    is_end_comment: bool = False


def get_file_name_without_path(path) -> str:
    return path.split("/")[-1]

def add_case(cases: dict[str, Dictionnary],case: tuple[str,String], key: str):
    lines = OrderedSeq(case[1].position, list(map(lambda x: String(None,x),case[1].value.split("\n"))))
    if cases.get(key) is not None:
        cases[key].entries[case[0]] = case[1]
    else:
        cases[key] = Dictionnary(None, {case[0]: case[1]})

@dataclass(frozen=True)
class GenericCoqPosition(GenericPosition):
    file_positions: Dict[str, Tuple[int, int]]

    def html_str(self) -> str:
        return ", ".join(
            f"<a download href='file://{file_name}'><b>{get_file_name_without_path(file_name)}</b>: {start} - {end}</a>"
            for file_name, (start, end)
            in self.file_positions.items())

    def __hash__(self):
        return hash(self.html_str())


class GenericCOQParser(Parser):
    def __init__(self, files: List[Path], to_exclude: List[Path], parser_name: str = "COQ",
                 title_regex: str = r"(22\.2(?:\.[0-9]{0,2}){1,3})",
                 spec_regex: str = r"^\(\*(\* )?>?>(.|\n)*?<<\*\)$",
                 case_regex: str = r"([a-zA-Z0-9\[\]]+) ::((?:.|\n)*)",
                 algo_regex: str = r"^(?:(?:(?:(?:[1-9][0-9]*)|[a-z]|[ivxlc]+)\.)|\*) .*$",
                 any_title_regex: str = r"^[ -]*?((?:[0-9]+\.)+[0-9]+)(?: .*?|)$"):
        self.sections_by_number = None
        self.comments: list[tuple[str, CoqLine]] = None
        self.all_filenames = None
        self.coq_code = None

        self.name = parser_name
        self.files = files
        self.to_exclude = to_exclude
        self.title_regex = re.compile(title_regex)
        self.any_title_regex = re.compile(any_title_regex, re.MULTILINE)
        self.spec_regex = re.compile(spec_regex)
        self.case_regex = re.compile(case_regex)
        self.algo_regex = re.compile(algo_regex)

    @staticmethod
    def __get_lines_num_from_paragraph(string_view: StringView) -> tuple[int, int]:
        original_string: str = string_view.s
        line_start = original_string.count("\n", 0, string_view.beg) + 1
        line_end = line_start + original_string.count("\n", string_view.beg, string_view.end)
        if original_string[string_view.end] == "\n":
            line_end -= 1
        return line_start, line_end

    @staticmethod
    def __get_line_num(string_view: StringView) -> int:
        return string_view.s.count("\n", 0, string_view.beg) + 1

    def __add_file(self, filename: str, files_dic: dict, all_filenames: list):
        if any([filename.startswith(excluded.uri) for excluded in self.to_exclude]):
            return
        with open(filename, "r") as f:
            coq_file = f.read()
            files_dic[filename] = coq_file
        all_filenames.append(filename)

    def __get_coq_code(self) -> Tuple[Dict[str, str], List[str]]:
        files_dic = {}
        all_filenames = []
        for file in self.files:
            if file.is_dir:
                for root, dirs, files in os.walk(file.uri, topdown=False):
                    for name in files:
                        self.__add_file(os.path.abspath(os.path.join(root, name)), files_dic, all_filenames)
            else:
                self.__add_file(file.uri, files_dic, all_filenames)
        return files_dic, all_filenames

    def __get_comment_lines(self) -> List[tuple[str, CoqLine]]:
        comments = []
        for filename in self.all_filenames:
            file = self.coq_code[filename]
            partition = coq_partition(file)
            for field in partition:
                if isinstance(field, Comment) and self.spec_regex.match(str(field.v)):
                    start_line_num = self.__get_line_num(field.v)
                    for i, line in enumerate(str(field.v).splitlines()):
                        line = self.__parse_comment(line)
                        if line != "":
                            comments.append((line, CoqLine(filename, start_line_num + i)))
                # avoid -1 at start, would have made no sense
                if len(comments) > 0:
                    comments.append(("", CoqLine(filename, -1, True)))
        return comments

    # Completely arbitrary in our case
    def __merge_comments(self, section1: Dictionnary, section2: Dictionnary) -> Dictionnary:
        print("[WARNING] Merge called for ", section1, section2)
        title = section1["title"] if len(section1["title"]) > len(section2["title"]) else section2["title"]
        description_first = section1["description"] if len(section1["description"]) > len(
            section2["description"]) else section2["description"]
        description_second = section1["description"] if len(section1["description"]) <= len(
            section2["description"]) else section2["description"]
        pos: tuple[GenericCoqPosition, GenericCoqPosition] = section1.position, section2.position
        new_files = {}
        old_files = (pos[0].file_positions, pos[1].file_positions)
        for filename in old_files[0].keys() | old_files[1].keys():
            match (filename in old_files[0].keys(), filename in old_files[1].keys()):
                case (True, True):
                    new_files[filename] = (min(old_files[0][filename], old_files[1][filename]),
                                           max(old_files[0][filename], old_files[1][filename]))
                case (False, True):
                    new_files[filename] = old_files[1][filename]
                case (True, False):
                    new_files[filename] = old_files[0][filename]
                case _:
                    raise Exception("This should never happen")
        new_cases = {}
        for case in section1["cases"].entries.keys() | section2["cases"].entries.keys():
            if section1["cases"][case] is not None and section2["cases"][case] is not None:
                section1["cases"][case]: Dictionnary[String]
                for key in section1["cases"][case].entries.keys() | section2["cases"][case].entries.keys():
                    #TODO Better handling of common keys
                    if section1["cases"][case][key] is not None:
                        new_cases[case] = section1["cases"][case][key]
                    else:
                        new_cases[case] = section2["cases"][case].entries[key]
                new_cases[case] = section1["cases"][case].entries.union(section2["cases"][case])
            elif section1["cases"][case] is not None:
                new_cases[case] = section1["cases"][case]
            else:
                new_cases[case] = section2["cases"][case]
        return Dictionnary(GenericCoqPosition(new_files), {"title": title, "description": description_first + "\n" +
                                                                                          description_second,
                                                           "cases": Dictionnary(None, new_cases)})

    """
    Gets the indices of the comments that contain the titles of the sections (comments that match the title_regex)
    """

    def __get_comment_titles(self) -> Dict[str, Dictionnary]:
        title_indices = {}
        current_block = ""
        last_block_end = 0
        section_to_be_thrown_away = False
        for comment_index, comment in enumerate(self.comments):
            if res2 := self.any_title_regex.match(comment[0]):
                if current_block != "" and not section_to_be_thrown_away:
                    if title_indices.get(current_block) is not None:
                        # This means the section was split
                        title_indices[current_block] = self.__merge_comments(
                            self.__parse_subsection((last_block_end, comment_index)), title_indices.get(current_block))
                    else:
                        title_indices[current_block] = self.__parse_subsection((last_block_end, comment_index))
                    last_block_end = comment_index
                elif current_block != "" and section_to_be_thrown_away:
                    last_block_end = comment_index
                current_block = res2.group(1)
                section_to_be_thrown_away = self.title_regex.search(str(comment)) is None
        if not section_to_be_thrown_away:
            title_indices[current_block] = self.__parse_subsection((last_block_end, len(self.comments)))
        return title_indices

    def __parse_title(self, title: str) -> str:

        lines = title.splitlines(keepends=False)
        title = lines[1].lstrip()
        for line in lines[3:-1]:
            title += "\n" + line.lstrip()
        return title + "\n"

    def __parse_comment(self, comment: str) -> str:
        return (comment.replace("\n", "").replace("(*>>", "").replace("<<*)", "")
                .replace("(** >>", "").lstrip().rstrip())

    # Pour les commentaires de 22.2.2.1, on peut soit:
    # - mettre un "-" ou "*" au début pour montrer qu'il s'agit d'un point
    # - mettre un commentaire avant qui indique qu'il s'agit d'un enchaînement de points
    def __parse_subsection(self, comment_indices) -> Dictionnary:
        comment_lines = self.comments[comment_indices[0]:comment_indices[1]]

        title = ""
        description = ""
        parser_state = ParserState.READING_TITLE
        in_case_title = False
        cases: dict[str, Dictionnary] = {}
        current_case = ""
        current_case_titles = []
        filenames = {}
        case_line_indices = [-1, -1]
        for parsed_comment, coq_line in comment_lines:
            # We are at the end of a comment
            if coq_line.is_end_comment:
                match parser_state:
                    case ParserState.READING_TITLE:
                        parser_state = ParserState.READING_DESCRIPTION
                    case ParserState.READING_DESCRIPTION:
                        pass
                    case ParserState.READING_CASES:
                        pass
                continue
            # Get file name
            filename = coq_line.file_name
            # If not already in, add it and add its current line
            if filenames.get(filename) is None:
                filenames[filename] = (coq_line.line_number, coq_line.line_number)
            # Otherwise update last line
            else:
                before_indices = filenames[filename]
                added_index = coq_line.line_number
                new_indices = (min(before_indices[0], added_index), max(before_indices[1], added_index))
                filenames[filename] = new_indices

            if self.case_regex.match(parsed_comment):
                parser_state = ParserState.READING_CASES
                if current_case != "":
                    case_pos = GenericCoqPosition({coq_line.file_name: tuple(case_line_indices)})
                    for case_title in current_case_titles:
                        add_case(cases, (case_title[1], String(case_pos,current_case)), case_title[0])
                    current_case_titles = []
                case_line_indices[0] = coq_line.line_number
                case_line_indices[1] = coq_line.line_number
                match = self.case_regex.match(parsed_comment)
                current_case_titles.append([match.group(1), match.group(2)])
                current_case = ""
                in_case_title = True

            else:
                match parser_state:
                    case ParserState.READING_TITLE:
                        if self.algo_regex.match(parsed_comment):
                            # If there is a start of an algorithm, but we are still building title, it means that there
                            # is only one case in the subsection, and therefore we set its title to ""
                            case_line_indices[0] = coq_line.line_number
                            case_line_indices[1] = coq_line.line_number
                            parser_state = ParserState.READING_CASES
                            current_case = parsed_comment + "\n"
                            if not current_case_titles:
                                current_case_titles.append(["", ""])
                        else:
                            title += parsed_comment
                            parser_state = ParserState.READING_DESCRIPTION
                    case ParserState.READING_DESCRIPTION:
                        if self.algo_regex.match(parsed_comment):
                            # If there is a start of an algorithm, but we are still building description, it means that
                            # there is only one case in the subsection, and therefore we set its title to ""
                            case_line_indices[0] = coq_line.line_number
                            case_line_indices[1] = coq_line.line_number
                            parser_state = ParserState.READING_CASES
                            current_case = parsed_comment + "\n"
                            if not current_case_titles:
                                current_case_titles.append(["", ""])
                        else:
                            description += parsed_comment + " "
                    case ParserState.READING_CASES:
                        case_line_indices[1] = coq_line.line_number
                        if self.algo_regex.match(parsed_comment) or not in_case_title:
                            if not current_case_titles:
                                current_case_titles.append(["", ""])
                            in_case_title = False
                            current_case += parsed_comment + "\n"
                        elif in_case_title:
                            current_case_titles[-1][1] += "\n" + parsed_comment
        if current_case != "":
            case_pos = GenericCoqPosition({comment_lines[-1][1].file_name: tuple(case_line_indices)})
            for case_title in current_case_titles:
                add_case(cases, (case_title[1], String(case_pos, current_case)), case_title[0])
        cases_dict = Dictionnary(None,cases)
        if title.startswith("22.2.1 "):
            return WildCard(GenericCoqPosition(filenames))
        return Dictionnary(GenericCoqPosition(filenames), {"title":String(None,title),
                                                           "description": String(None,description),
                                                           "cases": cases_dict})

    def get_parsed_page(self) -> GenericParsedPage:
        if self.sections_by_number is None:
            self.coq_code, self.all_filenames = self.__get_coq_code()
            self.comments = self.__get_comment_lines()
            self.sections_by_number = self.__get_comment_titles()
        return GenericParsedPage(self.name, Dictionnary(None,self.sections_by_number))
