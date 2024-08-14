from typing import List
from packaging.version import Version

from non_generic.Report import Report
from utils import Case, SubSection, ParsedPage


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
    def __init__(self, first_parsed_page: ParsedPage, second_parsed_page: ParsedPage, sections_to_exclude: List[str],
                 sort_section_titles=None):
        if sort_section_titles is None:
            self.sort_section_titles = lambda subsection: Version(subsection.title.split(" ")[0])
        else:
            self.sort_section_titles = sort_section_titles
        self.sections_to_exclude = sections_to_exclude
        self.first_page = first_parsed_page
        self.second_page = second_parsed_page
        self.report = Report(first_parsed_page.name, second_parsed_page.name)

    def __compare_cases(self, to_check_again: list[str], section_1: SubSection, section_2: SubSection,
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

    def produce_report(self):
        chars_to_replace = [' ', '\xa0']
        section_keys_first = self.first_page.get_all_section_numbers()
        section_keys_second = self.second_page.get_all_section_numbers()
        section_keys = section_keys_first | section_keys_second
        for section_number in section_keys:
            if section_number in self.sections_to_exclude:
                print(f"[LOG] Section {section_number} is excluded")
                continue
            if section_number not in section_keys_first:
                self.report.add_not_found(self.second_page[section_number], 0)
                continue
            if section_number not in section_keys_second:
                self.report.add_not_found(self.first_page[section_number], 1)
                continue
            # Section is contained in both
            section_1 = self.first_page[section_number]
            section_2 = self.second_page[section_number]
            if section_1.title != section_2.title:
                self.report.add_not_same_title(section_1, section_2)
                continue
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
                case_first = list(cases_first)[0]
                case_second = list(cases_second)[0]
                code1 = "".join([x for x in case_first.code if x not in chars_to_replace])
                code2 = "".join([x for x in case_second.code if x not in chars_to_replace])
                if code1 != code2:
                    self.report.add_case_code_not_same(section_1, section_2, case_first, case_second)
                    all_cases_correct = False
            if all_cases_correct:
                self.report.add_same(section_1, section_2)
                continue
            # 2 was found but not 1
            self.__compare_cases(to_check_again_from_first, section_1, section_2, 1)
            # 1 was found but not 2
            self.__compare_cases(to_check_again_from_second, section_1, section_2, 0)
        self.report.finalize(self.sort_section_titles)
        return self.report
