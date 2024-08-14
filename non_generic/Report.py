from utils import SubSection, Case


class Report:
    def __init__(self, first_doc_name: str, second_doc_name: str):
        self.not_found: dict[int, list[SubSection]] = {0: [], 1: []}
        self.not_same_title: list[tuple[SubSection, SubSection]] = []
        self.not_same_description: list[tuple[SubSection, SubSection]] = []
        self.case_not_found_at_all: dict[str, tuple[SubSection, SubSection, dict[int, list[Case]]]] = {}
        self.case_right_not_found: list[tuple[SubSection, SubSection, Case, list[Case], int]] = []
        self.case_found_multiple_times: list[tuple[SubSection, set[Case], int]] = []
        self.case_code_not_same: list[tuple[SubSection, SubSection, Case, Case]] = []
        self.correct: list[tuple[SubSection, SubSection]] = []
        self.first_doc_name = first_doc_name
        self.second_doc_name = second_doc_name

    @staticmethod
    def check_doc(doc):
        assert doc in {0, 1}

    def add_not_found(self, section: SubSection, doc: int):
        self.check_doc(doc)
        self.not_found[doc].append(section)

    def add_not_same_title(self, original_section: SubSection, other_section: SubSection):
        self.not_same_title.append((original_section, other_section))

    def add_not_same_description(self, original_section: SubSection, other_section: SubSection):
        self.not_same_description.append((original_section, other_section))

    def add_case_not_found_at_all(self, original_section: SubSection, other_section: SubSection, case: Case, doc: int):
        self.check_doc(doc)
        assert original_section.title == other_section.title, "Sections must have the same title"
        section = self.case_not_found_at_all.get(original_section.title)
        if section is not None:
            assert (section[0] == original_section and section[1] == other_section or
                    section[1] == original_section and section[0] == other_section), "subsections are not the same ???"
            section[2].get(doc).append(case)
        else:
            cases = {0: [], 1: []}
            cases[doc].append(case)
            if doc == 0:
                to_add = (original_section, other_section, cases)
            else:
                to_add = (other_section, original_section, cases)
            self.case_not_found_at_all[original_section.title] = to_add

    def add_case_right_not_found(self, original_section: SubSection, other_section: SubSection, case: Case,
                                 lefts: list[Case], doc: int):
        self.check_doc(doc)
        self.case_right_not_found.append((original_section, other_section, case, lefts, doc))

    def add_case_found_multiple_times(self, original_section: SubSection, cases: set[Case], doc: int):
        self.check_doc(doc)
        self.case_found_multiple_times.append((original_section, cases, doc))

    def add_case_code_not_same(self, original_section: SubSection, other_section: SubSection, original_case: Case,
                               other_case: Case):
        self.case_code_not_same.append((original_section, other_section, original_case, other_case))

    def add_same(self, original_section: SubSection, other_section: SubSection):
        self.correct.append((original_section, other_section))

    def finalize(self, sort_section_titles):
        from_tup_without_doc_order = lambda x: sort_section_titles(x[0])
        from_tup_with_doc_order = lambda x: (x[-1], sort_section_titles(x[0]))
        self.not_found[0].sort(key=sort_section_titles)
        self.not_found[1].sort(key=sort_section_titles)
        self.correct.sort(key=from_tup_without_doc_order)
        self.not_same_title.sort(key=from_tup_without_doc_order)
        self.not_same_description.sort(key=from_tup_without_doc_order)
        self.case_right_not_found.sort(key=from_tup_with_doc_order)
        self.case_found_multiple_times.sort(key=from_tup_with_doc_order)
        self.case_code_not_same.sort(key=from_tup_without_doc_order)
