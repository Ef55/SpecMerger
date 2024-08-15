from .aligner_utils import Content, ReportErrorType
from .content_classes.misalignment import Misalignment
from .content_classes.wildcard import WildCard


class SpecialComparator:
    @staticmethod
    def compare_special(elem1: Content, elem2: Content, aligner) -> Content:
        match (elem1, elem2):
            case (WildCard(), _) | (_, WildCard()):
                return Misalignment((elem1.position, elem2.position), elem1, elem2, ReportErrorType.MATCHED_WILDCARDS)
            case (t1, t2) if type(t1) is not type(t2):
                return Misalignment((elem1.position, elem2.position), elem1, elem2, ReportErrorType.MISMATCHED_TYPES)
            case _:
                print(
                    f"[WARNING!!!!!] Function is same type but not registered in SpecialComparator???? \n{elem1}\n VS \n{elem2}")
                return Misalignment((elem1.position, elem2.position), elem1, elem2, ReportErrorType.UNKNOWN_ERROR)
