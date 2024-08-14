from dataclasses import dataclass
from typing import TypeVar, Generic
from html import escape

from aligner_utils import Content
from error_warning_count import ErrorWarningCount

T = TypeVar('T', bound='Content', covariant=True)


@dataclass(frozen=True)
class OrderedDictionnary(Generic[T], Content):
    entries: dict[str, T]
    entries_list: list[str]

    def to_text(self, indenting: int) -> str:
        if self.count_errors() == ErrorWarningCount(0,0):
            return f"{'  '*indenting}ORDERED DICT: OK\n"
        return (f"{'  '*indenting}ORDERED DICT: OK\n" +
                ''.join('  '*(indenting+1)+k +
                        self.entries[k].to_text(indenting+1)[2*indenting:] for k in self.entries_list))

    def to_html(self, is_in_error: bool) -> str:
        error_count = self.count_errors()
        items = ''.join(f'<li><h3>{escape(key)}:</h3> {self.entries[key].to_html(is_in_error)}</li>' for key in
                        self.entries_list)
        return (
            f'<div class="toggle">Ordered Dictionary{error_count.to_html(is_in_error)}{self.render_positions_html()}</div>'
            f'<div class="content"><ul>{items}</ul></div>')

    def count_errors(self) -> ErrorWarningCount:
        return sum([element.count_errors() for element in self.entries.values()],
                   start=ErrorWarningCount(0, 0))

    def __getitem__(self, item):
        return self.entries.get(item)

    def __eq__(self, other):
        return (isinstance(other, OrderedDictionnary) and
                self.entries == other.entries and
                self.entries_list == other.entries_list)

    def __hash__(self):
        return hash((self.entries, self.entries_list))
