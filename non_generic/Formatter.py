import html
import os
import webbrowser
import difflib

from Report import Report
from utils import SubSection, Case


def check_doc(doc: int):
    assert doc in {0, 1}


class Formatter:
    """
    Formats a report into an HTML file and opens it in the default web browser
    @:param report: The report to format
    @:param report_path: The path to save the report
    """

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
        with open("formatted_template.html", "r", encoding="utf-8") as f:
            html_template = f.read()

        def format_section(section: SubSection, other_section=None):
            mid_string = ""
            if other_section is not None:
                mid_string = f", {other_section.position.html_str()}"
            return (f"<div class='section'>"
                    f"<h3>{e(section.title)}, {section.position.html_str() + mid_string}</h3>"
                    f"<p>{e(section.description)}</p>"
                    f"</div>")

        def format_case(case: Case):
            return f"""
                <div class='case'>
                    <p>{html.escape(case.left_title)} :: {html.escape(case.right_title)}, {case.position.html_str()}</p>
                    <div class='case-content'>
                        <pre>{html.escape(case.code)}</pre>
                    </div>
                </div>
                """

        def format_if_empty(section: str):
            return section if section != "" else "Empty"

        correct_html = format_if_empty("".join(format_section(original, other)
                                               for original, other in report.correct))

        not_found_html = format_if_empty("<br>".join(
            f"<div class='error'>"
            f"<p><h3>Not found in {e(names[i])}:</h3>" +
            f" {format_if_empty(''.join(format_section(section) for section in report.not_found[i]))}"
            f"</p></div>"
            for i in range(2)))

        not_same_title_html = format_if_empty("".join(
            f"<div class='comparison-pair'>"
            f"<p><h3>In {e(report.first_doc_name)}:</h3> {format_section(original)}</p>"
            f"<p><h3>In {e(report.second_doc_name)}:</h3>{format_section(other)}</p>"
            f"</div>"
            for original, other in report.not_same_title
        ))

        not_same_description_html = format_if_empty("".join(
            f"<div class='comparison-pair'>"
            f"<p><h3>In {e(report.first_doc_name)}:</h3> {format_section(original)}</p>"
            f"<p><h3>In {e(report.second_doc_name)}:</h3> {format_section(other)}</p>"
            f"</div>"
            for original, other in report.not_same_description
        ))

        def format_not_found():
            html_return = ["<div class='error'>"]
            for key in report.case_not_found_at_all.keys():
                section_1, section_2, cases_dict = report.case_not_found_at_all[key]
                html_return.append(f"<p>{format_section(section_1, section_2)}</p>")
                for i in range(2):
                    cases_i = cases_dict[i]
                    if not cases_i:
                        continue
                    html_return.append(f"<p><h3>In {e(names[i])}:</h3></p>")
                    html_return.append(
                        "".join(f"<p><h3>Case not found:</h3> {format_case(case)}</p>" for case in cases_i)
                    )
            html_return.append("</div>")
            return "".join(html_return)

        case_not_found_at_all_html = format_not_found()

        case_right_not_found_html = format_if_empty("<br><br>".join(
            f"<div class='error'>"
            f"<p><h3>IN {e(names[doc])}:</h3> {format_section(original)}</p>"
            f"<p><h3>Case:</h3> {format_case(case)}</p>"
            f"<p><h3>Left cases found:</h3> {chr(10).join(format_case(left) for left in lefts)}</p></div>"
            for original, other, case, lefts, doc in report.case_right_not_found
        ))

        case_found_multiple_times_html = format_if_empty("<br><br>".join(
            f"<div class='error'><p><h3>IN {e(names[doc])}:</h3> {format_section(original)}</p>"
            f"<p><h3>Cases with same title found:</h3>\n{(chr(10) + chr(10)).join(format_case(case) for case in cases)}</p></div>"
            for original, cases, doc in report.case_found_multiple_times
        ))

        def format_diff(original_code, other_code):
            diff = list(difflib.unified_diff(
                original_code.splitlines(),
                other_code.splitlines(),
                lineterm='',
                n=3
            ))

            if not diff:
                return "<p>No differences found.</p>"

            html_diff = ['<table class="diff-table">']
            for line in diff[3:]:  # Skip the first three lines (header)
                if line.startswith('+'):
                    html_diff.append(
                        f'<tr class="diff-add"><td class="diff-line-num">+</td><td>{html.escape(line[1:])}</td></tr>')
                elif line.startswith('-'):
                    html_diff.append(
                        f'<tr class="diff-remove">'
                        f'<td class="diff-line-num">-</td><td>{html.escape(line[1:])}</td>'
                        f'</tr>')
                elif line.startswith('@@'):
                    html_diff.append(f'<tr><td colspan="2" style="color: #6e7781;">{html.escape(line)}</td></tr>')
                else:
                    html_diff.append(f'<tr><td class="diff-line-num"></td><td>{html.escape(line)}</td></tr>')
            html_diff.append('</table>')

            return ''.join(html_diff)

        def format_case_code_not_same():
            case_code_not_same_html = []
            for i, (original, other, original_case, other_case) in enumerate(report.case_code_not_same):
                section_html = f"""
                <div class='section error'>
                    <h3>Section with Different Code</h3>
                    <p>{format_section(original, other)}</p>
                    <div class='case'>
                        <p>Case with different code</p>
                        <div class='case-content'>
                            <h4>IN {html.escape(report.first_doc_name)}:</h4>
                            {format_case(original_case)}
                            <h4>IN {html.escape(report.second_doc_name)}:</h4>
                            {format_case(other_case)}
                            <h4>Code Differences:</h4>
                            {format_diff(original_case.code, other_case.code)}
                        </div>
                    </div>
                </div>
                """
                case_code_not_same_html.append(section_html)

            return ''.join(
                case_code_not_same_html) if case_code_not_same_html else "No cases with different code found."

        case_code_not_same_html = format_case_code_not_same()

        html_content = html_template.format(
            not_found=not_found_html,
            not_same_title=not_same_title_html,
            not_same_description=not_same_description_html,
            case_not_found_at_all=case_not_found_at_all_html,
            case_right_not_found=case_right_not_found_html,
            case_found_multiple_times=case_found_multiple_times_html,
            case_code_not_same=case_code_not_same_html,
            correct=correct_html,
            first_doc_name=e(report.first_doc_name),
            second_doc_name=e(report.second_doc_name),
            not_found_count=len(report.not_found[0]) + len(report.not_found[1]),
            diff_title_count=len(report.not_same_title),
            diff_desc_count=len(report.not_same_description),
            case_not_found_count=len(report.case_not_found_at_all),
            case_right_not_found_count=len(report.case_right_not_found),
            case_multiple_count=len(report.case_found_multiple_times),
            case_diff_code_count=len(report.case_code_not_same),
            correct_count=len(report.correct)
        )

        file_path = os.path.abspath(os.path.join(report_path, "comparison_report.html"))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("[LOG] Report generated successfully")
        # Open the HTML file in the default web browser
        webbrowser.open('file://' + file_path, new=2)
        return html_content
