from .aligner_utils import Content, ReportErrorType
from .content_classes.alignment_issue import AlignmentIssue
from .content_classes.bag import Bag
from .content_classes.dictionary import Dictionary
from .content_classes.misalignment import Misalignment
from .content_classes.ordered_dictionary import OrderedDictionnary
from .content_classes.ordered_seq import OrderedSeq
from .content_classes.string import String
from .special_comparator import SpecialComparator
from typing import Optional, Callable, TypeVar
from nltk import edit_distance

T = TypeVar('T', covariant=True)
U = TypeVar('U', covariant=True)


def group_by(to_be_grouped: list[T] | set[T], key_function: Callable[[T], U]) -> tuple[dict[U, list[T]], list[U]]:
    result = {}
    keys = []
    for elem in to_be_grouped:
        key = key_function(elem)
        if key not in result:
            result[key] = []
            keys.append(key)
        result[key].append(elem)
    return result, keys


class Aligner:
    def __init__(self, alignment_functions: dict[tuple[type, type], Callable[[Content, Content], Content]] = None):
        self.__report_error_dict = alignment_functions
        if alignment_functions is None:
            self.__report_error_dict = {}
        self.__populate_report_error_dict()

    def __populate_report_error_dict(self):
        self.__report_error_dict[(Dictionary, Dictionary)] = self.__align_dict
        self.__report_error_dict[OrderedSeq, OrderedSeq] = self.__align_sequence
        self.__report_error_dict[(OrderedDictionnary, OrderedDictionnary)] = self.__align_ordered_dict
        self.__report_error_dict[(Bag, Bag)] = self.__align_set
        self.__report_error_dict[(String, String)] = self.__align_string

    def align(self, left: Content, right: Content) -> Content:
        """
        This method is used to align two Content trees by comparing them recursively. This method then returns a tree
        of Content with two more Content types: Misalignment and AlignmentIssue.
        Misalignment is used to represent a point where the two trees could not be unified, whereas AlignmentIssue
        warns about some difference but can still continue to compare deeper.
        """
        comparison_function = self.__report_error_dict.get((type(left), type(right)))
        if comparison_function is None:
            comparison_function = self.__report_error_dict.get((type(left), type(right)))
        if comparison_function is None:
            return SpecialComparator.compare_special(left, right, self)
        return comparison_function(left, right)

    @staticmethod
    def find_closest_key(keys: set[str], key: str, allowed_errors: float = 0.2) -> Optional[str]:
        assert 0 <= allowed_errors < 1
        if key == "":
            return None
        length = len(key)
        distances = map(lambda x: (x, edit_distance(x, key)), keys)
        close_distances = list(filter(lambda x: x[1] / length < allowed_errors, distances))
        return min(close_distances, key=lambda x: x[1], default=[None])[0]

    def __align_ordered_dict(self, left: Content, right: Content) -> Content:
        assert isinstance(left, OrderedDictionnary) and isinstance(right, OrderedDictionnary)
        left: OrderedDictionnary
        right: OrderedDictionnary
        current_dic = {}
        ordered_keys = []
        for i in range(max(len(left.entries_list), len(right.entries_list))):
            key_left = left.entries_list[i] if i < len(left.entries_list) else None
            key_right = right.entries_list[i] if i < len(right.entries_list) else None
            if key_left == key_right:
                current_dic[key_left] = self.align(left.entries[key_left], right.entries[key_right])
                ordered_keys.append(key_left)
            else:
                if key_left is not None and key_left in right.entries.keys() and key_left not in ordered_keys:
                    current_dic[key_left] = AlignmentIssue((None, None), self.align(left.entries[key_left],
                                                                                    right.entries[key_left]),
                                                           ReportErrorType.REORDERED_ENTRIES)
                    ordered_keys.append(key_left)
                elif key_left is not None and key_left not in ordered_keys:
                    current_dic[key_left] = Misalignment((None, None), left.entries[key_left], None,
                                                         ReportErrorType.MISSING_ENTRIES)
                    ordered_keys.append(key_left)
                if key_right is not None and key_right in left.entries.keys() and key_right not in ordered_keys:
                    current_dic[key_right] = AlignmentIssue((None, None), self.align(left.entries[key_right],
                                                                                     right.entries[key_right]),
                                                            ReportErrorType.REORDERED_ENTRIES)
                    ordered_keys.append(key_right)
                elif key_right is not None and key_right not in ordered_keys:
                    current_dic[key_right] = Misalignment((None, None), None, right.entries[key_right],
                                                          ReportErrorType.MISSING_ENTRIES)
                    ordered_keys.append(key_right)
        return OrderedDictionnary((left.position, right.position), current_dic, ordered_keys)

    def __align_dict(self, left: Content, right: Content) -> Content:
        assert isinstance(left, Dictionary) and isinstance(right, Dictionary)
        current_dic = {}
        left: Dictionary
        right: Dictionary
        keys_left = list(left.entries.keys())
        keys_right = list(right.entries.keys())
        common_keys = list(filter(lambda x: x in keys_left, keys_right))
        for key in common_keys:
            current_dic[key] = self.align(left.entries[key], right.entries[key])
        remaining_left = list(filter(lambda x: x not in common_keys, keys_left))
        remaining_right = list(filter(lambda x: x not in common_keys, keys_right))
        remaining_keys = remaining_left + list(filter(lambda x: x not in remaining_left, remaining_right))
        used = set()
        for key in remaining_keys:
            if key in used:
                continue
            used.add(key)
            if key in remaining_left:
                keys = filter(lambda x: x not in used and x not in remaining_left, remaining_right)
                match Aligner.find_closest_key(keys, key):
                    case None:
                        current_dic[key] = Misalignment((None, None), left.entries[key], None,
                                                        ReportErrorType.MISSING_ENTRIES)
                    case closest_key:
                        alignment_try = self.align(left.entries[key], right.entries[closest_key])
                        match alignment_try:
                            case Misalignment(_, _, _):
                                current_dic[key] = Misalignment((None, None),
                                                                left.entries[key], None,
                                                                ReportErrorType.MISSING_ENTRIES)
                            case _:
                                used.add(closest_key)
                                current_dic[key] = AlignmentIssue((None, None), alignment_try,
                                                                  ReportErrorType.MISSPELLED_ENTRY)

            elif key in remaining_right:
                keys = filter(lambda x: x not in used and x not in remaining_right, remaining_left)
                match Aligner.find_closest_key(keys, key):
                    case None:
                        current_dic[key] = Misalignment((None, None), None, right.entries[key],
                                                        ReportErrorType.MISSING_ENTRIES)
                    case closest_key:
                        alignment_try = self.align(left.entries[closest_key], right.entries[key])
                        match alignment_try:
                            case Misalignment(_, _, _):
                                current_dic[key] = Misalignment((None, None), None, right.entries[key],
                                                                ReportErrorType.MISSING_ENTRIES)
                            case _:
                                used.add(closest_key)
                                current_dic[key] = AlignmentIssue((None, None), alignment_try,
                                                                  ReportErrorType.MISSPELLED_ENTRY)
        return Dictionary((left.position, right.position), current_dic)

    def __align_sequence(self, left: Content, right: Content) -> Content:
        left: OrderedSeq
        right: OrderedSeq
        if len(left.sequence) == len(right.sequence):
            return OrderedSeq((None, None), list(self.align(left_elem, right_elem)
                                                 for left_elem, right_elem in zip(left.sequence, right.sequence)))
        # How to align elements if some are missing
        # Basically, we assume that there is no reordering, only missing elements
        # This is because there is already a special comparator for unordered sequences
        # We will try to align the smallest sequence with the biggest one
        # Go through every element of the smallest sequence and assume that it is a subset of the bigger list
        smallest = left if len(left.sequence) < len(right.sequence) else right
        biggest = left if smallest is right else right
        i = 0
        unmatched_from_small = []
        result = []
        for smallest_index, element in enumerate(smallest.sequence):
            supposed_to_match = biggest.sequence[i]
            alignment_result = self.align(element, supposed_to_match) if smallest is left else (
                self.align(supposed_to_match, element))
            i += 1
            while isinstance(alignment_result, Misalignment) and i < len(biggest.sequence):
                if smallest is left:
                    result.append(Misalignment((None, None), None, biggest.sequence[i - 1],
                                               ReportErrorType.NOT_SAME_ELEM_IN_SEQ))
                else:
                    result.append(Misalignment((None, None), biggest.sequence[i - 1], None,
                                               ReportErrorType.NOT_SAME_ELEM_IN_SEQ))
                supposed_to_match = biggest.sequence[i]
                alignment_result = self.align(element, supposed_to_match) if smallest is left else (
                    self.align(supposed_to_match, element))
                i += 1
            if isinstance(alignment_result, Misalignment):
                if smallest is left:
                    result.append(Misalignment((None, None), None, biggest.sequence[i - 1],
                                               ReportErrorType.NOT_SAME_ELEM_IN_SEQ))
                else:
                    result.append(Misalignment((None, None), biggest.sequence[i - 1], None,
                                               ReportErrorType.NOT_SAME_ELEM_IN_SEQ))
                unmatched_from_small = [smallest.sequence[x] for x in range(smallest_index, len(smallest.sequence))]
                break
            result.append(alignment_result)
        if smallest is left:
            return OrderedSeq((left.position, right.position), result +
                              [Misalignment((None, None), x, None, ReportErrorType.NOT_SAME_ELEM_IN_SEQ)
                               for x in unmatched_from_small])
        else:
            return OrderedSeq((left.position, right.position), result +
                              [Misalignment((None, None), None, x, ReportErrorType.NOT_SAME_ELEM_IN_SEQ)
                               for x in unmatched_from_small])

    def __align_set(self, left: Content, right: Content) -> Content:
        left: Bag
        right: Bag
        # List is used to keep order but elements are still treated as if it were a set
        constructing_set: list[Content] = []
        elems_left = left.bag
        elems_right = right.bag

        common_elems: list[Content] = []
        for elem_left in elems_left:
            for elem_right in elems_right:
                if elem_left == elem_right:
                    common_elems.append(self.align(elem_left, elem_right))
                    break
        constructing_set += common_elems
        missing_left = list(filter(lambda x: x not in common_elems, elems_right))
        missing_left_grouped_by_type, type_keys_left = group_by(missing_left, type)
        missing_right = list(filter(lambda x: x not in common_elems, elems_left))
        missing_right_grouped_by_type, type_keys_right = group_by(missing_right, type)
        for type_key in type_keys_right:
            if type_key not in type_keys_left:
                type_keys_left.append(type_key)
        for elem in type_keys_left:
            left_elems = missing_left_grouped_by_type.get(elem, [])
            right_elems = missing_right_grouped_by_type.get(elem, [])
            if len(left_elems) == 0:
                constructing_set += [
                    Misalignment((None, None), None, elem, ReportErrorType.MISSING_IN_BAG) for elem in
                    right_elems]
            elif len(right_elems) == 0:
                constructing_set += [
                    Misalignment((None, None), elem, None, ReportErrorType.MISSING_IN_BAG) for elem in
                    left_elems]
            elif len(left_elems) == len(right_elems) == 1:
                subtree = self.align(left_elems[0], right_elems[0])
                match subtree:
                    case Misalignment(_, _, _):
                        constructing_set.append(Misalignment((None, None), left_elems[0], None,
                                                             ReportErrorType.MISSING_IN_BAG))
                        constructing_set.append(
                            Misalignment((None, None), None, right_elems[0],
                                         ReportErrorType.MISSING_IN_BAG))
                    case _:
                        constructing_set.append(AlignmentIssue(subtree, ReportErrorType.MISSPELLED_ENTRY))
            else:
                constructing_set += [
                    Misalignment((None, None), left_elem, None, ReportErrorType.MISSING_IN_BAG)
                    for left_elem in left_elems]
                constructing_set += [
                    Misalignment((None, None), None, right_elem, ReportErrorType.MISSING_IN_BAG)
                    for right_elem in right_elems]
        return Bag((left.position, right.position), constructing_set)

    def __align_string(self, left: Content, right: Content) -> Content:
        left: String
        right: String
        if left != right:
            return Misalignment((None, None), left, right, ReportErrorType.NOT_SAME_STRING)
        return String((left.position, right.position), left.value)
