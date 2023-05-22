"""
This module defines Pydantic models for representing reservation-related data.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime

from pydantic import BaseModel as PydanticBase, Field, Extra, root_validator
from fastapi import Query
from sqlalchemy import select, and_, func

from ...util import format_description_with_example
from ...db.manager import SessionFacade
from ...db.models import Reservation as ReservationModel, \
    Restaurant as RestaurantModel, \
    Table as TableModel, \
    BusinessHour as BusinessHourModel

session = SessionFacade()

# Messages explaining the error-codes returned by the validation-methods.
# Used by the /reservations/validate-endpoints in restaurants and tables.
VALIDATION_ERRORS_RESTAURANT = {
    -1: "Reservation is not inside open-to-close timeframe and/or the restaurant does not accept "
        "reservations at the desired time.",
    -2: "There is no table with enough space for all the guests of the given reservation and/or other potential "
        "tables can only be reserved with more guests.",
    -3: "Reservation conflicts with other existing reservations on all potential tables."
}
VALIDATION_ERRORS_TABLE = {
    -1: "Reservation timeframe not inside open-to-close timeframe and/or the restaurant does not accept "
        "reservations at the desired time.",
    -2: "Not enough space for all the guests of the given reservation on the given table and/or the given table "
        "can only be reserved with more guests.",
    -3: "Reservation conflicts with other existing reservations on the table."
}


class ReservationNew(PydanticBase):
    """
    Represents a new reservation to be created.
    """
    customer_name: str
    customer_email: str
    reserved_from: datetime
    reserved_until: datetime
    guest_amount: int = Field(gt=0)
    customer_phone: Optional[str]
    additional_information: Optional[str]

    @root_validator(skip_on_failure=True)
    def validate_times(cls, values):
        if values['reserved_from'] > values['reserved_until']:
            raise ValueError("Reservation can't end before it has started.")
        return values

    class Config:
        schema_extra = {
            "example": {
                "customer_name": "Versuchskaninchen",
                "customer_email": "verena.versuchskaninchen@mail.de",
                "reserved_from": "2023-05-10 17:00:00.00000",
                "reserved_until": "2023-05-10 19:30:00.00000",
                "guest_amount": 5,
                "customer_phone": "+49-176-111-12345",
                "additional_information": "Bitte mit Kinderstuhl!"
            }
        }
        extra = Extra.forbid

    def cast_to_model(self, table_id: int) -> ReservationModel:
        """
        Convert a new reservation object to a SQLAlchemy model object.

        Args:
            table_id (int): The ID of the table to which the new reservation belongs.

        Returns:
            ReservationModel: The SQLAlchemy model object created from the new reservation object.
        """
        reservation_model = ReservationModel(
            customer_name=self.customer_name,
            customer_email=self.customer_email,
            reserved_from=self.reserved_from,
            reserved_until=self.reserved_until,
            guest_amount=self.guest_amount,
            customer_phone=self.customer_phone,
            additional_information=self.additional_information,
            table_id=table_id
        )
        return reservation_model

    def cast_to_put(self, reservation_id: int) -> ReservationPut:
        """
        Creates a new `ReservationPut` instance using the data from a `ReservationNew` instance and a reservation ID.

        Args:
            reservation_id (int): The ID of the reservation to be updated (primary key).

        Returns:
            ReservationPut: A new `ReservationPut` instance with the same reservation data as the `ReservationNew`
            instance.
        """
        reservation_put = ReservationPut(
            id=reservation_id,
            customer_name=self.customer_name,
            customer_email=self.customer_email,
            reserved_from=self.reserved_from,
            reserved_until=self.reserved_until,
            guest_amount=self.guest_amount,
            customer_phone=self.customer_phone,
            additional_information=self.additional_information,
        )
        return reservation_put

    def is_inside_business_hour_timeframe_for_restaurant(self, restaurant: RestaurantModel) -> bool:
        """
        Check if the reservation falls within the business hours of a restaurant.

        Args:
            restaurant (Restaurant): The SQLAlchemy restaurant.

        Returns:
            bool: True if the reservation is inside the business hours, False otherwise.
        """
        # Get business-hour entry for reservation.
        # E.g.: Monday 10-13, Monday 14-18, Reservation Monday 15-16 --> Monday 14-18
        qry = select(BusinessHourModel).where(and_(
            BusinessHourModel.restaurant_id == restaurant.id,
            BusinessHourModel.weekday == self.reserved_from.weekday(),
            BusinessHourModel.close_time >= self.reserved_until.time(),
            BusinessHourModel.open_time <= self.reserved_from.time(),
            BusinessHourModel.open_for_reservation_until >= self.reserved_from.time()
        ))
        business_hour = session.scalars(qry).first()
        return business_hour is not None

    def is_conflicting_with_existing_reservations_of_table(self, table: TableModel) -> bool:
        """
        Check if the reservation conflicts with existing reservations for a specific table.

        Args:
            table (Table): The SQLAlchemy table.

        Returns:
            bool: True if there is a conflict with existing reservations, False otherwise.
        """
        get_same_day_reservations_qry = select(ReservationModel).where(and_(
            ReservationModel.table_id == table.id,
            func.date(ReservationModel.reserved_from) == self.reserved_from.date()
        )).order_by(ReservationModel.reserved_from.asc())
        same_day_reservations = list(session.scalars(get_same_day_reservations_qry).all())

        # Find space of new reservation between same-day-reservations.
        # Add <self> to the list and sort by reserved_from (Pydantic- and SQLAlchemy-model
        # both have this attribute).
        # After that find the index <self> and validate from- and until-time with its
        # neighbours.
        is_conflicting = False
        if same_day_reservations:
            same_day_reservations.append(self)
            same_day_reservations.sort(key=lambda reservation: reservation.reserved_from)
            self_index = same_day_reservations.index(self)
            if self_index == 0:
                is_conflicting = self.reserved_until > same_day_reservations[self_index + 1].reserved_from
            elif self_index == len(same_day_reservations) - 1:
                is_conflicting = self.reserved_from < same_day_reservations[self_index - 1].reserved_until
            else:
                is_conflicting = (self.reserved_until > same_day_reservations[self_index + 1].reserved_from or
                                  self.reserved_from < same_day_reservations[self_index - 1].reserved_until)
        return is_conflicting

    def validate_for_restaurant(self, restaurant: RestaurantModel) -> int:
        """
        Validate the reservation for a specific restaurant.

        Args:
            restaurant (Restaurant): The SQLAlchemy restaurant.

        Returns:
            int: The ID of the valid table if the reservation is valid, or an error code otherwise.
                  -1: Invalid timeframe (not inside open-to-close timeframe or not open for new reservations)
                  -2: No tables available for the required number of guests
                  -3: Reservation conflicts with existing reservations on every potential table
        """
        if not self.is_inside_business_hour_timeframe_for_restaurant(restaurant):
            return -1

        get_potential_tables_qry = select(TableModel).where(and_(
            TableModel.restaurant_id == restaurant.id,
            TableModel.min_guests_required_for_reservation <= self.guest_amount,
            TableModel.seats >= self.guest_amount,
        ))
        potential_tables = session.scalars(get_potential_tables_qry).all()
        if not potential_tables:
            return -2

        potential_tables = [potential_table for potential_table in potential_tables
                            if not self.is_conflicting_with_existing_reservations_of_table(potential_table)]
        if not potential_tables:
            return -3

        # Prioritize tables by sorting the list by specified criteria
        potential_tables.sort(key=lambda potential_table: potential_table.seats - self.guest_amount)

        return potential_tables[0].id

    def validate_for_table(self, table: TableModel) -> int:
        """
        Validate the reservation for a specific table.

        Args:
            table (Table): The SQLAlchemy table.

        Returns:
            int: The ID of the valid table if the reservation is valid, or an error code otherwise.
                  -1: Invalid timeframe (not inside open-to-close timeframe or not open for new reservations)
                  -2: Specified table cannot accommodate all guests
                  -3: Reservation conflicts with existing reservations on the table
        """
        if not self.is_inside_business_hour_timeframe_for_restaurant(table.restaurant):
            return -1

        if (table.min_guests_required_for_reservation > self.guest_amount or
                table.seats < self.guest_amount):
            return -2

        if self.is_conflicting_with_existing_reservations_of_table(table):
            return -3

        return table.id


class Reservation(PydanticBase):
    """
    Represents a reservation.
    """
    id: int
    customer_name: str
    customer_email: str
    reserved_from: datetime
    reserved_until: datetime
    guest_amount: int
    customer_phone: Optional[str]
    additional_information: Optional[str]

    table_id: int

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "customer_name": "Versuchskaninchen",
                "customer_email": "verena.versuchskaninchen@mail.de",
                "reserved_from": "2023-05-10 17:00:00.00000",
                "reserved_until": "2023-05-10 19:30:00.00000",
                "guest_amount": 5,
                "customer_phone": "+49-176-111-12345",
                "additional_information": "Bitte mit Kinderstuhl!",
                "table_id": 1
            }
        }
        extra = Extra.forbid

    @staticmethod
    def cast_from_model(reservation_model: ReservationModel) -> Reservation:
        """
        Convert a SQLAlchemy model object to a reservation object.

        Args:
            reservation_model (ReservationModel): The SQLAlchemy model object to be converted.

        Returns:
            Reservation: The reservation object created from the SQLAlchemy model object.
        """
        reservation = Reservation(
            id=reservation_model.id,
            customer_name=reservation_model.customer_name,
            customer_email=reservation_model.customer_email,
            reserved_from=reservation_model.reserved_from,
            reserved_until=reservation_model.reserved_until,
            guest_amount=reservation_model.guest_amount,
            customer_phone=reservation_model.customer_phone,
            additional_information=reservation_model.additional_information,
            table_id=reservation_model.table_id
        )
        return reservation


class ReservationPut(PydanticBase):
    """
    Represents a reservation to be updated.
    """
    id: int = Field(gt=0)
    customer_name: str
    customer_email: str
    reserved_from: datetime
    reserved_until: datetime
    guest_amount: int = Field(gt=0)
    customer_phone: Optional[str]
    additional_information: Optional[str]

    @root_validator(skip_on_failure=True)
    def validate_times(cls, values):
        if values['reserved_from'] > values['reserved_until']:
            raise ValueError("Reservation can't end before it has started.")
        return values

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "customer_name": "Versuchskaninchen",
                "customer_email": "verena.versuchskaninchen@mail.de",
                "reserved_from": "2023-05-10 17:00:00.00000",
                "reserved_until": "2023-05-10 19:30:00.00000",
                "guest_amount": 5,
                "customer_phone": "+49-176-111-12345",
                "additional_information": "Bitte mit Kinderstuhl!"
            }
        }
        extra = Extra.forbid

    def cast_to_model(self) -> ReservationModel:
        """
        Convert a reservation update object to a SQLAlchemy model object.

        Returns:
            ReservationModel: The SQLAlchemy model object created from the reservation update object.
        """
        get_existing_reservation_model_qry = select(ReservationModel).where(ReservationModel.id == self.id)
        reservation_model = session.scalars(get_existing_reservation_model_qry).first()
        # Update existing model
        reservation_model.customer_name = self.customer_name
        reservation_model.customer_email = self.customer_email
        reservation_model.reserved_from = self.reserved_from
        reservation_model.reserved_until = self.reserved_until
        reservation_model.guest_amount = self.guest_amount
        reservation_model.customer_phone = self.customer_phone
        reservation_model.additional_information = self.additional_information
        return reservation_model

    def cast_to_new(self) -> ReservationNew:
        """
        Convert a ReservationPut object to a ReservationNew object.

        This instance can be used during the validation process for a reservation update.

        Returns:
            ReservationNew: The ReservationNew object created from the ReservationPut object.
        """
        reservation_new = ReservationNew(
            customer_name=self.customer_name,
            customer_email=self.customer_email,
            reserved_from=self.reserved_from,
            reserved_until=self.reserved_until,
            guest_amount=self.guest_amount,
            customer_phone=self.customer_phone,
            additional_information=self.additional_information
        )
        return reservation_new

    def validate_update(self) -> int:
        """
        Validate the reservation update for its table.

        Returns:
            int: The ID of the valid table if the reservation is valid, or an error code otherwise.
                  -1: Invalid timeframe (not inside open-to-close timeframe or not open for new reservations)
                  -2: Specified table cannot accommodate all guests
                  -3: Reservation conflicts with existing reservations on the table
        """
        qry = select(ReservationModel).where(ReservationModel.id == self.id)
        old_reservation_model: ReservationModel = session.scalars(qry).first()
        table_model = old_reservation_model.table

        # Remove the old state of the reservation from the session so
        # validation runs without considering it.
        session.delete(old_reservation_model)
        session.flush()

        reservation_new = self.cast_to_new()
        valid_table_id = reservation_new.validate_for_table(table_model)

        # Add back the old state object to the session as the update will
        # only be validated and not persistent in this method.
        session.make_transient(old_reservation_model)
        session.add(old_reservation_model)
        session.flush()

        return valid_table_id


class ReservationQuery(PydanticBase):
    """
    Represents a set of query parameters used to search for reservations in the system.
    \f
    Attributes:
        restaurant_id (Optional[int]): The ID of the restaurant to search for reservations at.
        table_id (Optional[int]): The ID of the table to search for reservations for.
        customer_name (Optional[str]): The name of the customer to search for reservations for.
        customer_email (Optional[str]): The email of the customer to search for reservations for.
        customer_phone (Optional[str]): The phone number of the customer to search for reservations for.
        starting_after (Optional[datetime]): The earliest time to search for reservations from.
        starting_at (Optional[datetime]): The exact start time to search for reservations for.
        ending_before (Optional[datetime]): The latest time to search for reservations until.
        ending_at (Optional[datetime]): The exact end time to search for reservations for.
        guest_amount (Optional[int]): The exact number of guests to search for reservations for.
        min_guest_amount (Optional[int]): The minimum number of guests to search for reservations for.
        max_guest_amount (Optional[int]): The maximum number of guests to search for reservations for.
    """
    restaurant_id: Optional[int] = Field(Query(None,
                                               description=format_description_with_example(
                                                   "Get all reservations for a restaurant with the given ID.", 1)))
    table_id: Optional[int] = Field(Query(None,
                                          description=format_description_with_example(
                                              "Get all reservations for a table with the given ID.", 1)))
    customer_name: Optional[str] = Field(Query(None,
                                               description=format_description_with_example(
                                                   "Get all reservations for customers with the given name.",
                                                   "Versuchskaninchen")))
    customer_email: Optional[str] = Field(Query(None,
                                                description=format_description_with_example(
                                                    "Get all reservations for customers with the given email.",
                                                    "verena.versuchskaninchen@mail.de")))
    customer_phone: Optional[str] = Field(Query(None,
                                                description=format_description_with_example(
                                                    "Get all reservations for customers with the given phone-number.",
                                                    "+49-176-111-12345")))
    starting_after: Optional[datetime] = Field(Query(None,
                                                     description=format_description_with_example(
                                                         "Get all reservations starting after that time.",
                                                         "2023-05-10 16:30:00.00000")))
    starting_at: Optional[datetime] = Field(Query(None,
                                                  description=format_description_with_example(
                                                      "Get all reservations starting at that exact time.",
                                                      "2023-05-10 17:00:00.00000")))
    ending_before: Optional[datetime] = Field(Query(None,
                                                    description=format_description_with_example(
                                                        "Get all reservations ending before that time.",
                                                        "2023-05-10 20:00:00.00000")))
    ending_at: Optional[datetime] = Field(Query(None,
                                                description=format_description_with_example(
                                                    "Get all reservations ending at that exact time.",
                                                    "2023-05-10 19:30:00.00000")))
    guest_amount: Optional[int] = Field(Query(None,
                                              description=format_description_with_example(
                                                  "Get all reservations with an exact amount of guests.", 5)))
    min_guest_amount: Optional[int] = Field(Query(None,
                                                  description=format_description_with_example(
                                                      "Get all reservations that have at least the amount of guests.",
                                                      3)))
    max_guest_amount: Optional[int] = Field(Query(None,
                                                  description=format_description_with_example(
                                                      "Get all reservations that have at most the "
                                                      "amount of guests.", 7)))
