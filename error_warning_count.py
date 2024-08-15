class ErrorWarningCount:
    """
    Class to represent the number of warnings and errors encountered during comparison
    """

    def __init__(self, error_count: int = 0, warning_count: int = 0):
        assert isinstance(error_count, int)
        assert isinstance(warning_count, int)
        self.error_count: int = error_count
        self.warning_count: int = warning_count

    def to_html(self, is_in_error: bool) -> str:
        """
        Returns the HTML representation of the error count
        :param is_in_error: Whether the error count is in an subtree that had an error at its root
        :return: The HTML representation of the error count
        """
        if is_in_error:
            return ""
        if self == ErrorWarningCount(0, 0):
            return "<span class='no-error'>(Fine)</span>"
        return f"<span class='error-count'>({self.error_count} errors, {self.warning_count} warnings)</span> "

    def __add__(self, other):
        if not isinstance(other, ErrorWarningCount):
            return self
        return ErrorWarningCount(self.error_count + other.error_count, self.warning_count + other.warning_count)

    def __radd__(self, other):
        return self + other

    def __str__(self):
        return f"({self.error_count}, {self.warning_count})"

    def __eq__(self, other):
        return (isinstance(other, ErrorWarningCount) and
                self.error_count == other.error_count and
                self.warning_count == other.warning_count)
