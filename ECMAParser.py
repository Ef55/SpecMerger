from dataclasses import dataclass
from typing import Dict, List

import bs4
import requests
from bs4 import BeautifulSoup

from utils import Parser, SubSection, Case, ParserState, Position


@dataclass(frozen=True)
class URLPosition(Position):
    url: str

    def html_str(self):
        return f"<a href='{self.url}'>{self.url}</a>"

class ECMAParser(Parser):

    def __init__(self, url, sections=None):
        if sections is None:
            sections = ["sec-regexp-regular-expression-objects"]
        self.url = url
        self.page = self._get_page()
        self.sections_by_number: Dict[str, SubSection] = {}
        self.avoid = {None, "emu-note", "\n"}
        self._preprocess(sections)

    def _get_page(self):
        html_spec = requests.get(self.url).content
        soup = BeautifulSoup(html_spec, 'html.parser')
        return soup

    def _parse_section(self, section_html: BeautifulSoup, ):
        position = URLPosition(self.url + "#" + section_html.get("id"))
        title = section_html.find("h1").find("span", {"class": "secnum"}).text
        first_subsection = section_html.find("emu-clause")
        if first_subsection is not None:
            paragraph = [x for x in first_subsection.previous_siblings if x.name not in self.avoid][::-1]
            self.sections_by_number[title] = self.parse_subsection(paragraph,position)
            for new_section in section_html.find_all("emu-clause", recursive=False):
                self._parse_section(new_section)
        else:
            paragraph = [x for x in section_html.children if x.name not in self.avoid]
            self.sections_by_number[title] = self.parse_subsection(paragraph,position)

    def _preprocess(self, sections):
        for section in sections:
            html_section = self.page.find("emu-clause", {"id": section})
            self._parse_section(html_section)

    @staticmethod
    def strip_sides(string: str) -> str:
        return string.replace("\n", "").replace("\t", "").lstrip().rstrip()

    def _parse_list(self, ol_or_ul: BeautifulSoup, list_type: str = "ol", prefix: str = "") -> str:
        result = ""
        for li in ol_or_ul.children:
            if li == '\n':
                continue
            if (sub_list := li.find(list_type)) is not None:
                result += prefix + "".join(
                    [self.strip_sides(self._parse_p(x)) for x in sub_list.previous_siblings][::-1]) + "\n"
                result += self._parse_list(sub_list, list_type)
            else:
                result += prefix + self.strip_sides(self._parse_p(li)) + "\n"

        return result

    def _parse_emu_alg(self, emu_alg_section: BeautifulSoup) -> str:
        # An emu-alg always contain a single <ol> containing a lot of <li> elements and can also contain other <ol>
        # elements
        main_ol = list(emu_alg_section.children)[0]
        return self._parse_list(main_ol)

    def _parse_emu_grammar(self, emu_grammar_section: BeautifulSoup) -> list[str]:
        # an emu-grammar always contains one or multiple emu-production which themselves contain :
        # - an emu-nt
        # - an emu-geq
        # one or multiple emu-rhs which all contain one or more element
        emu_prods = emu_grammar_section.find_all("emu-production")
        result = ["", ""]
        for prod in emu_prods:
            result[0] = prod.find("emu-nt").text
            separator = " " if prod.has_attr("collapsed") else "\n"
            right_hand_sides = prod.find_all("emu-rhs", recursive=False)
            for rhs in right_hand_sides:
                # hack to avoid beautiful soup to add \n for no reason ?
                if type(rhs) is not bs4.NavigableString:
                    result[1] += separator
                    for nt in rhs.children:
                        to_add = nt.text.replace("\n", "") + " "
                        result[1] += "" if to_add == " " else to_add
            # remove last space
            if result[1] != "":
                result[1] = result[1][:-1]
        return result

    def _parse_p(self, p: BeautifulSoup):
        res = ""
        if type(p) is bs4.NavigableString:
            return p.text
        for child in p.children:
            match child.name:
                case "emu-grammar":
                    res += " ::".join(self._parse_emu_grammar(child))
                case _:
                    res += child.text
        return res

    def parse_subsection(self, subsection: List[BeautifulSoup], position: URLPosition) -> SubSection:
        title = ""
        description = ""
        cases: set[Case] = set()
        current_case = ""
        current_case_title = ["", ""]
        parser_state = ParserState.READING_TITLE
        for children in subsection:
            match children.name:
                case "h1":
                    title += self.strip_sides(children.text)
                    parser_state = ParserState.READING_DESCRIPTION
                case "p":
                    if parser_state in {ParserState.READING_TITLE, ParserState.READING_DESCRIPTION}:
                        parser_state = ParserState.READING_DESCRIPTION
                        description += self.strip_sides(self._parse_p(children)) + " "
                    else:
                        pass
                case "ul":
                    match parser_state:
                        case ParserState.READING_TITLE:
                            title += self.strip_sides(children.text) + " "
                        case ParserState.READING_DESCRIPTION:
                            description += self._parse_list(children, "ul", prefix=" ")
                        case ParserState.READING_CASES:
                            current_case += self._parse_list(children, "ul", prefix="* ")
                case "emu-alg":
                    parser_state = ParserState.READING_CASES
                    current_case += self._parse_emu_alg(children)
                    cases.add(Case(current_case_title[0], current_case_title[1], current_case))
                    current_case = ""
                    current_case_title = ["", ""]
                case "emu-grammar":
                    parser_state = ParserState.READING_CASES
                    if current_case != "":
                        cases.add(Case(current_case_title[0], current_case_title[1], current_case))
                        current_case = ""
                    current_case_title = self._parse_emu_grammar(children)
                case "span" | "emu-table" | "emu-import" | "h2":
                    pass
                case _:
                    print(f"ERROR: Unhandled tag in html section : {children.name}, {children.text}")
                    raise ValueError
        if current_case_title != ["", ""]:
            cases.add(Case(current_case_title[0], current_case_title[1], current_case))
        return SubSection(title, description, cases,position)

    def get_section_for_comparison(self, section) -> SubSection:
        assert section in self.sections_by_number.keys()
        return self.sections_by_number[section]


