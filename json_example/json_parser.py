import json
import random
from dataclasses import dataclass

from spec_merger.aligner_utils import Content, Position
from spec_merger.content_classes.bag import Bag
from spec_merger.content_classes.dictionary import Dictionary
from spec_merger.content_classes.ordered_dictionary import OrderedDictionnary
from spec_merger.content_classes.ordered_seq import OrderedSeq
from spec_merger.content_classes.string import String
from spec_merger.content_classes.wildcard import WildCard
from spec_merger.utils import Parser, ParsedPage


@dataclass(frozen=True)
class JSONPosition(Position):
    position: str

    def html_str(self) -> str:
        return self.position


class JSONParser(Parser):
    def __init__(self, file_name: str, parser_num: str):
        with open(file_name, "r") as file:
            self.content = json.load(file)
        self.parsed_page: ParsedPage = None
        self.name = "JSONParser"
        self.parser_num = parser_num

    def new_pos(self):
        return JSONPosition(self.parser_num)

    def parse(self,content) -> Content:
        match content:
            case dict(dictionnary):
                keys = None
                if dictionnary.get("order", False):
                    keys = dictionnary["order"]
                entries = {}
                wildcards = dictionnary.get("wildcards", [])
                for key in dictionnary.keys():
                    if key == "wildcards" or key == "order":
                        pass
                    elif key in wildcards:
                        entries[key] = WildCard(self.new_pos())
                    else:
                        entries[key] = self.parse(dictionnary[key])
                if keys is not None:
                    return OrderedDictionnary(self.new_pos(), entries, keys)
                return Dictionary(self.new_pos(), entries)
            case list(values):
                is_ordered = values[0]
                parsed_list_values = map(self.parse, values[1:])
                if is_ordered:
                    return OrderedSeq(self.new_pos(), list(parsed_list_values))
                else:
                    return Bag(self.new_pos(), list(parsed_list_values))
            case str(value) | int(value) | float(value) | bool(value):
                return String(self.new_pos(), str(value))
            case _:
                raise Exception("Type can't be parsed for the moment")

    def get_parsed_page(self) -> ParsedPage:
        if self.parsed_page is not None:
            return self.parsed_page
        self.parsed_page = ParsedPage(self.name, Dictionary(self.new_pos(), {}))
        result = self.parse(self.content)
        match result:
            case Dictionary(_, ):
                self.parsed_page.entries = result
            case _:
                self.parsed_page.entries = Dictionary(self.new_pos(), {"content": result})
        return self.parsed_page
