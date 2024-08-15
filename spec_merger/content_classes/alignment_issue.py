from dataclasses import dataclass

from spec_merger.aligner_utils import Content, ReportErrorType
from spec_merger.error_warning_count import ErrorWarningCount


@dataclass(frozen=True)
class AlignmentIssue(Content):
    value: Content
    warning: ReportErrorType

    def to_text(self, indenting: int) -> str:
        return f"{'  '*indenting}!WARNING! {str(self.warning)}\n{self.value.to_text(indenting)}"

    def to_html(self, is_in_error: bool) -> str:
        error_class = "alignment-error > ERROR" if self.warning.is_error() else "alignment-warning > WARNING"
        return (f'<div>'
                f'<div class={error_class} {self.warning}</div>'
                f'<div>{self.value.to_html(is_in_error)}</div>'
                f'</div>')

    def count_errors(self) -> ErrorWarningCount:
        return ErrorWarningCount(1, 0) if self.warning.is_error() \
            else ErrorWarningCount(0, 1)
