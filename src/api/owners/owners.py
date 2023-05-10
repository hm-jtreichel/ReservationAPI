"""
Module containing routes for Owner-related API endpoints.
"""

from typing import List, Union

from fastapi import APIRouter, status, Depends, Path, HTTPException, Body
from sqlalchemy import select

from ..util import validate_ids_in_put_request
from ...db.manager import SessionFacade
from .ownerModels import Owner as PydanticOwner, \
    OwnerQuery as PydanticOwnerQuery, \
    OwnerNew as PydanticOwnerNew, \
    OwnerPut as PydanticOwnerPut, \
    OwnerModel
from ..restaurants.restaurantModels import Restaurant as PydanticRestaurant, \
    RestaurantNew as PydanticRestaurantNew, \
    RestaurantModel

router = APIRouter(
    prefix="/owners",
    tags=["owners"],
    dependencies=[],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Data or endpoint not found"}
    }
)

session = SessionFacade()


@router.get("/",
            summary="Get a list of owners (optionally matching provided query parameters)",
            response_description="The list of owners matching the provided query parameters",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_owners(owner_query: PydanticOwnerQuery = Depends()) -> List[PydanticOwner]:
    """
    Returns a list of all Owners that match the given query parameters.
    \f
    Parameters:
    -----------
    owner_query : PydanticOwnerQuery, optional
        The query parameters used to filter the returned list of Owners.

    Raises:
    -------
    HTTPException
        Raised if there are no owners that match the specified query parameters.

    Returns:
    --------
    List[PydanticOwner]
        A list of PydanticOwner objects matching the provided query parameters.

    """
    qry = select(OwnerModel)
    if owner_query.first_name:
        qry = qry.where(OwnerModel.first_name == owner_query.first_name)
    if owner_query.last_name:
        qry = qry.where(OwnerModel.last_name == owner_query.last_name)
    if owner_query.email:
        qry = qry.where(OwnerModel.email == owner_query.email)
    if owner_query.phone:
        qry = qry.where(OwnerModel.phone == owner_query.phone)

    owner_models = session.scalars(qry).all()
    if not owner_models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Owners for your specified query parameters do not exist")

    owners = list(map(PydanticOwner.cast_from_model, owner_models))

    return owners


@router.get("/{owner_id}",
            summary="Get owner with a specified ID",
            response_description="The owner with the specified ID",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_owner(owner_id: int = Path(description="The ID of the owner you are looking for", gt=0)
              ) -> PydanticOwner:
    """
    Fetch a single owner based on their ID.
    \f
    Parameters:
    -----------
    owner_id : int
        The ID of the owner to fetch.

    Raises:
    -------
    HTTPException
        Raised if no owner with the provided ID is found.

    Returns:
    --------
    PydanticOwner
        A PydanticOwner object representing the owner with the given ID.

    """
    qry = select(OwnerModel).where(OwnerModel.id == owner_id)

    owner_model = session.scalars(qry).first()
    if not owner_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"An owner with the given id <{owner_id}> does not exist")

    owner = PydanticOwner.cast_from_model(owner_model)
    return owner


@router.post('/',
             summary="Create one or multiple owners",
             response_description="The created owners",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"}
             })
def create_owners(new_owners: List[PydanticOwnerNew] = Body(description="The owner objects you want to create")
                  ) -> List[PydanticOwner]:
    """
    Create one or multiple owners.
    \f
    Parameters:
    -----------
    new_owners : List[PydanticOwnerNew]
        A list of PydanticOwnerNew objects to create.

    Raises:
    -------
    HTTPException
        Raised if the request body is empty or malformed.

    Returns:
    --------
    List[PydanticOwner]
        A list of PydanticOwner objects representing the newly created owners.
    """
    if not new_owners:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (owner-)objects present in the list request-body")

    owner_models = list(map(PydanticOwnerNew.cast_to_model, new_owners))
    session.add_all(owner_models)
    session.commit()
    # Owners now have an ID set on the database.

    added_owners = list(map(PydanticOwner.cast_from_model, owner_models))

    return added_owners


@router.post('/{owner_id}',
             summary="Create a new owner with a specified ID",
             response_description="The created owner",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
             })
def create_owner(owner_id: int = Path(description="The ID of the new owner", gt=0),
                 new_owner: PydanticOwnerNew = Body(description="The owner objects you want to create")
                 ) -> PydanticOwner:
    """
    Create a new owner with a specified ID.
    \f
    Parameters:
    -----------
    owner_id : int
        The ID of the new owner.
    new_owner : PydanticOwnerNew
        The PydanticOwnerNew object to use as a template for the new owner.

    Raises:
    -------
    HTTPException
        Raised if the specified owner ID is not available or if the request body is empty or malformed.

    Returns:
    --------
    PydanticOwner
        A PydanticOwner object representing the newly created owner.
    """
    look_for_owner_qry = select(OwnerModel).where(OwnerModel.id == owner_id)
    existing_owner = session.scalars(look_for_owner_qry).first()
    if existing_owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Owner-ID <{owner_id}> is not available. Please choose another one.")

    owner_model = PydanticOwnerNew.cast_to_model(new_owner)
    owner_model.id = owner_id

    session.add(owner_model)
    session.commit()

    added_owner = PydanticOwner.cast_from_model(owner_model)

    return added_owner


@router.put('/',
            summary="Update one or multiple owners",
            response_description="The updated owners",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"}
            })
def update_owners(owners_to_update: List[PydanticOwnerPut] = Body(description="The owner objects you want to update")
                  ) -> List[PydanticOwner]:
    """
    Update one or multiple owners in the database.
    \f
    Args:
        owners_to_update (List[PydanticOwner]): A list of owner objects to update.

    Returns:
        List[PydanticOwner]: A list of updated owner objects.

    Raises:
        HTTPException: If the request-body is empty or if there are invalid IDs in the request-body.
    """
    if not owners_to_update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (owner-)objects present in the list request-body")

    validate_ids_in_put_request(owners_to_update, OwnerModel)

    owner_models = list(map(PydanticOwnerPut.cast_to_model, owners_to_update))
    session.merge_all(owner_models)
    session.commit()

    updated_owners = list(map(PydanticOwner.cast_from_model, owner_models))

    return updated_owners


@router.put('/{owner_id}',
            summary="Update an owner with a specified ID",
            response_description="The updated owner",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
            })
def update_owner(owner_id: int = Path(description="The ID of the owner to update", gt=0),
                 owner_to_update: Union[PydanticOwnerPut, PydanticOwnerNew] = Body(description="The owner object you "
                                                                                               "want to update")
                 ) -> PydanticOwner:
    """
    Update an owner with a specified ID in the database.
    \f
    Args:
       owner_id (int): The ID of the owner to update.
       owner_to_update (Union[PydanticOwner, PydanticOwnerNew]): The owner object to update.

    Returns:
       PydanticOwner: The updated owner object.

    Raises:
       HTTPException: If the owner ID is invalid or if the owner object in the request-body does not match the ID
       in the path-parameter.
    """
    if type(owner_to_update) == PydanticOwnerPut:
        if owner_id != owner_to_update.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"The path-parameter ID <{owner_id}> doesn't match the "
                                       f"ID <{owner_to_update.id}> of the owner object in the request-body")

    qry = select(OwnerModel).where(OwnerModel.id == owner_id)
    owner = session.scalars(qry).first()

    if not owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no owner for the given ID <{owner_id}>")

    if type(owner_to_update) == PydanticOwnerNew:
        owner_to_update = PydanticOwnerNew.cast_to_put(owner_to_update, owner_id)

    owner_model = PydanticOwnerPut.cast_to_model(owner_to_update)

    session.merge(owner_model)
    session.commit()

    updated_owner = PydanticOwner.cast_from_model(owner_model)

    return updated_owner


@router.delete('/',
               summary="Delete all owners in the database",
               response_description="The deleted owners")
def delete_owners() -> List[PydanticOwner]:
    """
    Delete all owners in the database.
    \f
    Returns:
        List[PydanticOwner]: A list of deleted owner objects.
    """
    qry = select(OwnerModel)
    existing_owners = session.scalars(qry).all()

    session.delete_all(existing_owners)
    session.commit()

    deleted_owners = list(map(PydanticOwner.cast_from_model, existing_owners))

    return deleted_owners


@router.delete('/{owner_id}',
               summary="Delete an owner with a specified ID",
               response_description="The deleted owner",
               responses={
                   status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
               })
def delete_owner(owner_id: int = Path(description="The ID of the owner to delete", gt=0)) -> PydanticOwner:
    """
    Delete an owner with a specified ID from the database.
    \f
    Args:
        owner_id (int): The ID of the owner to delete.

    Returns:
        PydanticOwner: The deleted owner object.

    Raises:
        HTTPException: If the owner ID is invalid.
    """
    qry = select(OwnerModel).where(OwnerModel.id == owner_id)
    owner = session.scalars(qry).first()

    if not owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The owner with the given ID <{owner_id}> does not exist")

    session.delete(owner)
    session.commit()

    deleted_owner = PydanticOwner.cast_from_model(owner)

    return deleted_owner


@router.post('/{owner_id}/restaurants',
             summary="Create one or multiple restaurants",
             response_description="The created restaurants",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"}
             },
             tags=['restaurants'])
def create_restaurants(owner_id: int = Path(description="The ID of the owner of the restaurants", gt=0),
                       new_restaurants: List[PydanticRestaurantNew] = Body(
                           description="The restaurants you want to create")
                       ) -> List[PydanticRestaurant]:
    """
    Creates one or multiple restaurants with the provided data.
    \f
    Args:
        owner_id: The ID of the owner of the restaurants. Must be greater than 0.
        new_restaurants: The list of restaurants you want to create.

    Returns:
        The list of the created restaurants.

    Raises:
        HTTPException: If the request-body is invalid or the owner with the given ID does not exist.

    """
    if not new_restaurants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (restaurant-)objects present in the list request-body")

    qry = select(OwnerModel).where(OwnerModel.id == owner_id)
    owner = session.scalars(qry).first()

    if not owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The owner with the given ID <{owner_id}> does not exist")

    restaurant_models = list(map(
        lambda new_restaurant: PydanticRestaurantNew.cast_to_model(new_restaurant, owner_id), new_restaurants
    ))
    for restaurant_model in restaurant_models:
        restaurant_model.owner_id = owner_id

    session.add_all(restaurant_models)
    session.commit()

    added_restaurants = list(map(PydanticRestaurant.cast_from_model, restaurant_models))

    return added_restaurants


@router.post('/{owner_id}/restaurants/{restaurant_id}',
             summary="Create a new restaurant with a specified ID for an owner.",
             response_description="The created restaurant",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
             },
             tags=['restaurants'])
def create_restaurant(owner_id: int = Path(description="The ID of the owner of the restaurants", gt=0),
                      restaurant_id: int = Path(description="The ID of the restaurant you want to create", gt=0),
                      new_restaurant: PydanticRestaurantNew = Body(description="The restaurant you want to create")
                      ) -> PydanticRestaurant:
    """
    Creates a single restaurant with the provided data and a specified ID.
    \f
    Args:
        owner_id: The ID of the owner of the restaurants. Must be greater than 0.
        restaurant_id: The ID of the restaurant you want to create. Must be greater than 0.
        new_restaurant: The restaurant you want to create.

    Returns:
        The created restaurant.

    Raises:
        HTTPException: If the owner with the given ID does not exist or the given ID for restaurant is not available.

    """
    qry = select(OwnerModel).where(OwnerModel.id == owner_id)
    owner = session.scalars(qry).first()

    if not owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The owner with the given ID <{owner_id}> does not exist")

    qry = select(RestaurantModel).where(RestaurantModel.id == restaurant_id)
    existing_restaurant = session.scalars(qry).first()
    if existing_restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Restaurant-ID <{restaurant_id}> is not available. Please choose another one.")

    restaurant_model = PydanticRestaurantNew.cast_to_model(new_restaurant, owner_id)
    restaurant_model.id = restaurant_id

    session.add(restaurant_model)
    session.commit()

    added_restaurant = PydanticRestaurant.cast_from_model(restaurant_model)

    return added_restaurant
