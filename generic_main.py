import os
import webbrowser

from GenericComparer import Aligner
from GenericCoqParser import GenericCOQParser
from GenericParsedPageRenderer import GenericParsedPageRenderer
from JSONParser import JSONParser
from comparer_utils import String, OrderedSeq, Content, Bag, Dictionnary
from genericECMAParser import GenericECMAParser
from utils import GenericParsedPage, Path


def main():
    parsed1 = JSONParser("jsons/test.json","ONE").get_parsed_page()
    parsed2 = JSONParser("jsons/test2.json","TWO").get_parsed_page()
    paths = [Path("../warblre/mechanization/spec/", True)]
    files_to_exclude = [Path("../warblre/mechanization/spec/Node.v", False)]
    sections_to_exclude = ["22.2.1"]
    url = "https://262.ecma-international.org/14.0/"


    coq_parser = GenericCOQParser(paths, files_to_exclude)
    coq_parsed_page = coq_parser.get_parsed_page()
    ecma_parser_v14 = GenericECMAParser(url,parser_name="ECMAScript v14.0")
    ecma_parsed_page_v14 = ecma_parser_v14.get_parsed_page()

    a = Aligner()
    result = a.align(coq_parsed_page.entries, ecma_parsed_page_v14.entries)
    html = GenericParsedPageRenderer(result)
    with open("generic_result.html","w+") as f:
        f.write(html.render())
    webbrowser.open(f"file://{os.path.abspath('generic_result.html')}",2)


# main()
main()
