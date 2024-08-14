from typing import TypeVar, Generic

from dataclasses import dataclass

from aligner_utils import Content
from error_warning_count import ErrorWarningCount

T = TypeVar('T', bound='Content', covariant=True)


@dataclass(frozen=True)
class OrderedSeq(Generic[T], Content):
    sequence: list[T]

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.sequence[item]

    def __eq__(self, other):
        return isinstance(other, OrderedSeq) and self.sequence == other.sequence

    def __hash__(self):
        return hash(self.sequence)

    def count_errors(self) -> ErrorWarningCount:
        return sum([element.count_errors() for element in self.sequence],
                   start=ErrorWarningCount(0, 0))

    def to_text(self, indenting: int) -> str:
        if self.count_errors() == ErrorWarningCount(0,0):
            return f"{'  '*indenting}ORDERED SEQ: OK\n"
        return f"{'  '*indenting}ORDERED SEQ: OK\n{''.join(x.to_text(indenting+1) for x in self.sequence)}"

    def to_html(self, is_in_error: bool) -> str:
        error_count = self.count_errors()
        items = ''.join(f'<li>{item.to_html(is_in_error)}</li>' for item in self.sequence)
        return (
            f'<div class="toggle">OrderedSeq {error_count.to_html(is_in_error)}'
            f'{self.render_positions_html()}</div>'
            f'<div class="content"><ol>{items}</ol></div>')
