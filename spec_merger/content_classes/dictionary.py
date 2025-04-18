from typing import TypeVar, Generic
from html import escape
from dataclasses import dataclass

from spec_merger.aligner_utils import Content
from spec_merger.error_warning_count import ErrorWarningCount

T = TypeVar('T', bound='Content', covariant=True)


@dataclass(frozen=True)
class Dictionary(Generic[T], Content):
    entries: dict[str, T]

    def to_text(self, indenting: int = 0) -> str:
        if self.count_errors() == ErrorWarningCount(0,0):
            return "  "*indenting+"DICT: OK\n"
        return f"{'  '*indenting}DICT: OK\n{''.join('  '*(indenting+1)+k +self.entries[k].to_text(indenting+1)[2*indenting:] for k in sorted(self.entries.keys()))}"

    def to_html(self, is_in_error: bool) -> str:
        error_count = self.count_errors()
        items = ''.join(f'<li><h3>{escape(key)}:</h3> {value.to_html(is_in_error)}</li>' for key, value in
                        sorted(self.entries.items(), key=lambda x: x[0]))
        return (
            f'<div class="toggle">Dictionary{error_count.to_html(is_in_error)}{self.render_positions_html()}</div>'
            f'<div class="content"><ul>{items}</ul></div>')

    def count_errors(self) -> ErrorWarningCount:
        return sum([element.count_errors() for element in self.entries.values()],
                   start=ErrorWarningCount(0, 0))

    def __getitem__(self, item):
        return self.entries.get(item)

    def __eq__(self, other):
        return isinstance(other, Dictionary) and self.entries == other.entries

    def __hash__(self):
        return hash(self.entries)
