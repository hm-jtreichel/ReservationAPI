from typing import List, Union, Annotated

from fastapi import APIRouter, status, Depends, Path, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from ...util import validate_ids_in_put_request
from ...db.manager import SessionFacade
from .reservationModels import Reservation as PydanticReservation, \
    ReservationNew as PydanticReservationNew, \
    ReservationQuery as PydanticReservationQuery, \
    ReservationPut as PydanticReservationPut, \
    ReservationModel
from ..tables.tableModels import TableModel
from ..owners.ownerModels import OwnerModel
from ..restaurants.restaurantModels import RestaurantModel
from ..authentication.authenticationUtils import get_current_owner

router = APIRouter(
    prefix="/reservations",
    tags=["reservations"],
    dependencies=[],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Data or endpoint not found"}
    }
)

session = SessionFacade()


@router.get('/',
            summary="Get a list of reservations (optionally matching provided query parameters)",
            response_description="The list of reservations matching the provided query parameters",
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"},
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_reservations(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                     reservation_query: PydanticReservationQuery = Depends()) -> List[PydanticReservation]:
    """
    Gets a list of reservations matching the provided query parameters.
    \f
    Args:
        current_owner (Annotated[OwnerModel, Depends(get_current_owner)]):
            The Owner matching the given authentication token.
        reservation_query (PydanticReservationQuery): An object containing the query parameters.

    Returns:
        List[PydanticReservation]: A list of reservation objects matching the provided query parameters.

    Raises:
        HTTPException: If no reservations match the provided query parameters.
    """
    qry = select(ReservationModel).join(TableModel, ReservationModel.table)\
        .join(RestaurantModel).where(RestaurantModel.owner_id == current_owner.id)

    if reservation_query.restaurant_id:
        qry = qry.where(TableModel.restaurant_id == reservation_query.restaurant_id)
    if reservation_query.table_id:
        qry = qry.where(ReservationModel.table_id == reservation_query.table_id)
    if reservation_query.customer_name:
        qry = qry.where(ReservationModel.customer_name == reservation_query.customer_name)
    if reservation_query.customer_email:
        qry = qry.where(ReservationModel.customer_email == reservation_query.customer_email)
    if reservation_query.customer_phone:
        qry = qry.where(ReservationModel.customer_phone == reservation_query.customer_phone)
    if reservation_query.starting_after:
        qry = qry.where(ReservationModel.reserved_from >= reservation_query.starting_after)
    if reservation_query.starting_at:
        qry = qry.where(ReservationModel.reserved_from == reservation_query.starting_at)
    if reservation_query.ending_before:
        qry = qry.where(ReservationModel.reserved_until <= reservation_query.ending_before)
    if reservation_query.ending_at:
        qry = qry.where(ReservationModel.reserved_until == reservation_query.ending_at)
    if reservation_query.guest_amount:
        qry = qry.where(ReservationModel.guest_amount == reservation_query.guest_amount)
    if reservation_query.min_guest_amount:
        qry = qry.where(ReservationModel.guest_amount >= reservation_query.min_guest_amount)
    if reservation_query.max_guest_amount:
        qry = qry.where(ReservationModel.guest_amount <= reservation_query.max_guest_amount)

    reservation_models = session.scalars(qry).all()
    if not reservation_models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Reservations for your specified query parameters do not exist")

    reservations = [PydanticReservation.cast_from_model(reservation_model) for reservation_model in reservation_models]

    return reservations


@router.get('/{reservation_id}',
            summary="Get a single reservation with a specified ID",
            response_description="The reservation with the specified ID",
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"},
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_reservation(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                    reservation_id: int = Path(description="The ID of the reservation you are looking for", gt=0)
                    ) -> PydanticReservation:
    """
    Gets a single reservation with the specified ID.
    \f
    Args:
        current_owner (Annotated[OwnerModel, Depends(get_current_owner)]):
            The Owner matching the given authentication token.
        reservation_id (int, Path): The ID of the reservation to retrieve.

    Returns:
        PydanticReservation: The reservation object with the specified ID.

    Raises:
        HTTPException: If no reservation exists with the specified ID.
    """
    qry = select(ReservationModel).where(ReservationModel.id == reservation_id).join(TableModel)\
        .join(RestaurantModel).where(RestaurantModel.owner_id == current_owner.id)
    reservation_model: ReservationModel = session.scalars(qry).first()

    if not reservation_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"A reservation with the given ID <{reservation_id}> does not exist")

    reservation = PydanticReservation.cast_from_model(reservation_model)

    return reservation


@router.put('/',
            summary="Updates one or multiple reservations if possible without conflicts",
            response_description="The updated reservations",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"},
                status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"},
                status.HTTP_409_CONFLICT: {"description": "At least one update is not possible"}
            })
def update_reservations(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                        reservations_to_update: List[PydanticReservationPut] = Body(description="The reservation "
                                                                                                "objects you want to "
                                                                                                "update")
                        ) -> List[PydanticReservation]:
    """
    Updates one or multiple tables.
    \f
    Args:
        current_owner (Annotated[OwnerModel, Depends(get_current_owner)]):
            The Owner matching the given authentication token.
        reservations_to_update (List[PydanticReservationPut]): A list of reservation objects to be updated.

    Returns:
        List[PydanticReservation]: The updated reservation objects.

    Raises:
        HTTPException: If the request-body is empty or if one or more reservation objects in the list have an
                       invalid ID.

    """
    if not reservations_to_update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (reservation-)objects present in the list request-body")

    validate_ids_in_put_request(reservations_to_update, ReservationModel, current_owner)

    updated_reservation_models = []
    invalid_reservations = []
    for reservation_to_update in reservations_to_update:
        valid_table_id = reservation_to_update.validate_update()
        if valid_table_id > 0:
            updated_reservation = reservation_to_update.cast_to_model()
            session.merge(updated_reservation)
            session.flush()
            updated_reservation_models.append(updated_reservation)
        else:
            invalid_reservations.append(reservations_to_update)

    if invalid_reservations:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail={
                                "message": "Unable to update all reservations because of conflicts. "
                                           "For additional information you can verify a single reservation at the "
                                           "'tables/{table_id}/validate-reservation'- or "
                                           "'restaurant/{restaurant_id}/validate-reservation'-endpoint.",
                                "invalidReservations": jsonable_encoder(invalid_reservations)
                            })

    session.commit()

    updated_reservations = [PydanticReservation.cast_from_model(updated_reservation_model)
                            for updated_reservation_model in updated_reservation_models]

    return updated_reservations


@router.put('/{reservation_id}',
            summary="Updates a single reservation by ID if possible without conflicts",
            response_description="The updated reservation",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"},
                status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"},
                status.HTTP_409_CONFLICT: {"description": "Update is not possible"}
            })
def update_reservation(
        current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
        reservation_id: int = Path(description="The ID of the reservation to update", gt=0),
        reservation_to_update: Union[PydanticReservationPut, PydanticReservationNew] = Body(
            description="The reservation object you want to update.")
        ) -> PydanticReservation:
    """
    Updates a single reservation by ID.
    \f
    Args:
        current_owner (Annotated[OwnerModel, Depends(get_current_owner)]):
            The Owner matching the given authentication token.
        reservation (int): The ID of the reservation to update. Must be greater than 0.
        reservation_to_update (Union[PydanticReservationPut, PydanticReservationNew]): The reservation object to update.

    Returns:
        PydanticReservation: The updated reservation.

    Raises:
        HTTPException: If there is no reservation for the given ID or if the request is invalid.
    """
    if type(reservation_to_update) == PydanticReservationPut:
        if reservation_id != reservation_to_update.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"The path-parameter ID <{reservation_id}> doesn't match the "
                                       f"ID <{reservation_to_update.id}> of the table object in the request-body")

    qry = select(ReservationModel).where(ReservationModel.id == reservation_id).join(TableModel)\
        .join(RestaurantModel).where(RestaurantModel.owner_id == current_owner.id)
    reservation_model: ReservationModel = session.scalars(qry).first()

    if not reservation_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no reservation for the given ID <{reservation_id}>")

    if type(reservation_to_update) == PydanticReservationNew:
        reservation_to_update = reservation_to_update.cast_to_put(reservation_id)

    valid_table_id = reservation_to_update.validate_update()
    if valid_table_id < 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Unable to update provided reservation because of conflicts. "
                                   "For additional information you can verify a single reservation at the "
                                   "'tables/{table_id}/validate-reservation'- or "
                                   "'restaurant/{restaurant_id}/validate-reservation'-endpoint.")

    reservation_model = reservation_to_update.cast_to_model()

    session.merge(reservation_model)
    session.commit()

    updated_reservation = PydanticReservation.cast_from_model(reservation_model)

    return updated_reservation


@router.delete('/',
               summary="Delete all reservations in the database",
               response_description="The deleted tables",
               responses={
                   status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"},
               })
def delete_reservations(current_owner: Annotated[OwnerModel, Depends(get_current_owner)]) -> List[PydanticReservation]:
    """
    Delete all reservations.
    \f
    Args:
        current_owner (Annotated[OwnerModel, Depends(get_current_owner)]):
            The Owner matching the given authentication token.
    Returns:
        List[PydanticReservation]: The deleted reservations.
    """
    qry = select(ReservationModel).join(TableModel)\
        .join(RestaurantModel).where(RestaurantModel.owner_id == current_owner.id)
    reservations = session.scalars(qry).all()

    session.delete_all(reservations)
    session.commit()

    deleted_reservations = [PydanticReservation.cast_from_model(reservation) for reservation in reservations]

    return deleted_reservations


@router.delete('/{reservation_id}',
               summary="Delete a single reservation with a given ID in the database",
               response_description="The deleted reservation",
               responses={
                   status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not found)"},
                   status.HTTP_401_UNAUTHORIZED: {"description": "User not authorized"}
               })
def delete_reservation(current_owner: Annotated[OwnerModel, Depends(get_current_owner)],
                       reservation_id: int = Path(description="The ID of the reservation to be deleted.", gt=0)
                       ) -> PydanticReservation:
    """
    Delete a single reservation by ID.
    \f
    Args:
        current_owner (Annotated[OwnerModel, Depends(get_current_owner)]):
            The Owner matching the given authentication token.
        reservation_id (int, Path): The ID of the reservation to be deleted.

    Returns:
        PydanticReservation: The deleted reservation.

    Raises:
        HTTPException: If the reservation with the given ID does not exist.
    """
    qry = select(ReservationModel).where(ReservationModel.id == reservation_id).join(TableModel)\
        .join(RestaurantModel).where(RestaurantModel.owner_id == current_owner.id)
    reservation: ReservationModel = session.scalars(qry).first()

    if not reservation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The reservation with the given ID <{reservation_id}> does not exist")

    session.delete(reservation)
    session.commit()

    deleted_reservation = PydanticReservation.cast_from_model(reservation)

    return deleted_reservation
