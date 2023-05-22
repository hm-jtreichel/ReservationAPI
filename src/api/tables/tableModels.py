"""
This module defines Pydantic models for representing table-related data.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel as PydanticBase, Field, Extra, root_validator
from fastapi import Query
from sqlalchemy import select

from ...util import format_description_with_example
from ...db.manager import SessionFacade
from ...db.models import Table as TableModel

session = SessionFacade()


class TableNew(PydanticBase):
    """
    Represents a new table to be created.
    """
    name: str
    seats: int = Field(gt=0)
    min_guests_required_for_reservation: int = Field(gt=0)

    @root_validator(skip_on_failure=True)
    def validate_seats(cls, values):
        if values['min_guests_required_for_reservation'] > values['seats']:
            raise ValueError("Min-guests-required-for-reservation must be greater than seats.")
        return values

    class Config:
        schema_extra = {
            "example": {
                "name": "Stammtisch",
                "seats": 4,
                "min_guests_required_for_reservation": 2,
            }
        }
        extra = Extra.forbid

    def cast_to_model(self, restaurant_id: int) -> TableModel:
        """
        Convert a new table object to a SQLAlchemy model object.

        Args:
            restaurant_id (int): The ID of the restaurant to which the new table belongs.

        Returns:
            TableModel: The SQLAlchemy model object created from the new table object.
        """
        table_model = TableModel(
            name=self.name,
            seats=self.seats,
            min_guests_required_for_reservation=self.min_guests_required_for_reservation,
            restaurant_id=restaurant_id
        )
        return table_model

    def cast_to_put(self, table_id: int) -> TablePut:
        """
        Creates a new `TablePut` instance using the data from a `TableNew` instance and a table ID.

        Args:
            table_id (int): The ID of the table to be updated (primary key).

        Returns:
            TablePut: A new `TablePut` instance with the same table data as the `TableNew` instance.
        """
        table_put = TablePut(
            id=table_id,
            name=self.name,
            seats=self.seats,
            min_guests_required_for_reservation=self.min_guests_required_for_reservation
        )
        return table_put


class Table(PydanticBase):
    """
    Represents a table.
    """
    id: int
    name: str
    seats: int
    min_guests_required_for_reservation: int

    restaurant_id: int

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Stammtisch",
                "seats": 4,
                "min_guests_required_for_reservation": 2,
                "restaurant_id": 1
            }
        }
        extra = Extra.forbid

    @staticmethod
    def cast_from_model(table_model: TableModel) -> Table:
        """
        Convert a SQLAlchemy model object to a table object.

        Args:
            table_model (TableModel): The SQLAlchemy model object to be converted.

        Returns:
            Table: The table object created from the SQLAlchemy model object.
        """
        table = Table(
            id=table_model.id,
            name=table_model.name,
            seats=table_model.seats,
            min_guests_required_for_reservation=table_model.min_guests_required_for_reservation,
            restaurant_id=table_model.restaurant_id
        )
        return table


class TablePut(PydanticBase):
    """
    Represents a table to be updated.
    """
    id: int = Field(gt=0)
    name: str
    seats: int = Field(gt=0)
    min_guests_required_for_reservation: int = Field(gt=0)

    @root_validator(skip_on_failure=True)
    def validate_seats(cls, values):
        if values['min_guests_required_for_reservation'] > values['seats']:
            raise ValueError("Min-guests-required-for-reservation must be greater than seats.")
        return values

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Stammtisch",
                "seats": 2,
                "min_guests_required_for_reservation": 1,
            }
        }
        extra = Extra.forbid

    def cast_to_model(self) -> TableModel:
        """
        Convert a table update object to a SQLAlchemy model object.

        Returns:
            TableModel: The SQLAlchemy model object created from the table update object.
        """
        get_existing_table_model_qry = select(TableModel).where(TableModel.id == self.id)
        table_model = session.scalars(get_existing_table_model_qry).first()
        # Update existing model
        table_model.name = self.name
        table_model.seats = self.seats
        table_model.min_guests_required_for_reservation = self.min_guests_required_for_reservation
        return table_model


class TableQuery(PydanticBase):
    """
    Represents a set of query parameters used to search for tables in the system.
    \f
    Attributes:
        name (Optional[str]): The name of the table(s) you are looking for.
        restaurant_id (Optional[int]): The restaurant ID of the table(s) you are looking for.
        seats (Optional[int]): The total amount of the seats of the table(s) you are looking for.
        min_seats (Optional[int]): Get the tables that have at least the specified amount of seats.
        max_seats (Optional[int]): Get the tables that have at most the specified amount of seats.
    """
    name: Optional[str] = Field(Query(None,
                                      description=format_description_with_example("Get all tables with the given name.",
                                                                                  "Stammtisch")))
    restaurant_id: Optional[int] = Field(Query(None,
                                               description=format_description_with_example(
                                                   "Get all tables in a restaurant with the given ID.", 1)))
    seats: Optional[int] = Field(Query(None,
                                       description=format_description_with_example(
                                           "Get all tables with an exact amount of seats.", 4)))
    min_seats: Optional[int] = Field(Query(None,
                                           description=format_description_with_example(
                                               "Get all tables with at least the given amount of seats.", 2)))
    max_seats: Optional[int] = Field(Query(None,
                                           description=format_description_with_example(
                                               "Get all tables with at most the given amount of seats.", 6)))
