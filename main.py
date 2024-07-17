from ECMAParser import ECMAParser
from COQParser import COQParser
from Formatter import Formatter
from Comparer import Comparer
from utils import Path


def main():
    url = "https://262.ecma-international.org/14.0/"
    paths = [Path("../warblre/mechanization/spec/", True)]
    files_to_exclude = [Path("../warblre/mechanization/spec/Node.v", False)]
    sections_to_exclude = ["22.2.1"]

    coq_parser = COQParser(paths, files_to_exclude)
    ecma_parser = ECMAParser(url)

    comparer = Comparer(ecma_parser, coq_parser, sections_to_exclude)
    report = comparer.compare_auto()

    Formatter.format(report, "/home/martin/regex_coq/")


if __name__ == "__main__":
    main()
