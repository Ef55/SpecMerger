from typing import List, Callable
from packaging.version import Version
import difflib

from Report import Report
from utils import Path, Parser, Case, SubSection
from Formatter import Formatter


def _same_titles(case_titles: list[tuple[Case, str]]) -> set[set[Case]]:
    seen = set()
    same = {}
    for case, title in case_titles:
        if title in seen:
            if same.get(title) is None:
                same[title] = {case}
            else:
                same[title].add(case)
        seen.add(title)
    # This is used to get the first case that has the same title
    seen = set()
    for case, title in case_titles[::-1]:
        if title in seen:
            same[title].add(case)
        seen.add(title)
    return set(same.values())


class Comparer:
    def __init__(self, first_parser: Parser, second_parser: Parser, sections_to_exclude: List[str]):
        self.sections_to_exclude = sections_to_exclude
        self.formatter = Formatter()
        self.first_parser = first_parser
        self.second_parser = second_parser
        self.report = Report(first_parser.name, second_parser.name)

    def _compare_first_doc_auto(self, id: int):
        for section in self.second_parser.sections_by_number.keys():
            if section in self.sections_to_exclude:
                continue
            coq = self.second_parser.get_section_for_comparison(section)
            try:
                spec = self.first_parser.get_section_for_comparison(section)
            except:
                self.formatter.add_not_found(coq, id)
                continue
            if coq.title != spec.title and id == 0:
                self.formatter.add_not_same_title(coq, spec)
                continue
            if coq.description != spec.description and id == 0:
                self.formatter.add_not_same_description(coq, spec)
                continue
            all_cases_correct = True
            # Verify that coq cases are in spec
            for coq_case in coq.cases:
                lefts = [case for case in spec.cases if case.left_title == coq_case.left_title]
                if len(lefts) == 0:
                    self.formatter.add_case_not_found_at_all(coq, spec, coq_case, id)
                    all_cases_correct = False
                    continue
                preciser = [case for case in lefts if
                            case.right_title.replace(" ", "") == coq_case.right_title.replace(" ", "")]
                if len(preciser) == 0:
                    self.formatter.add_case_right_not_found(coq, spec, coq_case, lefts, id)
                    all_cases_correct = False
                    continue
                if len(preciser) > 1:
                    self.formatter.add_case_found_multiple_times(coq, spec, coq_case, preciser, id)
                    all_cases_correct = False
                    continue
                chars_to_remove = [' ', '\xa0']
                code1 = "".join([x for x in preciser[0].code if x not in chars_to_remove])
                code2 = "".join([x for x in coq_case.code if x not in chars_to_remove])

                if code1 != code2 and id == 0:
                    self.formatter.add_case_code_not_same(coq, spec, coq_case, preciser[0])
                    all_cases_correct = False
                    continue
            if all_cases_correct and id == 0:
                self.formatter.add_same(coq, spec)

    def _compare_second_doc_auto(self, id: int):
        for section in self.first_parser.sections_by_number.keys():
            if section in self.sections_to_exclude:
                continue
            ecma = self.first_parser.get_section_for_comparison(section)
            try:
                coq = self.second_parser.get_section_for_comparison(section)
            except:
                self.formatter.add_not_found(ecma, id)
                continue
            if coq.title != ecma.title and id == 0:
                self.formatter.add_not_same_title(ecma, coq)
                continue
            if coq.description != ecma.description and id == 0:
                self.formatter.add_not_same_description(ecma, coq)
                continue
            all_cases_correct = True
            # Verify that coq cases are in spec
            for ecma_case in ecma.cases:
                lefts = [case for case in coq.cases if case.left_title == ecma_case.left_title]
                if len(lefts) == 0:
                    self.formatter.add_case_not_found_at_all(ecma, coq, ecma_case, id)
                    all_cases_correct = False
                    continue
                preciser = [case for case in lefts if
                            case.right_title.replace(" ", "") == ecma_case.right_title.replace(" ", "")]
                if len(preciser) == 0:
                    self.formatter.add_case_right_not_found(ecma, coq, ecma_case, lefts, id)
                    all_cases_correct = False
                    continue
                if len(preciser) > 1:
                    self.formatter.add_case_found_multiple_times(ecma, coq, ecma_case, preciser, id)
                    all_cases_correct = False
                    continue
                if preciser[0].code.replace(" ", "") != ecma_case.code.replace(" ", "") and id == 0:
                    self.formatter.add_case_code_not_same(ecma, coq, ecma_case, preciser[0])
                    all_cases_correct = False
                    continue
            if all_cases_correct and id == 0:
                self.formatter.add_same(ecma, coq)

    def compare_cases(self, to_check_again: list[str], section_1: SubSection, section_2: SubSection,
                      found_curr_section: int):
        assert found_curr_section in {0, 1}
        sections = [section_1, section_2]
        section = sections[found_curr_section]
        for case_key in to_check_again:
            possible_cases = section.cases[case_key]
            if len(possible_cases) > 1:
                continue
            possibilities = []
            current_case = list(possible_cases)[0]
            left_title = current_case.left_title
            for case in sections[1 - found_curr_section].get_all_cases():
                if case.left_title == left_title:
                    possibilities.append(case)
            if len(possibilities) == 0:
                self.report.add_case_not_found_at_all(section_1, section_2, current_case, found_curr_section)
            else:
                self.report.add_case_right_not_found(section_1, section_2, current_case,
                                                     possibilities, found_curr_section)

    def compare_auto(self):
        chars_to_replace = [' ', '\xa0']
        section_keys_first = self.first_parser.get_all_section_numbers()
        section_keys_second = self.second_parser.get_all_section_numbers()
        section_keys = section_keys_first | section_keys_second
        for section_number in section_keys:
            if section_number in self.sections_to_exclude:
                print(f"[LOG] Section {section_number} is excluded")
                continue
            if section_number not in section_keys_first:
                self.report.add_not_found(self.second_parser.get_section_for_comparison(section_number), 0)
                continue
            if section_number not in section_keys_second:
                self.report.add_not_found(self.first_parser.get_section_for_comparison(section_number), 1)
                continue
            # Section is contained in both
            section_1 = self.first_parser.get_section_for_comparison(section_number)
            section_2 = self.second_parser.get_section_for_comparison(section_number)
            if section_1.title != section_2.title:
                self.report.add_not_same_title(section_1, section_2)
            description1 = "".join([x for x in section_1.description if x not in chars_to_replace])
            description2 = "".join([x for x in section_2.description if x not in chars_to_replace])
            if description1 != description2:
                self.report.add_not_same_description(section_1, section_2)
            all_cases_correct = True
            cases_keys_first = section_1.cases.keys()
            cases_keys_second = section_2.cases.keys()
            case_keys = cases_keys_first | cases_keys_second
            to_check_again_from_first = []
            to_check_again_from_second = []
            for case_key in case_keys:
                cases_first = section_1.cases.get(case_key)
                if cases_first is None:
                    to_check_again_from_first.append(case_key)
                    all_cases_correct = False
                elif len(cases_first) > 1:
                    self.report.add_case_found_multiple_times(section_1, cases_first, 0)
                    all_cases_correct = False
                cases_second = section_2.cases.get(case_key)
                if cases_second is None:
                    to_check_again_from_second.append(case_key)
                    all_cases_correct = False
                elif len(cases_second) > 1:
                    self.report.add_case_found_multiple_times(section_2, cases_second, 1)
                    all_cases_correct = False
                if not all_cases_correct:
                    continue
                case_first = cases_first.pop()
                case_second = cases_second.pop()
                code1 = "".join([x for x in case_first.code if x not in chars_to_replace])
                code2 = "".join([x for x in case_second.code if x not in chars_to_replace])
                if code1 != code2:
                    self.report.add_case_code_not_same(section_1, section_2, case_first, case_second)
                    all_cases_correct = False
            if all_cases_correct:
                self.report.add_same(section_1, section_2)
                continue
            # 2 was found but not 1
            self.compare_cases(to_check_again_from_first, section_1, section_2, 1, )
            # 1 was found but not 2
            self.compare_cases(to_check_again_from_second, section_1, section_2, 0, )
        return self.report

