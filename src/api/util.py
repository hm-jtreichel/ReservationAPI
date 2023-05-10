"""
A module containing helper functions used in the API-endpoints.
"""

from typing import List, TypeVar, Type

from fastapi import HTTPException, status
from pydantic import BaseModel as PydanticBase
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase

from ..db.manager import SessionFacade

T = TypeVar('T')

session = SessionFacade()


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


def validate_ids_in_put_request(elements_to_update: List[PydanticBase],
                                data_model: Type[DeclarativeBase]) -> List[PydanticBase]:

    ids_to_update = [element_to_update.id for element_to_update in elements_to_update]

    multiple_ids = get_multiple_elements_in_list(ids_to_update)
    if multiple_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The following IDs have been provided multiple times: "
                                   f"[{', '.join(map(str, multiple_ids))}]")

    qry = select(data_model.id).where(data_model.id.in_(ids_to_update))
    updatable_ids = session.scalars(qry).all()

    not_existing_ids = set(ids_to_update) - set(updatable_ids)
    if not_existing_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There are no {data_model.__name__.lower()}s for the given IDs: "
                                   f"[{', '.join(map(str, not_existing_ids))}]")

    return elements_to_update
