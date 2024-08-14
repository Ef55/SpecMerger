from typing import Callable

from aligner_utils import Content
from error_warning_count import ErrorWarningCount


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

    def render(self) -> str:
        """
        Renders the parsed page from the html template
        :return: An HTML document representing the final report
        """
        with open("generic_template.html", "r") as f:
            html = f.read()
        return html.format(content=self.__parsed_page.to_html(False))

    def get_errors(self) -> ErrorWarningCount:
        """
        Returns the number of errors and warnings in the parsed page
        :return: An ErrorWarningCount representing the number of errors and warnings
        """
        return self.__parsed_page.count_errors()
