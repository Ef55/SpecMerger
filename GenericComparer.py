from comparer_utils import String, OrderedSeq, Content, Bag, Dictionnary, GenericReportErrorType, AlignmentNotPossible, \
    AlignmentError, OrderedDictionnary
from special_comparator import SpecialComparator
from utils import GenericParsedPage, GenericParser
from typing import Optional, Callable, TypeVar
import nltk

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


class ComparisonNotFoundException(Exception):
    pass


class Aligner:
    def __init__(self, alignment_functions: dict[tuple[type, type], Callable[[Content, Content], Content]] = None):
        self.report_error_dict = alignment_functions
        if alignment_functions is None:
            self.report_error_dict = {}
        self.populate_report_error_dict()

    def populate_report_error_dict(self):
        self.report_error_dict[(Dictionnary, Dictionnary)] = self.align_dict
        self.report_error_dict[OrderedSeq, OrderedSeq] = self.align_sequence
        self.report_error_dict[(OrderedDictionnary, OrderedDictionnary)] = self.align_ordered_dict
        self.report_error_dict[(Bag, Bag)] = self.align_set
        self.report_error_dict[(String, String)] = self.align_string

    def align(self, left: Content, right: Content) -> Content:
        comparison_function = self.report_error_dict.get((type(left), type(right)))
        if comparison_function is None:
            return SpecialComparator.compare_special(left, right, self)
        return comparison_function(left, right)

    @staticmethod
    def find_closest_key(keys: set[str], key: str, allowed_errors: float = 0.2) -> Optional[str]:
        assert 0 <= allowed_errors < 1
        if key == "":
            return None
        length = len(key)
        distances = map(lambda x: (x, nltk.edit_distance(x, key)), keys)
        close_distances = list(filter(lambda x: x[1] / length < allowed_errors, distances))
        return min(close_distances, key=lambda x: x[1], default=[None])[0]

    def align_ordered_dict(self, left: Content, right: Content) -> Content:
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
                    current_dic[key_left] = AlignmentError((None, None), self.align(left.entries[key_left],
                                                                                    right.entries[key_left]),
                                                           GenericReportErrorType.REORDERED_ENTRIES)
                    ordered_keys.append(key_left)
                elif key_left is not None and key_left not in ordered_keys:
                    current_dic[key_left] = AlignmentNotPossible((None, None), left.entries[key_left], None,
                                                                 GenericReportErrorType.MISSING_ENTRIES)
                    ordered_keys.append(key_left)
                if key_right is not None and key_right in left.entries.keys() and key_right not in ordered_keys:
                    current_dic[key_right] = AlignmentError((None, None), self.align(left.entries[key_right],
                                                                                     right.entries[key_right]),
                                                            GenericReportErrorType.REORDERED_ENTRIES)
                    ordered_keys.append(key_right)
                elif key_right is not None and key_right not in ordered_keys:
                    current_dic[key_right] = AlignmentNotPossible((None, None), None, right.entries[key_right],
                                                                  GenericReportErrorType.MISSING_ENTRIES)
                    ordered_keys.append(key_right)
        return OrderedDictionnary((left.position, right.position), current_dic, ordered_keys)

    def align_dict(self, left: Content, right: Content) -> Content:
        assert isinstance(left, Dictionnary) and isinstance(right, Dictionnary)
        current_dic = {}
        left: Dictionnary
        right: Dictionnary
        keys_left = list(left.entries.keys())
        keys_right = list(right.entries.keys())
        common_keys = list(filter(lambda x: x in keys_left, keys_right))
        for key in common_keys:
            current_dic[key] = self.align(left.entries[key], right.entries[key])
        if "22.2.1" in common_keys:
            print("DEBUG")
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
                        current_dic[key] = AlignmentNotPossible((None, None), left.entries[key], None,
                                                                GenericReportErrorType.MISSING_ENTRIES)
                    case closest_key:
                        alignment_try = self.align(left.entries[key], right.entries[closest_key])
                        match alignment_try:
                            case AlignmentNotPossible(_, _, _):
                                current_dic[key] = AlignmentNotPossible((None, None),
                                                                        left.entries[key], None,
                                                                        GenericReportErrorType.MISSING_ENTRIES)
                            case _:
                                used.add(closest_key)
                                current_dic[key] = AlignmentError((None, None), alignment_try,
                                                                  GenericReportErrorType.MISSPELLED_ENTRY)

            elif key in remaining_right:
                keys = filter(lambda x: x not in used and x not in remaining_right,remaining_left)
                match Aligner.find_closest_key(keys, key):
                    case None:
                        current_dic[key] = AlignmentNotPossible((None, None), None, right.entries[key],
                                                                GenericReportErrorType.MISSING_ENTRIES)
                    case closest_key:
                        alignment_try = self.align(left.entries[closest_key], right.entries[key])
                        match alignment_try:
                            case AlignmentNotPossible(_, _, _):
                                current_dic[key] = AlignmentNotPossible((None, None), None, right.entries[key],
                                                                        GenericReportErrorType.MISSING_ENTRIES)
                            case _:
                                used.add(closest_key)
                                current_dic[key] = AlignmentError((None, None), alignment_try,
                                                                  GenericReportErrorType.MISSPELLED_ENTRY)
        return Dictionnary((left.position, right.position), current_dic)

    def align_sequence(self, left: Content, right: Content) -> Content:
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
            while isinstance(alignment_result, AlignmentNotPossible) and i < len(biggest.sequence):
                if smallest is left:
                    result.append(AlignmentNotPossible((None, None), None, biggest.sequence[i - 1],
                                                       GenericReportErrorType.NOT_SAME_ELEM_IN_SEQ))
                else:
                    result.append(AlignmentNotPossible((None, None), biggest.sequence[i - 1], None,
                                                       GenericReportErrorType.NOT_SAME_ELEM_IN_SEQ))
                supposed_to_match = biggest.sequence[i]
                alignment_result = self.align(element, supposed_to_match) if smallest is left else (
                    self.align(supposed_to_match, element))
                i += 1
            if isinstance(alignment_result, AlignmentNotPossible):
                if smallest is left:
                    result.append(AlignmentNotPossible((None, None), None, biggest.sequence[i - 1],
                                                       GenericReportErrorType.NOT_SAME_ELEM_IN_SEQ))
                else:
                    result.append(AlignmentNotPossible((None, None), biggest.sequence[i - 1], None,
                                                       GenericReportErrorType.NOT_SAME_ELEM_IN_SEQ))
                unmatched_from_small = [smallest.sequence[x] for x in range(smallest_index, len(smallest.sequence))]
                break
            result.append(alignment_result)
        if smallest is left:
            return OrderedSeq((left.position, right.position), result +
                              [AlignmentNotPossible((None, None), x, None, GenericReportErrorType.NOT_SAME_ELEM_IN_SEQ)
                               for x in unmatched_from_small])
        else:
            return OrderedSeq((left.position, right.position), result +
                              [AlignmentNotPossible((None, None), None, x, GenericReportErrorType.NOT_SAME_ELEM_IN_SEQ)
                               for x in unmatched_from_small])

    def align_set(self, left: Content, right: Content) -> Content:
        left: Bag
        right: Bag
        # List is used to keep order but elements are still treated as if it were a set
        constructing_set: list[Content] = []
        elems_left = left.bag
        elems_right = right.bag

        common_elems: set[Content] = set()
        for elem_left in elems_left:
            for elem_right in elems_right:
                if elem_left == elem_right:
                    common_elems.add(self.align(elem_left, elem_right))
                    break
        constructing_set += common_elems
        missing_left = list(filter(lambda x: x in common_elems, elems_right))
        missing_left_grouped_by_type, type_keys_left = group_by(missing_left, type)
        missing_right = list(filter(lambda x: x in common_elems, elems_left))
        missing_right_grouped_by_type, type_keys_right = group_by(missing_right, type)
        for type_key in type_keys_right:
            if type_key not in type_keys_left:
                type_keys_left.append(type_key)
        for elem in type_keys_left:
            left_elems = missing_left_grouped_by_type.get(elem, [])
            right_elems = missing_right_grouped_by_type.get(elem, [])
            if len(left_elems) == 0:
                constructing_set += [
                    AlignmentNotPossible((None, None), None, elem, GenericReportErrorType.MISSING_IN_BAG) for elem in
                    right_elems]
            elif len(right_elems) == 0:
                constructing_set += [
                    AlignmentNotPossible((None, None), elem, None, GenericReportErrorType.MISSING_IN_BAG) for elem in
                    left_elems]
            elif len(left_elems) == len(right_elems) == 1:
                subtree = self.align(left_elems[0], right_elems[0])
                match subtree:
                    case AlignmentNotPossible(_, _, _):
                        constructing_set.append(AlignmentNotPossible((None, None), left_elems[0], None,
                                                                     GenericReportErrorType.MISSING_IN_BAG))
                        constructing_set.append(
                            AlignmentNotPossible((None, None), None, right_elems[0],
                                                 GenericReportErrorType.MISSING_IN_BAG))
                    case _:
                        constructing_set.append(AlignmentError(subtree, GenericReportErrorType.MISSPELLED_ENTRY))
            else:
                constructing_set += [
                    AlignmentNotPossible((None, None), left_elem, None, GenericReportErrorType.MISSING_IN_BAG)
                    for left_elem in left_elems]
                constructing_set += [
                    AlignmentNotPossible((None, None), None, right_elem, GenericReportErrorType.MISSING_IN_BAG)
                    for right_elem in right_elems]
        return Bag((left.position, right.position), constructing_set)

    def align_string(self, left: Content, right: Content) -> Content:
        left: String
        right: String
        if left != right:
            return AlignmentNotPossible((None, None), left, right, GenericReportErrorType.NOT_SAME_STRING)
        return String((left.position, right.position), left.value)
