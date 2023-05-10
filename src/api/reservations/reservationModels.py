"""
This module defines Pydantic models for representing reservation-related data.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime

from pydantic import BaseModel as PydanticBase, Field, Extra
from fastapi import Query
from sqlalchemy import select

from ...db.manager import SessionFacade
from ...db.models import Reservation as ReservationModel

session = SessionFacade()


class ReservationNew(PydanticBase):
    """
    Represents a new reservation to be created.
    """
    customer_name: str
    customer_email: str
    reserved_from: datetime
    reserved_until: datetime
    guest_amount: int
    customer_phone: Optional[str]
    additional_information: Optional[str]

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

    @staticmethod
    def cast_to_model(reservation_new: ReservationNew, table_id: int) -> ReservationModel:
        """
        Convert a new reservation object to a SQLAlchemy model object.

        Args:
            reservation_new (ReservationNew): The new reservation object to be converted.
            table_id (int): The ID of the table to which the new reservation belongs.

        Returns:
            ReservationModel: The SQLAlchemy model object created from the new reservation object.
        """
        reservation_model = ReservationModel(
            customer_name=reservation_new.customer_name,
            customer_email=reservation_new.customer_email,
            reserved_from=reservation_new.reserved_from,
            reserved_until=reservation_new.reserved_until,
            guest_amount=reservation_new.guest_amount,
            customer_phone=reservation_new.customer_phone,
            additional_information=reservation_new.additional_information,
            table_id=table_id
        )
        return reservation_model

    @staticmethod
    def cast_to_put(reservation_new: ReservationNew, reservation_id: int) -> ReservationPut:
        """
        Creates a new `ReservationPut` instance using the data from a `ReservationNew` instance and a reservation ID.

        Args:
            reservation_new (ReservationNew): The `ReservationNew` instance containing the new reservation data.
            reservation_id (int): The ID of the reservation to be updated (primary key).

        Returns:
            ReservationPut: A new `ReservationPut` instance with the same reservation data as the `ReservationNew`
            instance.
        """
        reservation_put = ReservationPut(
            id=reservation_id,
            customer_name=reservation_new.customer_name,
            customer_email=reservation_new.customer_email,
            reserved_from=reservation_new.reserved_from,
            reserved_until=reservation_new.reserved_until,
            guest_amount=reservation_new.guest_amount,
            customer_phone=reservation_new.customer_phone,
            additional_information=reservation_new.additional_information,
        )
        return reservation_put


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
    id: int
    customer_name: str
    customer_email: str
    reserved_from: datetime
    reserved_until: datetime
    guest_amount: int
    customer_phone: Optional[str]
    additional_information: Optional[str]

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

    @staticmethod
    def cast_to_model(reservation_put: ReservationPut) -> ReservationModel:
        """
        Convert a reservation update object to a SQLAlchemy model object.

        Args:
            reservation_put (ReservationPut): The reservation update object to be converted.

        Returns:
            ReservationModel: The SQLAlchemy model object created from the reservation update object.
        """
        get_existing_reservation_model_qry = select(ReservationModel).where(ReservationModel.id == reservation_put.id)
        reservation_model = session.scalars(get_existing_reservation_model_qry).first()
        # Update existing model
        reservation_model.customer_name = reservation_put.customer_name
        reservation_model.customer_email = reservation_put.customer_email
        reservation_model.reserved_from = reservation_put.reserved_from
        reservation_model.reserved_until = reservation_put.reserved_until
        reservation_model.guest_amount = reservation_put.guest_amount
        reservation_model.customer_phone = reservation_put.customer_phone
        reservation_model.additional_information = reservation_put.additional_information
        return reservation_model


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
        starting_from (Optional[datetime]): The earliest time to search for reservations from.
        starting_at (Optional[datetime]): The exact start time to search for reservations for.
        ending_before (Optional[datetime]): The latest time to search for reservations until.
        ending_at (Optional[datetime]): The exact end time to search for reservations for.
        guest_amount (Optional[int]): The exact number of guests to search for reservations for.
        min_guest_amount (Optional[int]): The minimum number of guests to search for reservations for.
        max_guest_amount (Optional[int]): The maximum number of guests to search for reservations for.
    """
    restaurant_id: Optional[int] = Field(Query(None,
                                               description="Get all reservations for a restaurant with the given ID.",
                                               example=1))
    table_id: Optional[int] = Field(Query(None,
                                          description="Get all reservations for a table with the given ID.",
                                          example=1))
    customer_name: Optional[str] = Field(Query(None,
                                               description="Get all reservations for customers with the given name.",
                                               example="Versuchskaninchen"))
    customer_email: Optional[str] = Field(Query(None,
                                                description="Get all reservations for customers with the given email.",
                                                example="verena.versuchskaninchen@mail.de"))
    customer_phone: Optional[str] = Field(Query(None,
                                                description="Get all reservations for customers with the "
                                                            "given phone-number.",
                                                example="+49-176-111-12345"))
    starting_from: Optional[datetime] = Field(Query(None,
                                                    description="Get all reservations starting from that time.",
                                                    example="2023-05-10 16:30:00.00000"))
    starting_at: Optional[datetime] = Field(Query(None,
                                                  description="Get all reservations starting at that exact time.",
                                                  example="2023-05-10 17:00:00.00000"))
    ending_before: Optional[datetime] = Field(Query(None,
                                                    description="Get all reservations ending before that time.",
                                                    example="2023-05-10 20:00:00.00000"))
    ending_at: Optional[datetime] = Field(Query(None,
                                                description="Get all reservations ending at that exact time.",
                                                example="2023-05-10 19:30:00.00000"))
    guest_amount: Optional[int] = Field(Query(None,
                                              description="Get all reservations with an exact amount of guests.",
                                              example=5))
    min_guest_amount: Optional[int] = Field(Query(None,
                                                  description="Get all reservations that have at least the "
                                                              "amount of guests.",
                                                  example=3))
    max_guest_amount: Optional[int] = Field(Query(None,
                                                  description="Get all reservations that have at most the "
                                                              "amount of guests.",
                                                  example=7))
