from typing import List, Union, Annotated

from fastapi import APIRouter, status, Depends, Path, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from ...util import validate_ids_in_put_request
from ...db.manager import SessionFacade
from .restaurantModels import Restaurant as PydanticRestaurant, \
    RestaurantNew as PydanticRestaurantNew, \
    RestaurantQuery as PydanticRestaurantQuery, \
    RestaurantPut as PydanticRestaurantPut, \
    RestaurantModel
from ..tables.tableModels import Table as PydanticTable, \
    TableNew as PydanticTableNew, \
    TableModel
from ..reservations.reservationModels import Reservation as PydanticReservation, \
    ReservationNew as PydanticReservationNew, \
    ReservationModel, \
    VALIDATION_ERRORS_RESTAURANT
from ..owners.ownerModels import OwnerModel
from ..authentication.authenticationUtils import get_current_owner
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


# TODO: Doctrings!
@router.get('/',
            summary="Get a list of restaurants (optionally matching provided query parameters)",
            response_description="The list of restaurants matching the provided query parameters",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_restaurants(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                    restaurant_query: PydanticRestaurantQuery = Depends()) -> List[PydanticRestaurant]:
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
    qry = select(RestaurantModel).join(AddressModel, RestaurantModel.address)\
        .where(RestaurantModel.owner_id == current_owner.id)
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

    restaurants = [PydanticRestaurant.cast_from_model(restaurant_model) for restaurant_model in restaurant_models]

    return restaurants


@router.get('/{restaurant_id}',
            summary="Get a single restaurant by its ID",
            response_description="The restaurant with the provided ID",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_restaurant(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                   restaurant_id: int = Path(description="The ID of the restaurant you are looking for.", gt=0)
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
    qry = select(RestaurantModel)\
        .where(RestaurantModel.id == restaurant_id)\
        .where(RestaurantModel.owner_id == current_owner.id)
    restaurant: RestaurantModel = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"A restaurant with the given ID <{restaurant_id}> does not exist")

    return PydanticRestaurant.cast_from_model(restaurant)


# TODO: PUT with authentication!!!
@router.put('/',
            summary="Update one or multiple restaurants",
            response_description="The updated restaurants",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"}
            })
def update_restaurants(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                       restaurants_to_update: List[PydanticRestaurantPut] = Body(description="The restaurant objects "
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
        HTTPException: If the request-body is empty or if one or more restaurant objects in the list have an invalid ID.

    """
    if not restaurants_to_update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (restaurant-)objects present in the list request-body")

    validate_ids_in_put_request(restaurants_to_update, RestaurantModel)

    restaurant_models = [restaurant_to_update.cast_to_model() for restaurant_to_update in restaurants_to_update]
    session.merge_all(restaurant_models)
    session.commit()

    updated_restaurants = [PydanticRestaurant.cast_from_model(restaurant_model)
                           for restaurant_model in restaurant_models]

    return updated_restaurants


# TODO: PUT with authentication!!!
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
    restaurant: RestaurantModel = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no restaurant for the given ID <{restaurant_id}>")

    if type(restaurant_to_update) == PydanticRestaurantNew:
        restaurant_to_update = restaurant_to_update.cast_to_put(restaurant_id)

    restaurant_model = restaurant_to_update.cast_to_model()

    session.merge(restaurant_model)
    session.commit()

    updated_restaurant = PydanticRestaurant.cast_from_model(restaurant_model)

    return updated_restaurant


@router.delete('/',
               summary="Delete all restaurants in the database",
               response_description="The deleted restaurants")
def delete_restaurants(current_owner: Annotated[OwnerModel, Depends(get_current_owner)]) -> List[PydanticRestaurant]:
    """
    Delete all restaurants.
    \f
    Returns:
        List[PydanticRestaurant]: The deleted restaurants.
    """
    qry = select(RestaurantModel).where(RestaurantModel.owner_id == current_owner.id)
    restaurants = session.scalars(qry).all()

    session.delete_all(restaurants)
    session.commit()

    deleted_restaurants = [PydanticRestaurant.cast_from_model(restaurant_model) for restaurant_model in restaurants]

    return deleted_restaurants


@router.delete('/{restaurant_id}',
               summary="Delete a single restaurant with a given ID in the database",
               response_description="The deleted restaurant",
               responses={
                   status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not found)"}
               })
def delete_restaurant(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                      restaurant_id: int = Path(description="The ID of the restaurant to be deleted.", gt=0)
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
    qry = select(RestaurantModel)\
        .where(RestaurantModel.id == restaurant_id)\
        .where(RestaurantModel.owner_id == current_owner.id)
    restaurant: RestaurantModel = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{restaurant_id}> does not exist")

    session.delete(restaurant)
    session.commit()

    deleted_restaurant = PydanticRestaurant.cast_from_model(restaurant)

    return deleted_restaurant


@router.post('/{restaurant_id}/tables',
             summary="Create one or multiple tables",
             response_description="The created tables",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"}
             },
             tags=['tables'])
def create_tables_for_restaurant(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                                 restaurant_id: int = Path(description="The ID of the restaurant of the table", gt=0),
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

    qry = select(RestaurantModel)\
        .where(RestaurantModel.id == restaurant_id)\
        .where(RestaurantModel.owner_id == current_owner.id)
    restaurant: RestaurantModel = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{restaurant_id}> does not exist")

    table_models = [table_to_create.cast_to_model(restaurant_id) for table_to_create in tables_to_create]

    session.add_all(table_models)
    session.commit()

    added_tables = [PydanticTable.cast_from_model(table_model) for table_model in table_models]

    return added_tables


@router.post('/{restaurant_id}/tables/{table_id}',
             summary="Create a new table with a specified ID for a restaurant.",
             response_description="The created table",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
             },
             tags=['tables'])
def create_table_for_restaurant(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                                restaurant_id: int = Path(description="The ID of the restaurant of the table", gt=0),
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
    qry = select(RestaurantModel)\
        .where(RestaurantModel.id == restaurant_id)\
        .where(RestaurantModel.owner_id == current_owner.id)
    restaurant: RestaurantModel = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{restaurant_id}> does not exist")

    qry = select(TableModel).where(TableModel.id == table_id)
    existing_table: TableModel = session.scalars(qry).first()

    if existing_table:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Table-ID <{table_id}> is not available. Please choose another one.")

    table_model = table_to_create.cast_to_model(restaurant_id)
    table_model.id = table_id

    session.add(table_model)
    session.commit()

    added_table = PydanticTable.cast_from_model(table_model)

    return added_table


@router.post('/{restaurant_id}/reservations',
             summary="Create one or multiple reservations",
             response_description="The created reservations",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list or reservations "
                                                              "not possible)"},
                 status.HTTP_409_CONFLICT: {"description": "At least one reservation is not possible for the given "
                                                           "restaurant"}
             },
             tags=['reservations'])
def create_reservations_for_restaurant(
        current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
        restaurant_id: int = Path(description="The ID of the restaurant of the reservation", gt=0),
        reservations_to_create: List[PydanticReservationNew] = Body(description="The reservations you want to create "
                                                                                "(sorted by priority descending)")
        ) -> List[PydanticReservation]:
    """
    Create one or multiple reservations for a restaurant and assign them to a valid table
    \f
    Args:
        restaurant_id (int): The ID of the restaurant of the reservation.
        reservations_to_create (List[PydanticReservationNew]): The reservations you want to create
                                                               (sorted by priority descending).

    Returns:
        List[PydanticReservation]: The created reservations.

    Raises:
        HTTPException: If the request-body is invalid (e.g., empty list or reservations not possible) or
                       the restaurant with the given ID does not exist.
    """
    if not reservations_to_create:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (reservation-)objects present in the list request-body")

    qry = select(RestaurantModel)\
        .where(RestaurantModel.id == restaurant_id)\
        .where(RestaurantModel.owner_id == current_owner.id)
    restaurant: RestaurantModel = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{restaurant_id}> does not exist")

    created_reservation_models = []
    invalid_reservations = []
    for reservation_to_create in reservations_to_create:
        valid_table_id = reservation_to_create.validate_for_restaurant(restaurant)
        if valid_table_id > 0:
            created_reservation = reservation_to_create.cast_to_model(valid_table_id)
            session.add(created_reservation)
            session.flush()
            created_reservation_models.append(created_reservation)
        else:
            invalid_reservations.append(reservation_to_create)

    if invalid_reservations:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail={
                                "message": "Unable to find an available table for all provided reservations because "
                                           "of conflicts. Your provided reservations might also overlap. "
                                           "For additional information you can verify a single reservation at the "
                                           "'restaurants/{restaurant_id}/validate-reservation'-endpoint.",
                                "invalidReservations": jsonable_encoder(invalid_reservations)
                            })

    session.commit()

    added_reservations = [PydanticReservation.cast_from_model(created_reservation_model)
                          for created_reservation_model in created_reservation_models]

    return added_reservations


@router.post('/{restaurant_id}/reservations/{reservation_id}',
             summary="Create a new reservation with a specified ID for a restaurant.",
             response_description="The created reservation",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"},
                 status.HTTP_409_CONFLICT: {"description": "Reservation is not possible for the given restaurant"}
             },
             tags=['reservations'])
def create_reservation_for_restaurant(
        current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
        restaurant_id: int = Path(description="The ID of the restaurant of the reservation", gt=0),
        reservation_to_create: PydanticReservationNew = Body(description="The reservation you want to "
                                                                         "create"),
        reservation_id: int = Path(description="The ID of the reservation you want to create", gt=0)
        ) -> PydanticReservation:
    """
    Create a new reservation with a specified ID for a restaurant.
    \f
    Args:
        restaurant_id (int): The ID of the restaurant of the reservation.
        reservation_to_create (PydanticReservationNew): The reservation you want to create.
        reservation_id (int): The ID of the reservation you want to create.

    Returns:
        PydanticReservation: The created reservation.

    Raises:
        HTTPException: If the request is invalid (e.g., ID not available), the restaurant with the given ID does not
                       exist, or an available table cannot be found for the provided reservation.
    """
    qry = select(RestaurantModel)\
        .where(RestaurantModel.id == restaurant_id)\
        .where(RestaurantModel.owner_id == current_owner.id)
    restaurant: RestaurantModel = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{restaurant_id}> does not exist")

    qry = select(ReservationModel).where(ReservationModel.id == reservation_id)
    existing_reservation: ReservationModel = session.scalars(qry).first()

    if existing_reservation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Reservation-ID <{reservation_id}> is not available. Please choose another one.")

    valid_table_id = reservation_to_create.validate_for_restaurant(restaurant)
    if valid_table_id < 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Unable to find an available table for the provided reservation because of "
                                   "conflicts. For additional information you can verify your reservation at the "
                                   "'restaurants/{restaurant_id}/validate-reservation'-endpoint.")

    reservation_model = reservation_to_create.cast_to_model(valid_table_id)
    reservation_model.id = reservation_id

    session.add(reservation_model)
    session.commit()

    added_reservation = PydanticReservation.cast_from_model(reservation_model)

    return added_reservation


@router.post('/{restaurant_id}/validate-reservation',
             summary="Validates a reservation for a restaurant.",
             response_description="An available table of the restaurant for the reservation.",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"},
                 status.HTTP_409_CONFLICT: {"description": "Reservation is not possible for the given restaurant"}
             },
             tags=['reservations'])
def validate_reservation_for_restaurant(
        current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
        restaurant_id: int = Path(description="The ID of the restaurant of the reservation", gt=0),
        reservation_to_validate: PydanticReservationNew = Body(description="The reservation you want to validate"),
        ) -> PydanticTable:
    """
    Validates a reservation for a restaurant.
    \f
    Args:
        restaurant_id (int): The ID of the restaurant for the reservation.
        reservation_to_validate (PydanticReservationNew): The reservation you want to validate.

    Returns:
        PydanticTable: An available table of the restaurant for the reservation.

    Raises:
        HTTPException:
            - status_code 400: If the restaurant with the given ID does not exist.
            - status_code 409: If the reservation is not possible for the given restaurant.
    """
    qry = select(RestaurantModel)\
        .where(RestaurantModel.id == restaurant_id)\
        .where(RestaurantModel.owner_id == current_owner.id)
    restaurant: RestaurantModel = session.scalars(qry).first()

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{restaurant_id}> does not exist")

    valid_table_id = reservation_to_validate.validate_for_restaurant(restaurant)
    if valid_table_id < 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=VALIDATION_ERRORS_RESTAURANT[valid_table_id])

    qry = select(TableModel).where(TableModel.id == valid_table_id)
    valid_table_model: TableModel = session.scalars(qry).first()

    valid_table = PydanticTable.cast_from_model(valid_table_model)

    return valid_table
