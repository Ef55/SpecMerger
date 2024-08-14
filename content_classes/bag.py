from typing import TypeVar, Generic

from dataclasses import dataclass

from aligner_utils import Content
from error_warning_count import ErrorWarningCount

T = TypeVar('T', bound='Content', covariant=True)


@dataclass(frozen=True)
class Bag(Generic[T], Content):
    # represents a set but stored as list to avoid non-determinism
    bag: list[T]

    def to_text(self, indenting: int) -> str:
        if self.count_errors() == ErrorWarningCount(0,0):
            return f"{'  '*indenting}ORDERED SEQ: OK\n"
        return f"{'  '*indenting}ORDERED SEQ: OK\n{''.join(x.to_text(indenting+1) for x in self.bag)}"

    def count_errors(self) -> ErrorWarningCount:
        return sum([element.count_errors() for element in self.bag],
                   start=ErrorWarningCount(0, 0))

    def to_html(self, is_in_error: bool) -> str:
        error_count = self.count_errors()
        items = ''.join(f'<li>{item.to_html(is_in_error)}</li>' for item in self.bag)
        return (
            f'<div class="toggle">Bag {error_count.to_html(is_in_error)}{self.render_positions_html()}</div>'
            f'<div class="content"><ul>{items}</ul></div>')

    def __eq__(self, other):
        return isinstance(other, Bag) and set(self.bag) == set(other.bag)

    def __hash__(self):
        return hash(self.bag)
