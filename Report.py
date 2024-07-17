from utils import SubSection, Case


class Report:
    def __init__(self, first_doc_name: str, second_doc_name: str):
        self.not_found: dict[int, list[SubSection]] = {0: [], 1: []}
        self.not_same_title = []
        self.not_same_description = []
        self.case_not_found_at_all = []
        self.case_right_not_found = []
        self.case_found_multiple_times = []
        self.case_code_not_same = []
        self.correct = []
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
        self.case_not_found_at_all.append((original_section, other_section, case, doc))

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
