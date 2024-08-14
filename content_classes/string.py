from abc import ABC

from dataclasses import dataclass
from html import escape
from aligner_utils import Content
from error_warning_count import ErrorWarningCount


@dataclass(frozen=True)
class String(Content):
    value: str
    chars_useless: str = " \xa0"

    def real_string(self):
        s = self.value
        for c in self.chars_useless:
            s = s.replace(c, "")
        return s

    def count_errors(self) -> ErrorWarningCount:
        return ErrorWarningCount(0, 0)

    def to_text(self, indenting) -> str:
        return "  "*indenting + "STRING: OK\n"

    def to_html(self, is_in_error: bool) -> str:
        return f'<div>\"{escape(self.value)}\"{self.render_positions_html()}</div>'

    def __eq__(self, other):
        return isinstance(other, String) and self.real_string() == other.real_string()

    def __hash__(self):
        return hash(self.real_string())

    def __len__(self):
        return len(self.value)

    def __add__(self, other):
        if isinstance(other, String):
            return String(self.position, self.value + other.value)
        if isinstance(other, str):
            return String(self.position, self.value + other)
