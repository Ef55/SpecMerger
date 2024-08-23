import os
import webbrowser

from python_parser import PythonParser
from json_parser import JSONParser
from spec_merger.aligner import Aligner
from spec_merger.html_renderer import HTMLRenderer


def compare_jsons_and_see_html_report():
    parsed1 = JSONParser("jsons/spec.json", "Specification").get_parsed_page()
    parsed2 = PythonParser("jsons/implem.py").get_parsed_page()
    alignment_result = Aligner().align(parsed1.entries, parsed2.entries)
    rendered = HTMLRenderer(alignment_result).render(path_to_template="../spec_merger")
    with open("json_comparison_report.html", "w+") as f:
        f.write(rendered)
    webbrowser.open(f"file://{os.path.abspath('json_comparison_report.html')}", 2)


def compare_jsons_and_see_minimal_text_report():
    parsed1 = JSONParser("jsons/spec.json", "ONE").get_parsed_page()
    parsed2 = PythonParser("jsons/implem.py").get_parsed_page()
    alignment_result = Aligner().align(parsed1.entries, parsed2.entries)
    print(alignment_result.to_text(0))


if __name__ == "__main__":
    print("""You are comparing spec.json and implem.py
[1] If you want to see a nice HTML report
[2] If you want to see a minimal text report
""")
    while True:
        choice = input("Enter your choice: ")
        if choice == "1":
            compare_jsons_and_see_html_report()
        elif choice == "2":
            compare_jsons_and_see_minimal_text_report()
        else:
            print("Invalid choice")
