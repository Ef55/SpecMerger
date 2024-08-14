from dataclasses import dataclass
from typing import Optional

from aligner_utils import Content, ReportErrorType
from error_warning_count import ErrorWarningCount


@dataclass(frozen=True)
class Misalignment(Content):
    left: Optional[Content]
    right: Optional[Content]
    error: ReportErrorType

    def to_text(self, indenting) -> str:
        none_str = "  "*(indenting+1) + "NONE\n"
        left = self.left.to_text(indenting+1) if self.left is not None else none_str
        right = self.right.to_text(indenting+1) if self.right is not None else none_str
        return f"{'  '*indenting}!MISALIGNMENT! {str(self.error)}\n{left}{right}"

    def to_html(self, is_in_error: bool) -> str:
        error_class = "alignment-error > ERROR" if self.error.is_error() else "alignment-warning > WARNING"
        return (f'<div>'
                f'<div class={error_class} {self.error}</div>'
                f'<div class="text-displayer">{self.left.to_html(True) if self.left is not None else "None"}</div>'
                f'<div> VS </div>'
                f'<div class="text-displayer">{self.right.to_html(True) if self.right is not None else "None"}</div>'
                f'</div>')

    def count_errors(self) -> ErrorWarningCount:
        return ErrorWarningCount(1, 0) if self.error.is_error() \
            else ErrorWarningCount(0, 1)
