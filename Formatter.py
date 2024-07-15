import os
import webbrowser

from utils import SubSection, Case


def check_doc(doc: int):
    assert doc in {0, 1}


class Formatter:
    def __init__(self):
        self.not_found : dict[int,list[SubSection]] = {0: [], 1: []}
        self.not_same_title = []
        self.not_same_description = []
        self.case_not_found_at_all = []
        self.case_right_not_found = []
        self.case_found_multiple_times = []
        self.case_code_not_same = []
        self.correct = []

    def add_not_found(self, section: SubSection, doc: int):
        check_doc(doc)
        self.not_found[doc].append(section)

    def add_not_same_title(self, original_section: SubSection, other_section: SubSection):
        self.not_same_title.append((original_section, other_section))

    def add_not_same_description(self, original_section: SubSection, other_section: SubSection):
        self.not_same_description.append((original_section, other_section))

    def add_case_not_found_at_all(self, original_section: SubSection, other_section: SubSection, case: Case, doc: int):
        check_doc(doc)
        self.case_not_found_at_all.append((original_section, other_section, case, doc))

    def add_case_right_not_found(self, original_section: SubSection, other_section: SubSection, case: Case,
                                 lefts: list[Case], doc: int):
        check_doc(doc)
        self.case_right_not_found.append((original_section, other_section, case, lefts, doc))

    def add_case_found_multiple_times(self, original_section: SubSection, other_section: SubSection, case: Case,
                                      preciser: list[Case], doc: int):
        check_doc(doc)
        self.case_found_multiple_times.append((original_section, other_section, case, preciser, doc))

    def add_case_code_not_same(self, original_section: SubSection, other_section: SubSection, original_case: Case,
                               other_case: Case):
        self.case_code_not_same.append((original_section, other_section, original_case, other_case))

    def add_same(self, original_section: SubSection, other_section: SubSection):
        self.correct.append((original_section, other_section))

    def format(self, original_doc_name: str, other_doc_name: str):
        names = [original_doc_name, other_doc_name]
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Comparison Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .section {{ margin-bottom: 20px; }}
                .case {{ margin-left: 20px; }}
                .error {{ color: red; }}
                .success {{ color: green; }}
            </style>
        </head>
        <body>
            <h1>Comparison Report</h1>
            
            <h2>Correct Matches</h2>
            {correct}
            
            <h2>Sections Not Found</h2>
            {not_found}

            <h2>Sections with Different Titles</h2>
            {not_same_title}

            <h2>Sections with Different Descriptions</h2>
            {not_same_description}

            <h2>Cases Not Found At All</h2>
            {case_not_found_at_all}

            <h2>Cases with Right Side Not Found</h2>
            {case_right_not_found}

            <h2>Cases Found Multiple Times</h2>
            {case_found_multiple_times}

            <h2>Cases with Different Code</h2>
            {case_code_not_same}

            
        </body>
        </html>
        """

        def format_section(section: SubSection):
            return f"<div class='section'><h3>{section.title}, {section.position.html_str()}</h3><p>{section.description}</p></div>"

        def format_case(case: Case):
            return f"<div class='case'><p>{case.left_title} :: {case.right_title}</p><pre>{case.code}</pre></div>"

        def format_if_empty(section: str):
            return section if section != "" else "Empty"

        not_found_html = format_if_empty("<br>".join(
            f"<div class='error'><p><h3>{names[i]}:</h3> {'<br><br>'.join(f'{section.title} : {section.position.html_str()}' for section in self.not_found[i])}"
            f"</p></div>"
            for i in range(2)))

        not_same_title_html = format_if_empty("<br>".join(
            f"<div class='error'><p><h3>{original_doc_name}:</h3> {format_section(original)}</p><p><h3>{other_doc_name}:</h3>{format_section(other)}</p></div>"
            for original, other in self.not_same_title
        ))

        not_same_description_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>{original_doc_name}:</h3> {format_section(original)}</p><p><h3>{other_doc_name}:</h3> {format_section(other)}</p></div>"
            for original, other in self.not_same_description
        ))

        case_not_found_at_all_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>{names[doc]}:</h3> {format_section(original)}</p><p><h3>Case not found:</h3> {format_case(case)}</p></div>"
            for original, other, case, doc in self.case_not_found_at_all
        ))

        case_right_not_found_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>{names[doc]}:</h3> {format_section(original)}</p><p><h3>Case:</h3> {format_case(case)}</p><p>Left cases found: {chr(10).join(format_case(left) for left in lefts)}</p></div>"
            for original, other, case, lefts, doc in self.case_right_not_found
        ))

        case_found_multiple_times_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>{names[doc]}:</h3> {format_section(original)}</p><p><h3>Case found multiple times:</h3> {format_case(case)}</p><p>Preciser cases: {', '.join(str(p) for p in preciser)}</p></div>"
            for original, other, case, preciser, doc in self.case_found_multiple_times
        ))

        case_code_not_same_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>Section:</h3> {format_section(original)}</p><p><h3>{original_doc_name}:</h3> {format_case(original_case)}</p><p>{other_doc_name}: {format_case(other_case)}</p></div>"
            for original, other, original_case, other_case in self.case_code_not_same
        ))

        correct_html = format_if_empty("".join(
            f"<div class='success'><p><h3>{original.title}:</h3></p></div>"
            for original, other in self.correct
        ))

        html_content = html_template.format(
            not_found=not_found_html,
            not_same_title=not_same_title_html,
            not_same_description=not_same_description_html,
            case_not_found_at_all=case_not_found_at_all_html,
            case_right_not_found=case_right_not_found_html,
            case_found_multiple_times=case_found_multiple_times_html,
            case_code_not_same=case_code_not_same_html,
            correct=correct_html
        )

        file_path = os.path.abspath('comparison_report.html')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Open the HTML file in the default web browser
        webbrowser.open('file://' + file_path, new=2)
        return html_content
