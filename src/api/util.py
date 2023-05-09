"""
A module containing helper functions used in the API-endpoints.
"""

from typing import List, TypeVar


T = TypeVar('T')


def get_multiple_elements_in_list(elements: List[T]) -> List[T]:
    """
    Returns a list of all elements that occur more than once in the input list.

    Parameters:
    -----------
    elements (List[T]):
        A list of elements.

    Returns:
    --------
    List[T]:
        A list of all elements that occur more than once in the input list.
        If there are no duplicate elements, an empty list is returned.
    """
    if len(set(elements)) == len(elements):
        return []

    element_occurrence_count = {}
    for element in elements:
        element_occurrence_count[element] = element_occurrence_count.get(element, 0) + 1

    multiple_elements = [element for element, count in element_occurrence_count.items() if count >= 2]
    return multiple_elements
