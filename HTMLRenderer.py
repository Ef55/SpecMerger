from typing import Callable

from comparer_utils import Content, OrderedSeq, String, Bag, Dictionnary, WildCard, AlignmentError, \
    AlignmentNotPossible, OrderedDictionnary, GenericPosition
from html import escape


class ErrorWarningCount:
    """
    Class to represent the number of warnings and errors encountered during comparison
    """

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
        return isinstance(other,
                          ErrorWarningCount) and self.error_count == other.error_count and self.warning_count == other.warning_count


class HTMLRenderer:
    def __init__(self, parsed_page: Content,
                 render_functions_for_added_types: dict[type, Callable[[Content, bool], str]] = None,
                 count_errors_function: dict[type, Callable[[Content], ErrorWarningCount]] = None):
        """
        HTML Renderer to be added at the last step of the pipeline. Takes in the ParsedPage containing the already
        combined tree between the 2 documents, and some additional functions for special types of `Content` that were
        added by you.

        :param parsed_page: The tree representing the result of the GenericComparer class

        :param render_functions_for_added_types: A dict with every key being a type that was added and its value being the corresponding rendering function on html, which takes as input the content and whether it is in an error or not.

        :param count_errors_function:  A dict with every key being a type that was added and its value being a function to count the number of errors and warnings encountered in its subtree.
        """
        self.__parsed_page = parsed_page
        self.__render_functions = render_functions_for_added_types
        if self.__render_functions is None:
            self.__render_functions = {}
        self.__count_errors_function = count_errors_function
        if self.__count_errors_function is None:
            self.__count_errors_function = {}
        self.__populate_render_functions()
        self.__populate_count_errors_functions()

    def __populate_render_functions(self):
        self.__render_functions[OrderedSeq] = self.__render_sequence
        self.__render_functions[Bag] = self.__render_bag
        self.__render_functions[Dictionnary] = self.__render_dictionary
        self.__render_functions[OrderedDictionnary] = self.__render_ordered_dictionary
        self.__render_functions[String] = self.__render_string
        self.__render_functions[AlignmentError] = self.__render_alignment_error
        self.__render_functions[AlignmentNotPossible] = self.__render_alignment_not_possible
        self.__render_functions[WildCard] = self.__render_wildcard
        self.__render_functions[type(None)] = lambda x, y: "None"

    def __populate_count_errors_functions(self):
        self.__count_errors_function[OrderedSeq] = lambda o: sum(
            self.__count_errors(element) for element in o.sequence) + ErrorWarningCount(0, 0)
        self.__count_errors_function[Bag] = lambda b: sum(
            self.__count_errors(element) for element in b.bag) + ErrorWarningCount(0, 0)
        self.__count_errors_function[Dictionnary] = lambda d: sum(
            self.__count_errors(element) for element in d.entries.values()) + ErrorWarningCount(0, 0)
        self.__count_errors_function[OrderedDictionnary] = self.__count_errors_function[Dictionnary]
        self.__count_errors_function[String] = lambda s: ErrorWarningCount(0, 0)
        self.__count_errors_function[AlignmentError] = lambda a: ErrorWarningCount(1, 0) \
            if a.warning.is_error() else ErrorWarningCount(0, 1)
        self.__count_errors_function[AlignmentNotPossible] = lambda a: ErrorWarningCount(1, 0) \
            if a.error.is_error() else ErrorWarningCount(0, 1)
        self.__count_errors_function[WildCard] = lambda w: ErrorWarningCount(0, 0)
        self.__count_errors_function[type(None)] = lambda n: ErrorWarningCount(0, 0)

    def render(self) -> str:
        """
        Renders the parsed page from the html template
        :return: An HTML document representing the final report
        """
        with open("generic_template.html", "r") as f:
            html = f.read()
        return html.format(content=self.__render_content(self.__parsed_page, False))

    def get_errors(self) -> ErrorWarningCount:
        """
        Returns the number of errors and warnings in the parsed page
        :return: An ErrorWarningCount representing the number of errors and warnings
        """
        return self.__count_errors(self.__parsed_page)

    def __render_content(self, content: Content, is_in_error: bool) -> str:
        render_function = self.__render_functions.get(type(content))
        if render_function is None:
            raise NotImplementedError(f"The function for type {type(content)} is not defined,"
                                      f" therefore the render can't be done")
        return render_function(content, is_in_error)

    def __render_sequence(self, seq: OrderedSeq, is_in_error: bool) -> str:
        error_count = self.__count_errors(seq)
        items = ''.join(f'<li>{self.__render_content(item, is_in_error)}</li>' for item in seq.sequence)
        return (
            f'<div class="toggle">OrderedSeq {self.__num_error_string(error_count, is_in_error)}{self.__render_positions(seq)}</div>'
            f'<div class="content"><ol>{items}</ol></div>')

    def __render_bag(self, bag: Bag, is_in_error: bool) -> str:
        error_count = self.__count_errors(bag)
        items = ''.join(f'<li>{self.__render_content(item, is_in_error)}</li>' for item in bag.bag)
        return (
            f'<div class="toggle">Bag {self.__num_error_string(error_count, is_in_error)}{self.__render_positions(bag)}</div>'
            f'<div class="content"><ul>{items}</ul></div>')

    def __render_dictionary(self, dictionary: Dictionnary, is_in_error: bool) -> str:
        error_count = self.__count_errors(dictionary)
        items = ''.join(f'<li><h3>{key}:</h3> {self.__render_content(value, is_in_error)}</li>' for key, value in
                        sorted(dictionary.entries.items(), key=lambda x: x[0]))

        return (
            f'<div class="toggle">Dictionary{self.__num_error_string(error_count, is_in_error)}{self.__render_positions(dictionary)}</div>'
            f'<div class="content"><ul>{items}</ul></div>')

    def __render_ordered_dictionary(self, dictionary: OrderedDictionnary, is_in_error: bool) -> str:
        error_count = self.__count_errors(dictionary)
        items = ''.join(
            f'<li><strong>{key}:</strong> {self.__render_content(dictionary.entries[key], is_in_error)}</li>' for key in
            dictionary.entries_list)

        return (
            f'<div class="toggle">OrderedDictionary{self.__num_error_string(error_count, is_in_error)}{self.__render_positions(dictionary)}</div>'
            f'<div class="content"><ul>{items}</ul></div>')

    def __render_string(self, string: String, is_in_error: bool) -> str:
        return f'<div>\"{escape(string.value)}\"{self.__render_positions(string)}</div>'

    def __render_wildcard(self, wildcard: WildCard, is_in_error: bool) -> str:
        return f'<div class="wildcard">Wildcard{self.__render_positions(wildcard)}</div>'

    def __render_alignment_error(self, alignment_error: AlignmentError, is_in_error: bool):
        error_class = "alignment-error > ERROR" if alignment_error.warning.is_error() else "alignment-warning > WARNING"
        return (f'<div>'
                f'<div class={error_class} {alignment_error.warning}</div>'
                f'<div>{self.__render_content(alignment_error.value, is_in_error)}</div>'
                f'</div>')

    def __render_alignment_not_possible(self, alignment_not_possible: AlignmentNotPossible, is_in_error: bool):
        error_class = "alignment-error > ERROR" if alignment_not_possible.error.is_error() else "alignment-warning > WARNING"
        return (f'<div>'
                f'<div class={error_class} {alignment_not_possible.error}</div>'
                f'<div class="text-displayer">{self.__render_content(alignment_not_possible.left, True)}</div>'
                f'<div> VS </div>'
                f'<div class="text-displayer">{self.__render_content(alignment_not_possible.right, True)}</div>'
                f'</div>')

    @staticmethod
    def __num_error_string(errors_and_warnings: ErrorWarningCount, is_in_error: bool) -> str:
        if is_in_error:
            return ""
        if errors_and_warnings == ErrorWarningCount(0, 0):
            return "<span class='no-error'>(Fine)</span>"
        return (f"<span class='error-count'>({errors_and_warnings.error_count} errors, "
                f"{errors_and_warnings.warning_count} warnings)</span> ")

    def __count_errors(self, content: Content) -> ErrorWarningCount:
        count_function = self.__count_errors_function.get(type(content))
        if count_function is None:
            raise NotImplementedError(f"The function for type {type(content)} is not defined,"
                                      f" therefore the count can't be done")
        return count_function(content)

    @staticmethod
    def __render_positions(content: Content) -> str:
        if not content.position:
            return ""
        if isinstance(content.position, GenericPosition):
            return ", <div> POS: " + content.position.html_str() + "</div>"
        return ", <div> POS: " + ", ".join(
            content.position[i].html_str() for i in range(2) if content.position[i]) + "</div>"
