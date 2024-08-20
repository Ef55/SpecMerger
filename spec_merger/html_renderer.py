import os.path

from .aligner_utils import Content
from .error_warning_count import ErrorWarningCount


class HTMLRenderer:
    def __init__(self, parsed_page: Content):
        """
        HTML Renderer to be added at the last step of the pipeline. Takes in the ParsedPage containing the already
        combined tree between the 2 documents.

        :param parsed_page: The tree representing the result of the GenericComparer class
        """
        self.__parsed_page = parsed_page

    def render(self, path_to_template: str = "") -> str:
        """
        Renders the parsed page from the html template
        :return: An HTML document representing the final report
        """
        with open(os.path.join(path_to_template,"generic_template.html"), "r") as f:
            html = f.read()
        return html.format(content=self.__parsed_page.to_html(False))

    def get_errors(self) -> ErrorWarningCount:
        """
        Returns the number of errors and warnings in the parsed page
        :return: An ErrorWarningCount representing the number of errors and warnings
        """
        return self.__parsed_page.count_errors()
