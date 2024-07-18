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

    ecma_parser = ECMAParser(url,parser_name="ECMA 14.0")
    ecma_parsed_page = ecma_parser.get_parsed_page()

    ecma_parser_2 = ECMAParser(url2, parser_name="ECMA 15.0")
    ecma_parsed_page_2 = ecma_parser_2.get_parsed_page()

    print(ecma_parsed_page["22.2.1.7"].title)
    print(ecma_parsed_page_2["22.2.1.7"].title)
    comparer = Comparer(coq_parsed_page,ecma_parsed_page, sections_to_exclude)
    report = comparer.produce_report()

    Formatter.format(report, "/home/martin/regex_coq/parser/v15")


if __name__ == "__main__":
    main()
