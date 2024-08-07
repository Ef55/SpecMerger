import json
import random

from utils import GenericParser, GenericParsedPage
from comparer_utils import *


@dataclass(frozen=True)
class JSONPosition(GenericPosition):
    rand_value_so_not_equal: str

    def html_str(self) -> str:
        return str(random.randint(0, 1000)) + self.rand_value_so_not_equal


class JSONParser(GenericParser):
    def __init__(self, file_name: str, last_letter: str):
        with open(file_name, "r") as file:
            self.content = json.load(file)
        self.parsed_page: GenericParsedPage = None
        self.name = "JSONParser"
        self.last_letter = last_letter

    def new_pos(self):
        return JSONPosition(self.last_letter)

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
                return Dictionnary(self.new_pos(), entries)
            case list(values):
                is_ordered = values[0]
                parsed_list_values = map(self.parse, values[1:])
                if is_ordered:
                    return OrderedSeq(self.new_pos(), list(parsed_list_values))
                else:
                    return Bag(self.new_pos(), set(parsed_list_values))
            case str(value) | int(value) | float(value) | bool(value):
                return String(self.new_pos(), str(value))
            case _:
                raise Exception("Type can't be parsed for the moment")

    def get_parsed_page(self) -> GenericParsedPage:
        if self.parsed_page is not None:
            return self.parsed_page
        self.parsed_page = GenericParsedPage(self.name, Dictionnary(self.new_pos(), {}))
        result = self.parse(self.content)
        match result:
            case Dictionnary(_, ):
                self.parsed_page.entries = result
            case _:
                self.parsed_page.entries = Dictionnary(self.new_pos(), {"content": result})
        return self.parsed_page
