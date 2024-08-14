import os
import sys
import webbrowser

from GenericComparer import Aligner
from GenericCoqParser import GenericCOQParser
from HTMLRenderer import HTMLRenderer
from JSONParser import JSONParser
from comparer_utils import String, OrderedSeq, Content, Bag, Dictionnary
from GenericECMAParser import GenericECMAParser
from utils import GenericParsedPage, Path


def main(open_in_browser:bool):
    parsed1 = JSONParser("jsons/test.json", "ONE").get_parsed_page()
    parsed2 = JSONParser("jsons/test2.json", "TWO").get_parsed_page()
    paths = [Path("../warblre/mechanization/spec/", True)]
    files_to_exclude = [Path("../warblre/mechanization/spec/Node.v", False)]
    url = "https://262.ecma-international.org/14.0/"

    coq_parser = GenericCOQParser(paths, files_to_exclude)
    coq_parsed_page = coq_parser.get_parsed_page()
    ecma_parser_v14 = GenericECMAParser(url, parser_name="ECMAScript v14.0")
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
