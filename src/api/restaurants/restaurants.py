from typing import List, Union

from fastapi import APIRouter, status, Depends, Path, HTTPException, Body
from sqlalchemy import select

from ..util import validate_ids_in_put_request
from ...db.manager import SessionFacade
from .restaurantModels import Restaurant as PydanticRestaurant, \
    RestaurantNew as PydanticRestaurantNew, \
    RestaurantQuery as PydanticRestaurantQuery, \
    RestaurantPut as PydanticRestaurantPut, \
    RestaurantModel
from ..tables.tableModels import Table as PydanticTable, \
    TableNew as PydanticTableNew, \
    TableModel
from .addressModels import AddressModel

router = APIRouter(
    prefix="/restaurants",
    tags=["restaurants"],
    dependencies=[],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Data or endpoint not found"}
    }
)

session = SessionFacade()


@router.get('/',
            summary="Get a list of restaurants (optionally matching provided query parameters)",
            response_description="The list of restaurants matching the provided query parameters",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_restaurants(restaurant_query: PydanticRestaurantQuery = Depends()) -> List[PydanticRestaurant]:
    """
    Get a list of restaurants matching the provided query parameters.
    \f
    Args:
        restaurant_query (PydanticRestaurantQuery, optional):
        The query parameters used to filter the list of restaurants.

    Returns:
        List[PydanticRestaurant]:
        A list of PydanticRestaurant objects representing the restaurants that match the provided query parameters.

    Raises:
        HTTPException:
        If no restaurants match the provided query parameters, a HTTPException with a 404 status code is raised.
    """
    qry = select(RestaurantModel).join(AddressModel, RestaurantModel.address)
    if restaurant_query.name:
        qry = qry.where(RestaurantModel.name == restaurant_query.name)
    if restaurant_query.owner_id:
        qry = qry.where(RestaurantModel.owner_id == restaurant_query.owner_id)
    if restaurant_query.street_name:
        qry = qry.where(AddressModel.street_name == restaurant_query.street_name)
    if restaurant_query.house_number:
        qry = qry.where(AddressModel.house_number == restaurant_query.house_number)
    if restaurant_query.postal_code:
        qry = qry.where(AddressModel.postal_code == restaurant_query.postal_code)
    if restaurant_query.country_code:
        qry = qry.where(AddressModel.country_code == restaurant_query.country_code)

    restaurant_models = session.scalars(qry).all()
    if not restaurant_models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Restaurants for your specified query parameters do not exist")

    restaurants = list(map(PydanticRestaurant.cast_from_model, restaurant_models))

    return restaurants


@router.get('/{restaurant_id}',
            summary="Get a single restaurant by its ID",
            response_description="The restaurant with the provided ID",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_restaurant(restaurant_id: int = Path(description="The ID of the restaurant you are looking for.", gt=0)
                   ) -> PydanticRestaurant:
    """
    Retrieve a single restaurant by its ID.
    \f
    Args:
        restaurant_id (int): The ID of the restaurant to retrieve. Must be greater than 0.

    Returns:
        PydanticRestaurant: The restaurant with the provided ID.

    Raises:
        HTTPException: If no restaurant with the provided ID is found.
    """
    qry = select(RestaurantModel).where(RestaurantModel.id == restaurant_id)
    restaurant = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Restaurants with ID <{restaurant_id}> does not exist")

    return PydanticRestaurant.cast_from_model(restaurant)


@router.put('/',
            summary="Update one or multiple restaurants",
            response_description="The updated restaurants",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"}
            })
def update_restaurants(restaurants_to_update: List[PydanticRestaurantPut] = Body(description="The restaurant objects "
                                                                                             "you want to update")
                       ) -> List[PydanticRestaurant]:
    """
    Updates one or multiple restaurants.
    \f
    Args:
        restaurants_to_update (List[PydanticRestaurantPut]): A list of restaurant objects to be updated.

    Returns:
        List[PydanticRestaurant]: The updated restaurant objects.

    Raises:
        HTTPException: If the request-body is empty or if one or more restaurant objects in the list has an invalid ID.

    """
    if not restaurants_to_update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (restaurant-)objects present in the list request-body")

    validate_ids_in_put_request(restaurants_to_update, RestaurantModel)

    restaurant_models = list(map(PydanticRestaurantPut.cast_to_model, restaurants_to_update))
    session.merge_all(restaurant_models)
    session.commit()

    updated_restaurants = list(map(PydanticRestaurant.cast_from_model, restaurant_models))

    return updated_restaurants


@router.put('/{restaurant_id}',
            summary="Update a single restaurant by ID",
            response_description="The updated restaurant",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
            })
def update_restaurant(restaurant_id: int = Path(description="The ID of the restaurant to update", gt=0),
                      restaurant_to_update: Union[PydanticRestaurantPut, PydanticRestaurantNew] =
                      Body(description="The restaurant object you want to update.")
                      ) -> PydanticRestaurant:
    """
    Update a single restaurant by ID.
    \f
    Args:
        restaurant_id (int, Path): The ID of the restaurant to update.
        restaurant_to_update (Union[PydanticRestaurantPut, PydanticRestaurantNew], Body): The restaurant object you
        want to update.

    Returns:
        PydanticRestaurant: The updated restaurant.

    Raises:
        HTTPException: If the ID is not available or if the ID in the request body does not match the path-parameter ID.
    """
    if type(restaurant_to_update) == PydanticRestaurantPut:
        if restaurant_id != restaurant_to_update.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"The path-parameter ID <{restaurant_id}> doesn't match the "
                                       f"ID <{restaurant_to_update.id}> of the restaurant object in the request-body")

    qry = select(RestaurantModel).where(RestaurantModel.id == restaurant_id)
    restaurant = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no restaurant for the given ID <{restaurant_id}>")

    if type(restaurant_to_update) == PydanticRestaurantNew:
        restaurant_to_update = PydanticRestaurantNew.cast_to_put(restaurant_to_update, restaurant_id)

    restaurant_model = PydanticRestaurantPut.cast_to_model(restaurant_to_update)

    session.merge(restaurant_model)
    session.commit()

    updated_restaurant = PydanticRestaurant.cast_from_model(restaurant_model)

    return updated_restaurant


@router.delete('/',
               summary="Delete all restaurants in the database",
               response_description="The deleted restaurants")
def delete_restaurants() -> List[PydanticRestaurant]:
    """
    Delete all restaurants in the database.
    \f
    Returns:
        List[PydanticRestaurant]: The deleted restaurants.
    """
    qry = select(RestaurantModel)
    restaurants = session.scalars(qry).all()

    session.delete_all(restaurants)
    session.commit()

    deleted_restaurants = list(map(PydanticRestaurant.cast_from_model, restaurants))

    return deleted_restaurants


@router.delete('/{restaurant_id}',
               summary="Delete a single restaurant with a given ID in the database",
               response_description="The deleted restaurant",
               responses={
                   status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
               })
def delete_restaurant(restaurant_id: int = Path(description="The ID of the restaurant to be deleted.", gt=0)
                      ) -> PydanticRestaurant:
    """
    Delete a single restaurant by ID.
    \f
    Args:
        restaurant_id (int, Path): The ID of the restaurant to be deleted.

    Returns:
        PydanticRestaurant: The deleted restaurant.

    Raises:
        HTTPException: If the restaurant with the given ID does not exist.
    """
    qry = select(RestaurantModel).where(RestaurantModel.id == restaurant_id)
    restaurant = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{restaurant_id}> does not exist")

    session.delete(restaurant)
    session.commit()

    return PydanticRestaurant.cast_from_model(restaurant)


@router.post('/{restaurant_id}/tables',
             summary="Create one or multiple tables",
             response_description="The created tables",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"}
             },
             tags=['tables'])
def create_tables_for_restaurant(restaurant_id: int = Path(description="The ID of the restaurant of the table", gt=0),
                                 tables_to_create: List[PydanticTableNew]
                                 = Body(description="The tables you want to create")) -> List[PydanticTable]:
    """
    Create one or multiple tables for a restaurant.
    \f
    Args:
        restaurant_id (int, Path): The ID of the restaurant of the table.
        tables_to_create (List[PydanticTableNew], Body): The tables you want to create.

    Returns:
        List[PydanticTable]: The created tables.

    Raises:
        HTTPException: If the list request-body is empty or if the restaurant with the given ID does not exist.
    """
    if not tables_to_create:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (table-)objects present in the list request-body")

    qry = select(RestaurantModel).where(RestaurantModel.id == restaurant_id)
    restaurant = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{restaurant_id}> does not exist")

    table_models = list(map(
        lambda new_table: PydanticTableNew.cast_to_model(new_table, restaurant_id), tables_to_create
    ))

    session.add_all(table_models)
    session.commit()

    added_tables = list(map(PydanticTable.cast_from_model, table_models))

    return added_tables


@router.post('/{restaurant_id}/tables/{table_id}',
             summary="Create a new table with a specified ID for a restaurant.",
             response_description="The created table",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
             },
             tags=['tables'])
def create_table_for_restaurant(restaurant_id: int = Path(description="The ID of the restaurant of the table", gt=0),
                                table_to_create: PydanticTableNew = Body(description="The table you want to create"),
                                table_id: int = Path(description="The ID of the table you want to create", gt=0)
                                ) -> PydanticTable:
    """
    Create a new table with a specified ID for a restaurant.
    \f
    Args:
        restaurant_id (int, Path): The ID of the restaurant of the table.
        table_to_create (PydanticTableNew, Body): The table you want to create.
        table_id (int, Path): The ID of the table you want to create.

    Returns:
        PydanticTable: The created table.

    Raises:
        HTTPException: If the restaurant with the given ID does not exist or if the table ID is not available.
    """
    qry = select(RestaurantModel).where(RestaurantModel.id == restaurant_id)
    restaurant = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{restaurant_id}> does not exist")

    qry = select(TableModel).where(TableModel.id == table_id)
    existing_table = session.scalars(qry).first()

    if existing_table:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Table-ID <{table_id}> is not available. Please choose another one.")

    table_model = PydanticTableNew.cast_to_model(table_to_create, restaurant_id)
    table_model.id = table_id

    session.add(table_model)
    session.commit()

    added_table = PydanticTable.cast_from_model(table_model)

    return added_table
