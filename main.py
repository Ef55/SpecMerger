from ECMAParser import ECMAParser
from COQParser import COQParser
from Formatter import Formatter
from Comparer import Comparer
from utils import Path

def main():
    url = "https://262.ecma-international.org/14.0/"
    url2 = "https://262.ecma-international.org/15.0/"
    paths = [Path("../warblre/mechanization/spec/", True)]
    files_to_exclude = [Path("../warblre/mechanization/spec/Node.v", False)]
    sections_to_exclude = ["22.2.1"]

    coq_parser = COQParser(paths, files_to_exclude)
    coq_parsed_page = coq_parser.get_parsed_page()

    ecma_parser_v14 = ECMAParser(url,parser_name="ECMAScript v14.0")
    ecma_parsed_page_v14 = ecma_parser_v14.get_parsed_page()

    ecma_parser_v15 = ECMAParser(url2, parser_name="ECMAScript v15.0")
    ecma_parsed_page_v15 = ecma_parser_v15.get_parsed_page()

    comparer = Comparer(coq_parsed_page, ecma_parsed_page_v14, sections_to_exclude)
    report = comparer.produce_report()

    Formatter.format(report, "/home/martin/regex_coq/parser/v15")


if __name__ == "__main__":
    main()
