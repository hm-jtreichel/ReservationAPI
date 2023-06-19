"""
Module containing routes for Owner-related API endpoints.
"""

from typing import List, Annotated

from fastapi import APIRouter, status, Depends, Path, HTTPException, Body
from sqlalchemy import select

from ...db.manager import SessionFacade
from .ownerModels import Owner as PydanticOwner, \
    OwnerQuery as PydanticOwnerQuery, \
    OwnerNew as PydanticOwnerNew, \
    OwnerModel
from ..restaurants.restaurantModels import Restaurant as PydanticRestaurant, \
    RestaurantNew as PydanticRestaurantNew, \
    RestaurantModel
from ..authentication.authenticationUtils import get_current_owner

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
            summary="Get your own owner information",
            response_description="Owner object of the logged in owner.",
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"},
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_owners(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
               owner_query: PydanticOwnerQuery = Depends()) -> List[PydanticOwner]:
    """
    Returns a list of all Owners that match the given query parameters.
    \f
    Parameters:
    -----------
    current_owner : Annotated[OwnerModel, Depends(get_current_owner)]
        The Owner matching the given authentication token.
    owner_query : PydanticOwnerQuery, optional
        The query parameters used to filter the returned list of Owners.

    Raises:
    -------
    HTTPException
        Raised if there are no owners that match the specified query parameters or the user is not authenticated.

    Returns:
    --------
    List[PydanticOwner]
        A list of PydanticOwner objects matching the provided query parameters.

    """
    qry = select(OwnerModel).where(OwnerModel.id == current_owner.id)
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

    owners = [PydanticOwner.cast_from_model(owner_model) for owner_model in owner_models]

    return owners


@router.put('/',
            summary="Update owner information for logged in owner",
            response_description="The updated owner",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request"},
                status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"}
            })
def update_owner(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                 owner_to_update: PydanticOwnerNew = Body(description="The owner object you want to update")
                 ) -> PydanticOwner:
    """
    Update an owner with a specified ID in the database.
    \f
    Args:
        current_owner : Annotated[OwnerModel, Depends(get_current_owner)]
            The Owner matching the given authentication token.
        owner_to_update (PydanticOwnerNew): The owner object to update.

    Returns:
       PydanticOwner: The updated owner object.

    Raises:
       HTTPException: If the owner ID is invalid or if the owner object in the request-body does not match the ID
       in the path-parameter or the user is not authenticated.
    """
    owner_to_update = owner_to_update.cast_to_put(current_owner.id)

    owner_model = owner_to_update.cast_to_model()

    session.merge(owner_model)
    session.commit()

    updated_owner = PydanticOwner.cast_from_model(owner_model)

    return updated_owner


@router.delete('/',
               summary="Delete owner (own account)",
               response_description="The deleted owner",
               responses={
                   status.HTTP_400_BAD_REQUEST: {"description": "Invalid request"},
                   status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"}
               })
def delete_owner(current_owner: Annotated[OwnerModel, Depends(get_current_owner)]) -> PydanticOwner:
    """
    Delete an owner with a specified ID.
    \f
    Args:
        current_owner : Annotated[OwnerModel, Depends(get_current_owner)]
            The Owner matching the given authentication token.
    Returns:
        PydanticOwner: The deleted owner object.
    Raises:
       HTTPException: If the user is not authenticated.
    """
    qry = select(OwnerModel).where(OwnerModel.id == current_owner.id)
    owner: OwnerModel = session.scalars(qry).first()

    session.delete(owner)
    session.commit()

    deleted_owner = PydanticOwner.cast_from_model(owner)

    return deleted_owner


@router.post('/restaurants',
             summary="Create one or multiple restaurants",
             response_description="The created restaurants",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"},
                 status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"}
             },
             tags=['restaurants'])
def create_restaurants(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                       new_restaurants: List[PydanticRestaurantNew] = Body(
                           description="The restaurants you want to create")
                       ) -> List[PydanticRestaurant]:
    """
    Creates one or multiple restaurants with the provided data.
    \f
    Args:
        current_owner : Annotated[OwnerModel, Depends(get_current_owner)]
            The Owner matching the given authentication token.
        new_restaurants: The list of restaurants you want to create.

    Returns:
        The list of the created restaurants.

    Raises:
        HTTPException: If the request-body is invalid or the user is not authenticated.

    """
    if not new_restaurants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (restaurant-)objects present in the list request-body")

    restaurant_models = [new_restaurant.cast_to_model(current_owner.id) for new_restaurant in new_restaurants]
    for restaurant_model in restaurant_models:
        restaurant_model.owner_id = current_owner.id

    session.add_all(restaurant_models)
    session.commit()

    added_restaurants = [PydanticRestaurant.cast_from_model(restaurant_model) for restaurant_model in restaurant_models]

    return added_restaurants


@router.post('/restaurants/{restaurant_id}',
             summary="Create a new restaurant with a specified ID.",
             response_description="The created restaurant",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"},
                 status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"},
             },
             tags=['restaurants'])
def create_restaurant(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                      restaurant_id: int = Path(description="The ID of the restaurant you want to create", gt=0),
                      new_restaurant: PydanticRestaurantNew = Body(description="The restaurant you want to create")
                      ) -> PydanticRestaurant:
    """
    Creates a single restaurant with the provided data and a specified ID.
    \f
    Args:
        current_owner : Annotated[OwnerModel, Depends(get_current_owner)]
            The Owner matching the given authentication token.
        restaurant_id: The ID of the restaurant you want to create. Must be greater than 0.
        new_restaurant: The restaurant you want to create.

    Returns:
        The created restaurant.

    Raises:
        HTTPException: If the owner with the given ID does not exist or the given ID for restaurant is not available
        or the user is not authenticated.

    """
    qry = select(RestaurantModel).where(RestaurantModel.id == restaurant_id)
    existing_restaurant: RestaurantModel = session.scalars(qry).first()
    if existing_restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Restaurant-ID <{restaurant_id}> is not available. Please choose another one.")

    restaurant_model = new_restaurant.cast_to_model(current_owner.id)
    restaurant_model.id = restaurant_id

    session.add(restaurant_model)
    session.commit()

    added_restaurant = PydanticRestaurant.cast_from_model(restaurant_model)

    return added_restaurant
