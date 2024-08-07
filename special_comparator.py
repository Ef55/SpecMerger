from comparer_utils import Content, WildCard, GenericReportErrorType, AlignmentNotPossible


class SpecialComparator:
    @staticmethod
    def compare_special(elem1: Content, elem2: Content, aligner) -> Content:
        match (elem1, elem2):
            case (WildCard(), _) | (_, WildCard()):
                return AlignmentNotPossible((elem1.position,elem2.position),elem1, elem2, GenericReportErrorType.MATCHED_WILDCARDS)
            case (t1, t2) if type(t1) is not type(t2):
                print(type(t1),type(t2))
                return AlignmentNotPossible((elem1.position,elem2.position),elem1, elem2, GenericReportErrorType.MISMATCHED_TYPES)
            case _:
                print(
                    f"[WARNING!!!!!] Function is same type but not registered in SpecialComparator???? \n{elem1}\n VS \n{elem2}")
                return AlignmentNotPossible((elem1.position,elem2.position),elem1, elem2, GenericReportErrorType.UNKNOWN_ERROR)
