from dataclasses import dataclass
from typing import TypeVar, Generic

from aligner_utils import Content
from error_warning_count import ErrorWarningCount

T = TypeVar('T', bound='Content', covariant=True)


@dataclass(frozen=True)
class WildCard(Generic[T], Content):
    def to_text(self, indenting: int) -> str:
        return "  " * indenting + "WildCard\n"

    def to_html(self, is_in_error: bool) -> str:
        return f'<div class="wildcard">Wildcard{self.render_positions_html()}</div>'

    def count_errors(self) -> ErrorWarningCount:
        return ErrorWarningCount(0, 1)

    def __eq__(self, other):
        return isinstance(other, WildCard)

    def __hash__(self):
        return hash(WildCard)
