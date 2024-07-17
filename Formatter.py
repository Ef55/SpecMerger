import html
import os
import webbrowser
import difflib

from Report import Report
from utils import SubSection, Case


def check_doc(doc: int):
    assert doc in {0, 1}


class Formatter:
    @staticmethod
    def format(report: Report, report_path: str):
        e = html.escape
        print("[LOG] Found :")
        print(f"[LOG]    {len(report.not_found[0]) + len(report.not_found[1])} SECTIONS NOT FOUND")
        print(f"[LOG]    {len(report.not_same_title)} SECTIONS WITH DIFFERENT TITLES")
        print(f"[LOG]    {len(report.not_same_description)} SECTIONS WITH DIFFERENT DESCRIPTIONS")
        print(f"[LOG]    {len(report.case_not_found_at_all)} CASES NOT FOUND AT ALL")
        print(f"[LOG]    {len(report.case_right_not_found)} CASES WITH RIGHT SIDE NOT FOUND")
        print(f"[LOG]    {len(report.case_found_multiple_times)} CASES FOUND MULTIPLE TIMES")
        print(f"[LOG]    {len(report.case_code_not_same)} CASES WITH DIFFERENT CODE")
        print(f"[LOG]    {len(report.correct)} CORRECT MATCHES")
        names = [report.first_doc_name, report.second_doc_name]
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
            return f"<div class='section'><h3>{e(section.title)}, {section.position.html_str()}</h3><p>{e(section.description)}</p></div>"

        def format_case(case: Case):
            return f"<div class='case'><p>{e(case.left_title)} :: {e(case.right_title)}</p><pre>{e(case.code)}</pre></div>"

        def format_if_empty(section: str):
            return section if section != "" else "Empty"

        not_found_html = format_if_empty("<br>".join(
            f"<div class='error'><p><h3>{e(names[i])}:</h3> {'<br><br>'.join(f'{e(section.title)} : {section.position.html_str()}' for section in report.not_found[i])}"
            f"</p></div>"
            for i in range(2)))

        not_same_title_html = format_if_empty("<br>".join(
            f"<div class='error'><p><h3>{e(report.first_doc_name)}:</h3> {format_section(original)}</p><p><h3>{e(report.second_doc_name)}:</h3>{format_section(other)}</p></div>"
            for original, other in report.not_same_title
        ))

        not_same_description_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>{e(report.first_doc_name)}:</h3> {format_section(original)}</p><p><h3>{e(report.second_doc_name)}:</h3> {format_section(other)}</p></div>"
            for original, other in report.not_same_description
        ))

        case_not_found_at_all_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>{e(names[doc])}:</h3> {format_section(original)}</p><p><h3>Case not found:</h3> {format_case(case)}</p></div>"
            for original, other, case, doc in report.case_not_found_at_all
        ))

        case_right_not_found_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>{e(names[doc])}:</h3> {format_section(original)}</p><p><h3>Case:</h3> {format_case(case)}</p><p>Left cases found: {chr(10).join(format_case(left) for left in lefts)}</p></div>"
            for original, other, case, lefts, doc in report.case_right_not_found
        ))

        case_found_multiple_times_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>{e(names[doc])}:</h3> {format_section(original)}</p><p><h3>Case found multiple times:</h3> {format_case(case)}</p><p>Preciser cases: {', '.join(str(p) for p in preciser)}</p></div>"
            for original, other, case, preciser, doc in report.case_found_multiple_times
        ))

        case_code_not_same_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>Section:</h3> {format_section(original)}</p><p><h3>{e(report.first_doc_name)}:</h3> {format_case(original_case)}</p><p><h3>{e(report.second_doc_name)}</h3>: {format_case(other_case)}</p></div>"
            "<b>line-diffs</b> : " + "<br>".join(
                difflib.unified_diff(original_case.code.replace('\xa0','').replace(' ','').splitlines(), other_case.code.replace('\xa0','').replace(' ','').splitlines()))

            for original, other, original_case, other_case in report.case_code_not_same
        ))

        correct_html = format_if_empty("".join(
            f"<div class='success'><p><h3>{e(original.title)}:</h3></p></div>"
            for original, other in report.correct
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

        file_path = os.path.abspath(os.path.join(report_path,"comparison.html"))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("[LOG] Report generated successfully")
        # Open the HTML file in the default web browser
        webbrowser.open('file://' + file_path, new=2)
        return html_content
