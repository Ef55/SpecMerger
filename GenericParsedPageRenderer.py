from typing import Callable

from comparer_utils import Content, OrderedSeq, String, Bag, Dictionnary, WildCard, AlignmentError, \
    AlignmentNotPossible, OrderedDictionnary, GenericPosition
from html import escape


class ErrorWarningCount:
    def __init__(self, error_count: int = 0, warning_count: int = 0):
        self.error_count = error_count
        self.warning_count = warning_count

    def __add__(self, other):
        if not isinstance(other, ErrorWarningCount):
            return self
        return ErrorWarningCount(self.error_count + other.error_count, self.warning_count + other.warning_count)

    def __radd__(self, other):
        return self + other

    def __str__(self):
        return f"({self.error_count}, {self.warning_count})"
    def __eq__(self, other):
        return isinstance(other, ErrorWarningCount) and self.error_count == other.error_count and self.warning_count == other.warning_count


class GenericParsedPageRenderer:
    def __init__(self, parsed_page: Content,
                 render_functions_for_added_types: dict[type, Callable[[Content, bool], str]] = None,
                 count_errors_function: dict[type, Callable[[Content], int]] = None):
        self.parsed_page = parsed_page
        self.render_functions = render_functions_for_added_types
        if self.render_functions is None:
            self.render_functions = {}
        self.count_errors_function = count_errors_function
        if self.count_errors_function is None:
            self.count_errors_function = {}
        self.populate_render_functions()
        self.populate_count_errors_functions()

    def populate_render_functions(self):
        self.render_functions[OrderedSeq] = self._render_sequence
        self.render_functions[Bag] = self._render_bag
        self.render_functions[Dictionnary] = self._render_dictionary
        self.render_functions[OrderedDictionnary] = self._render_ordered_dictionary
        self.render_functions[String] = self._render_string
        self.render_functions[AlignmentError] = self._render_alignment_error
        self.render_functions[AlignmentNotPossible] = self._render_alignment_not_possible
        self.render_functions[WildCard] = self._render_wildcard
        self.render_functions[type(None)] = lambda x, y: "None"

    def populate_count_errors_functions(self):
        self.count_errors_function[OrderedSeq] = lambda o: sum(self._count_errors(element) for element in o.sequence)+ErrorWarningCount(0,0)
        self.count_errors_function[Bag] = lambda b: sum(self._count_errors(element) for element in b.bag)+ErrorWarningCount(0,0)
        self.count_errors_function[Dictionnary] = lambda d: sum(
            self._count_errors(element) for element in d.entries.values()) + ErrorWarningCount(0,0)
        self.count_errors_function[OrderedDictionnary] = self.count_errors_function[Dictionnary]
        self.count_errors_function[String] = lambda s: ErrorWarningCount(0, 0)
        self.count_errors_function[AlignmentError] = lambda a: ErrorWarningCount(1, 0) \
            if a.warning.is_error() else ErrorWarningCount(0, 1)
        self.count_errors_function[AlignmentNotPossible] = lambda a: ErrorWarningCount(1, 0) \
            if a.error.is_error() else ErrorWarningCount(0, 1)
        self.count_errors_function[WildCard] = lambda w: ErrorWarningCount(0, 0)
        self.count_errors_function[type(None)] = lambda n: ErrorWarningCount(0, 0)

    def render(self) -> str:
        with open("generic_template.html", "r") as f:
            html = f.read()
        return html.format(content=self._render_content(self.parsed_page, False))

    def _render_content(self, content: Content, is_in_error: bool) -> str:
        render_function = self.render_functions.get(type(content))
        if render_function is None:
            raise NotImplementedError(f"The function for type {type(content)} is not defined,"
                                      f" therefore the render can't be done")
        return render_function(content, is_in_error)

    def _render_sequence(self, seq: OrderedSeq, is_in_error: bool) -> str:
        error_count = self._count_errors(seq)
        items = ''.join(f'<li>{self._render_content(item, is_in_error)}</li>' for item in seq.sequence)
        return (
            f'<div class="toggle">OrderedSeq {self.num_error_string(error_count, is_in_error)}{self._render_positions(seq)}</div>'
            f'<div class="content"><ol>{items}</ol></div>')

    def _render_bag(self, bag: Bag, is_in_error: bool) -> str:
        error_count = self._count_errors(bag)
        items = ''.join(f'<li>{self._render_content(item, is_in_error)}</li>' for item in bag.bag)
        return (f'<div class="toggle">Bag {self.num_error_string(error_count, is_in_error)}{self._render_positions(bag)}</div>'
                f'<div class="content"><ul>{items}</ul></div>')

    def _render_dictionary(self, dictionary: Dictionnary, is_in_error: bool) -> str:
        error_count = self._count_errors(dictionary)
        items = ''.join(f'<li><h3>{key}:</h3> {self._render_content(value, is_in_error)}</li>' for key, value in
                        sorted(dictionary.entries.items(),key=lambda x: x[0]))

        return (f'<div class="toggle">Dictionary{self.num_error_string(error_count, is_in_error)}{self._render_positions(dictionary)}</div>'
                f'<div class="content"><ul>{items}</ul></div>')

    def _render_ordered_dictionary(self, dictionary: OrderedDictionnary, is_in_error: bool) -> str:
        error_count = self._count_errors(dictionary)
        items = ''.join(
            f'<li><strong>{key}:</strong> {self._render_content(dictionary.entries[key], is_in_error)}</li>' for key in
            dictionary.entries_list)

        return (f'<div class="toggle">OrderedDictionary{self.num_error_string(error_count, is_in_error)}{self._render_positions(dictionary)}</div>'
                f'<div class="content"><ul>{items}</ul></div>')

    def _render_string(self, string: String, is_in_error: bool) -> str:
        return f'<div>\"{escape(string.value)}\"{self._render_positions(string)}</div>'

    def _render_wildcard(self, wildcard: WildCard, is_in_error: bool) -> str:
        return f'<div class="wildcard">Wildcard{self._render_positions(wildcard)}</div>'

    def _render_alignment_error(self, alignment_error: AlignmentError, is_in_error: bool):
        error_class = "alignment-error > ERROR" if alignment_error.warning.is_error() else "alignment-warning > WARNING"
        return (f'<div>'
                f'<div class={error_class} {alignment_error.warning}</div>'
                f'<div>{self._render_content(alignment_error.value, is_in_error)}</div>'
                f'</div>')

    def _render_alignment_not_possible(self, alignment_not_possible: AlignmentNotPossible, is_in_error: bool):
        error_class = "alignment-error > ERROR" if alignment_not_possible.error.is_error() else "alignment-warning > WARNING"
        return (f'<div>'
                f'<div class={error_class} {alignment_not_possible.error}</div>'
                f'<div class="text-displayer">{self._render_content(alignment_not_possible.left, True)}</div>'
                f'<div> VS </div>'
                f'<div class="text-displayer">{self._render_content(alignment_not_possible.right, True)}</div>'
                f'</div>')

    @staticmethod
    def num_error_string(errors_and_warnings: ErrorWarningCount, is_in_error: bool) -> str:
        if is_in_error:
            return ""
        if errors_and_warnings == ErrorWarningCount(0,0):
            return "<span class='no-error'>(Fine)</span>"
        return (f"<span class='error-count'>({errors_and_warnings.error_count} errors, "
                f"{errors_and_warnings.warning_count} warnings)</span> ")

    def _count_errors(self, content: Content) -> ErrorWarningCount:
        count_function = self.count_errors_function.get(type(content))
        if count_function is None:
            raise NotImplementedError(f"The function for type {type(content)} is not defined,"
                                      f" therefore the count can't be done")
        return count_function(content)
    @staticmethod
    def _render_positions(content: Content) -> str:
        if not content.position:
            return ""
        if isinstance(content.position, GenericPosition):
            return ", <div> POS: " + content.position.html_str() + "</div>"
        return ", <div> POS: " + ", ".join(
            content.position[i].html_str() for i in range(2) if content.position[i]) + "</div>"
