import os
import random
import sys
import webbrowser

from aligner import Aligner
from coq_parser import COQParser
from html_renderer import HTMLRenderer
from json_parser import JSONParser
from ecma_parser import ECMAParser
from utils import Path


def main(open_in_browser:bool):
    random.seed(12)
    parsed1 = JSONParser("jsons/test.json", "ONE").get_parsed_page()
    parsed2 = JSONParser("jsons/test2.json", "TWO").get_parsed_page()
    alignment_result = Aligner().align(parsed1.entries,parsed2.entries)
    rendered = HTMLRenderer(alignment_result).render()
    with open("jsons.html","w") as f:
        f.write(rendered)
    webbrowser.open(f"file://{os.path.abspath('jsons.html')}", 2)
    print(alignment_result.to_text(0))
    exit(0)
    paths = [Path("../warblre/mechanization/spec/", True)]
    files_to_exclude = [Path("../warblre/mechanization/spec/Node.v", False)]
    url = "https://262.ecma-international.org/14.0/"

    coq_parser = COQParser(paths, files_to_exclude)
    coq_parsed_page = coq_parser.get_parsed_page()
    ecma_parser_v14 = ECMAParser(url, parser_name="ECMAScript v14.0")
    ecma_parsed_page_v14 = ecma_parser_v14.get_parsed_page()

    a = Aligner()
    result = a.align(coq_parsed_page.entries, ecma_parsed_page_v14.entries)
    renderer = HTMLRenderer(result)
    errors = renderer.get_errors()
    if errors.error_count == 0:
        print("The documents correspond !")
    else:
        print("ERRORS DETECTED")
    render = renderer.render()
    with open("generic_result.html", "r") as f:
        assert f.read() == render
    if open_in_browser:
        webbrowser.open(f"file://{os.path.abspath('generic_result.html')}", 2)
    return 1 if errors.error_count != 0 else 0

if __name__ == "__main__":
    sys.exit(main(True))
