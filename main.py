from typing import List
from packaging.version import Version
import difflib
import curses

from ECMAParser import ECMAParser
from COQParser import COQParser
from Formatter import Formatter
from utils import Path


class Comparer:
    def __init__(self, url: str, files: List[Path], to_exclude: List[Path]):
        self.url = url
        self.files = files
        self.to_exclude = to_exclude
        self.formatter = Formatter()
        self.coq_parser = COQParser(files, to_exclude)
        print("[LOG] COQ PARSER INITIALIZED")
        self.ecma_parser = ECMAParser(url)
        print("[LOG] ECMASCRIPT PARSER INITIALIZED")

    def compare(self):
        print("SECTIONS AVAILABLE IN ECMASCRIPT: ")
        print(str(sorted(self.ecma_parser.sections_by_number.keys(), key=Version)))

        print("SECTIONS AVAILABLE IN COQ: ")
        print(str(sorted(self.coq_parser.sections_by_number.keys(), key=Version)))

        while True:
            coq = None
            spec = None
            section = input("What section do you want to compare? \n")
            turtle = "🐢"
            try:
                spec = self.ecma_parser.get_section(section)
                print("====================  HTML CODE  ====================\n")
                print(spec)
            except:
                print("WARNING: Section not found in html\n")
            try:
                coq = self.coq_parser.get_section(section)
                print("====================   COQ CODE  ====================\n")
                print(coq)
            except:
                print("WARNING: Section not found in coq\n")

            if coq and spec:
                coq_sub = self.coq_parser.get_section_for_comparison(section)
                spec_sub = self.ecma_parser.get_section_for_comparison(section)
                if coq_sub.title != spec_sub.title:
                    print("WARNING: Titles are different")
                    print("COQ: \n", coq_sub.title)
                    print("SPEC: \n", spec_sub.title)
                    continue
                if coq_sub.description != spec_sub.description:
                    print("WARNING: Descriptions are different")
                    print("COQ: \n", coq_sub.description)
                    print("SPEC: \n", spec_sub.description)
                    continue

                # Verify that coq cases are in spec
                for coq_case in coq_sub.cases:
                    lefts = [case for case in spec_sub.cases if case.left_title == coq_case.left_title]
                    if len(lefts) == 0:
                        print("WARNING: COQ case not found in spec")
                        continue
                    preciser = [case for case in lefts if case.right_title == coq_case.right_title]
                    if len(preciser) == 0:
                        print("WARNING: COQ case not found in spec")
                        print("Most similar cases are :")
                        print("\n".join(
                            [case for case in difflib.get_close_matches(str(coq_case), [str(x) for x in lefts])]))
                        continue
                    if len(preciser) > 1:
                        print("WARNING: More than one case found")
                        print("\n".join([str(x) for x in preciser]))
                        continue
                    if preciser[0].code != coq_case.code:
                        print("WARNING: Code is different")
                        print("COQ: ", coq_case.code)
                        print("SPEC: ", preciser[0].code)
                        continue
                    print("COQ AND SPEC ARE THE SAME 🎉")

    def _compare_coq_auto(self, id: int):
        for section in self.coq_parser.sections_by_number.keys():
            coq = self.coq_parser.get_section_for_comparison(section)
            try:
                spec = self.ecma_parser.get_section_for_comparison(section)
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
                if preciser[0].code != coq_case.code and id == 0:
                    self.formatter.add_case_code_not_same(coq, spec, coq_case, preciser[0])
                    all_cases_correct = False
                    continue
            if all_cases_correct and id == 0:
                self.formatter.add_same(coq, spec)

    def _compare_ecma_auto(self, id: int):
        for section in self.ecma_parser.sections_by_number.keys():
            ecma = self.ecma_parser.get_section_for_comparison(section)
            try:
                coq = self.coq_parser.get_section_for_comparison(section)
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
                if preciser[0].code != ecma_case.code and id == 0:
                    self.formatter.add_case_code_not_same(ecma, coq, ecma_case, preciser[0])
                    all_cases_correct = False
                    continue
            if all_cases_correct and id == 0:
                self.formatter.add_same(ecma, coq)

    def compare_auto(self):
        self._compare_coq_auto(0)
        self._compare_ecma_auto(1)
        self.formatter.format("IN COQ", "IN ECMAScript")


def main():
    url = "https://262.ecma-international.org/14.0/"
    paths = [Path("../warblre/mechanization/spec/", True)]
    to_exclude = [Path("../warblre/mechanization/spec/Node.v", False)]
    parser = Comparer(url, paths, to_exclude)
    parser.compare_auto()


if __name__ == "__main__":
    main()
