from typing import List, Union

from fastapi import APIRouter, status, Depends, Path, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from ..util import validate_ids_in_put_request
from ...db.manager import SessionFacade
from .tableModels import Table as PydanticTable, \
    TableNew as PydanticTableNew, \
    TableQuery as PydanticTableQuery, \
    TablePut as PydanticTablePut, \
    TableModel
from ..reservations.reservationModels import Reservation as PydanticReservation, \
    ReservationNew as PydanticReservationNew, \
    ReservationModel, \
    VALIDATION_ERRORS_TABLE

router = APIRouter(
    prefix="/tables",
    tags=["tables"],
    dependencies=[],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Data or endpoint not found"}
    }
)

session = SessionFacade()


@router.get('/',
            summary="Get a list of tables (optionally matching provided query parameters)",
            response_description="The list of tables matching the provided query parameters",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_tables(table_query: PydanticTableQuery = Depends()) -> List[PydanticTable]:
    """
    Get a list of tables matching the provided query parameters.
    \f
    Args:
        table_query: A PydanticTableQuery instance containing query parameters for filtering the tables.

    Returns:
        A list of PydanticTable instances representing the tables matching the provided query parameters.

    Raises:
        HTTPException: If no tables matching the provided query parameters are found.

    """
    qry = select(TableModel)

    if table_query.name:
        qry = qry.where(TableModel.name == table_query.name)
    if table_query.restaurant_id:
        qry = qry.where(TableModel.restaurant_id == table_query.restaurant_id)
    if table_query.seats:
        qry = qry.where(TableModel.seats == table_query.seats)
    if table_query.min_seats:
        qry = qry.where(TableModel.seats >= table_query.min_seats)
    if table_query.max_seats:
        qry = qry.where(TableModel.seats <= table_query.max_seats)

    table_models = session.scalars(qry).all()
    if not table_models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Tables for your specified query parameters do not exist")

    tables = [PydanticTable.cast_from_model(table_model) for table_model in table_models]

    return tables


@router.get('/{table_id}',
            summary="Get a single table with a specified ID",
            response_description="The table with the specified ID",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "No results for request found"}
            })
def get_table(table_id: int = Path(description="The ID of the table you are looking for", gt=0)) -> PydanticTable:
    """
    Get a table with a specified ID.
    \f
    Args:
        table_id: An integer representing the ID of the table to retrieve.

    Returns:
        A PydanticTable instance representing the table with the specified ID.

    Raises:
        HTTPException: If a table with the specified ID does not exist.

    """
    qry = select(TableModel).where(TableModel.id == table_id)
    table_model: TableModel = session.scalars(qry).first()

    if not table_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"A table with the given ID <{table_id}> does not exist")

    table = PydanticTable.cast_from_model(table_model)

    return table


@router.put('/',
            summary="Update one or multiple tables",
            response_description="The updated tables",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list)"}
            })
def update_tables(tables_to_update: List[PydanticTablePut] = Body(description="The table objects "
                                                                              "you want to update")
                  ) -> List[PydanticTable]:
    """
    Updates one or multiple tables.
    \f
    Args:
        tables_to_update (List[PydanticTablePut]): A list of table objects to be updated.

    Returns:
        List[PydanticTable]: The updated table objects.

    Raises:
        HTTPException: If the request-body is empty or if one or more table objects in the list have an invalid ID.

    """
    if not tables_to_update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (table-)objects present in the list request-body")

    validate_ids_in_put_request(tables_to_update, TableModel)

    table_models = [table_to_update.cast_to_model() for table_to_update in tables_to_update]
    session.merge_all(table_models)
    session.commit()

    updated_tables = [PydanticTable.cast_from_model(table_model) for table_model in table_models]

    return updated_tables


@router.put('/{table_id}',
            summary="Update a single table by ID",
            response_description="The updated table",
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
            })
def update_table(table_id: int = Path(description="The ID of the table to update", gt=0),
                 table_to_update: Union[PydanticTablePut, PydanticTableNew] = Body(description="The table "
                                                                                               "object you want to "
                                                                                               "update.")
                 ) -> PydanticTable:
    """
    Updates a single table by ID.
    \f
    Args:
    table_id (int): The ID of the table to update. Must be greater than 0.
    table_to_update (Union[PydanticTablePut, PydanticTableNew]): The table object to update.

    Returns:
    PydanticTable: The updated table.

    Raises:
    HTTPException: If there is no table for the given ID or if the request is invalid.
    """
    if type(table_to_update) == PydanticTablePut:
        if table_id != table_to_update.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"The path-parameter ID <{table_id}> doesn't match the "
                                       f"ID <{table_to_update.id}> of the table object in the request-body")

    qry = select(TableModel).where(TableModel.id == table_id)
    table_model: TableModel = session.scalars(qry).first()

    if not table_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no table for the given ID <{table_id}>")

    if type(table_to_update) == PydanticTableNew:
        table_to_update = table_to_update.cast_to_put(table_id)

    table_model = table_to_update.cast_to_model()

    session.merge(table_model)
    session.commit()

    updated_table = PydanticTable.cast_from_model(table_model)

    return updated_table


@router.delete('/',
               summary="Delete all tables in the database",
               response_description="The deleted tables")
def delete_tables() -> List[PydanticTable]:
    """
    Delete all tables.
    \f
    Returns:
        List[PydanticTable]: The deleted tables.
    """
    qry = select(TableModel)
    tables = session.scalars(qry).all()

    session.delete_all(tables)
    session.commit()

    deleted_tables = [PydanticTable.cast_from_model(table_model) for table_model in tables]

    return deleted_tables


@router.delete('/{table_id}',
               summary="Delete a single table with a given ID in the database",
               response_description="The deleted table",
               responses={
                   status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not found)"}
               })
def delete_table(table_id: int = Path(description="The ID of the table to be deleted.", gt=0)
                 ) -> PydanticTable:
    """
    Delete a single table by ID.
    \f
    Args:
        table_id (int, Path): The ID of the table to be deleted.

    Returns:
        PydanticTable: The deleted table.

    Raises:
        HTTPException: If the table with the given ID does not exist.
    """
    qry = select(TableModel).where(TableModel.id == table_id)
    table: TableModel = session.scalars(qry).first()

    if not table:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The table with the given ID <{table_id}> does not exist")

    session.delete(table)
    session.commit()

    deleted_table = PydanticTable.cast_from_model(table)

    return deleted_table


@router.post('/{table_id}/reservations',
             summary="Create one or multiple reservations for the given table",
             response_description="The created reservations",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request-body (e.g. empty list or reservations "
                                                              "not possible)"},
                 status.HTTP_409_CONFLICT: {"description": "At least one reservation is not possible for the given "
                                                           "table"}
             },
             tags=['reservations'])
def create_reservations_for_table(
        table_id: int = Path(description="The ID of the table of the reservation", gt=0),
        reservations_to_create: List[PydanticReservationNew] = Body(description="The reservations you want to create "
                                                                                "(sorted by priority descending)")
) -> List[PydanticReservation]:
    """
    Create one or multiple reservations for a given table.
    \f
    Args:
        table_id (int): The ID of the table of the reservation.
        reservations_to_create (List[PydanticReservationNew]): The reservations you want to create
                                                               (sorted by priority descending).

    Returns:
        List[PydanticReservation]: The created reservations.

    Raises:
        HTTPException: If the request-body is invalid (e.g., empty list or reservations not possible) or
                       the table with the given ID does not exist.
        """
    if not reservations_to_create:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (reservation-)objects present in the list request-body")

    qry = select(TableModel).where(TableModel.id == table_id)
    table: TableModel = session.scalars(qry).first()

    if not table:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{table_id}> does not exist")

    created_reservation_models = []
    invalid_reservations = []
    for reservation_to_create in reservations_to_create:
        valid_table_id = reservation_to_create.validate_for_table(table)
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
                                "message": "Unable to fit all reservations on the given table because of conflicts. "
                                           "Your provided reservations might also overlap. "
                                           "For additional information you can verify a single reservation at the "
                                           "'tables/{table_id}/validate-reservation'-endpoint.",
                                "invalidReservations": jsonable_encoder(invalid_reservations)
                            })

    session.commit()

    added_reservations = [PydanticReservation.cast_from_model(created_reservation_model)
                          for created_reservation_model in created_reservation_models]

    return added_reservations


@router.post('/{table_id}/reservations/{reservation_id}',
             summary="Create a new reservation with a specified ID for the given table.",
             response_description="The created reservation",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"},
                 status.HTTP_409_CONFLICT: {"description": "Reservation is not possible for the given table"}
             },
             tags=['reservations'])
def create_reservation_for_table(
        table_id: int = Path(description="The ID of the table of the reservation", gt=0),
        reservation_to_create: PydanticReservationNew = Body(description="The reservation you want to "
                                                                         "create"),
        reservation_id: int = Path(description="The ID of the reservation you want to create", gt=0)
        ) -> PydanticReservation:
    """
    Create a new reservation with a specified ID for a given table.
    \f
    Args:
        table_id (int): The ID of the restaurant of the reservation.
        reservation_to_create (PydanticReservationNew): The reservation you want to create.
        reservation_id (int): The ID of the reservation you want to create.

    Returns:
        PydanticReservation: The created reservation.

    Raises:
        HTTPException: If the request is invalid (e.g., ID not available), the restaurant with the given ID does not
                       exist, or an available table cannot be found for the provided reservation.
    """
    qry = select(TableModel).where(TableModel.id == table_id)
    table: TableModel = session.scalars(qry).first()

    if not table:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The restaurant with the given ID <{table_id}> does not exist")

    qry = select(ReservationModel).where(ReservationModel.id == reservation_id)
    existing_reservation: ReservationModel = session.scalars(qry).first()

    if existing_reservation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Reservation-ID <{reservation_id}> is not available. Please choose another one.")

    valid_table_id = reservation_to_create.validate_for_table(table)
    if valid_table_id < 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Unable to fit the provided reservation on the given table because of conflicts. "
                                   "For additional information you can verify your reservation at the "
                                   "'tables/{table_id}/validate-reservation'-endpoint.")

    reservation_model = reservation_to_create.cast_to_model(valid_table_id)
    reservation_model.id = reservation_id

    session.add(reservation_model)
    session.commit()

    added_reservation = PydanticReservation.cast_from_model(reservation_model)

    return added_reservation


@router.post('/{table_id}/validate-reservation',
             summary="Validates a reservation for a table.",
             response_description="The table for the reservation (if available).",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"},
                 status.HTTP_409_CONFLICT: {"description": "Reservation is not possible for the given table"}
             },
             tags=['reservations'])
def validate_reservation_for_table(
        table_id: int = Path(description="The ID of the table of the reservation", gt=0),
        reservation_to_validate: PydanticReservationNew = Body(description="The reservation you want to validate"),
        ) -> PydanticTable:
    """
    Validates a reservation for a table.
    \f
    Args:
        table_id (int): The ID of the table for the reservation.
        reservation_to_validate (PydanticReservationNew): The reservation you want to validate.

    Returns:
        PydanticTable: The table for the reservation (if available).

    Raises:
        HTTPException:
            - status_code 400: If the table with the given ID does not exist.
            - status_code 409: If the reservation is not possible for the given table.
    """
    qry = select(TableModel).where(TableModel.id == table_id)
    table: TableModel = session.scalars(qry).first()

    if not table:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The table with the given ID <{table_id}> does not exist")

    valid_table_id = reservation_to_validate.validate_for_table(table)
    if valid_table_id < 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=VALIDATION_ERRORS_TABLE[valid_table_id])

    valid_table = PydanticTable.cast_from_model(table)

    return valid_table
