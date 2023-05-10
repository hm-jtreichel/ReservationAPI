from typing import List, Union

from fastapi import APIRouter, status, Depends, Path, HTTPException, Body
from sqlalchemy import select

from ..util import validate_ids_in_put_request
from ...db.manager import SessionFacade
from .tableModels import Table as PydanticTable,\
    TableNew as PydanticTableNew, \
    TableQuery as PydanticTableQuery, \
    TablePut as PydanticTablePut, \
    TableModel

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

    tables = list(map(PydanticTable.cast_from_model, table_models))

    return tables


@router.get('/{table_id}',
            summary="Get table with a specified ID",
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
    table_model = session.scalars(qry).first()

    if not table_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"An table with the given id <{table_id}> does not exist")

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
        HTTPException: If the request-body is empty or if one or more table objects in the list has an invalid ID.

    """
    if not tables_to_update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No (table-)objects present in the list request-body")

    validate_ids_in_put_request(tables_to_update, TableModel)

    table_models = list(map(PydanticTablePut.cast_to_model, tables_to_update))
    session.merge_all(table_models)
    session.commit()

    updated_tables = list(map(PydanticTable.cast_from_model, table_models))

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
                                                                                               "update.")) \
        -> PydanticTable:
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

    Summary:
    Update a single table by ID.

    Response Description:
    The updated table.

    Responses:
    HTTP 400 Bad Request: If the request is invalid, e.g. the ID is not available.
    """
    if type(table_to_update) == PydanticTablePut:
        if table_id != table_to_update.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"The path-parameter ID <{table_id}> doesn't match the "
                                       f"ID <{table_to_update.id}> of the table object in the request-body")

    qry = select(TableModel).where(TableModel.id == table_id)
    table_model = session.scalars(qry).first()

    if not table_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no table for the given ID <{table_id}>")

    if type(table_to_update) == PydanticTableNew:
        table_to_update = PydanticTableNew.cast_to_put(table_to_update, table_id)

    table_model = PydanticTablePut.cast_to_model(table_to_update)

    session.merge(table_model)
    session.commit()

    updated_table = PydanticTable.cast_from_model(table_model)

    return updated_table


@router.delete('/',
               summary="Delete all tables in the database",
               response_description="The deleted tables")
def delete_tables() -> List[PydanticTable]:
    """
    Delete all tables in the database.
    \f
    Returns:
        List[PydanticTable]: The deleted tables.
    """
    qry = select(TableModel)
    tables = session.scalars(qry).all()

    session.delete_all(tables)
    session.commit()

    deleted_tables = list(map(PydanticTable.cast_from_model, tables))

    return deleted_tables


@router.delete('/{table_id}',
               summary="Delete a single table with a given ID in the database",
               response_description="The deleted table",
               responses={
                   status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. ID not available)"}
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
    table = session.scalars(qry).first()

    if not table:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The table with the given ID <{table_id}> does not exist")

    session.delete(table)
    session.commit()

    return PydanticTable.cast_from_model(table)


# TODO
@router.post('/{table_id}/reservations')
def create_reservations():
    pass


# TODO
@router.post('/{table_id}/reservations/{reservation_id}')
def create_reservation():
    pass

