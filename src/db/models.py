from __future__ import annotations

from typing import List, Optional
from datetime import datetime, time

from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    A declarative base class for SQLAlchemy models.
    """
    pass


class Restaurant(Base):
    """
    A model representing a restaurant.

    Attributes:
        id (int): The unique identifier for the restaurant.
        name (str): The name of the restaurant.
        owner_id (int): The unique identifier of the restaurant owner.
        address_id (int): The unique identifier of the restaurant address.

    Relationships:
        owner (Owner): The owner of the restaurant.
        address (Address): The address of the restaurant.
        business_hours (List[BusinessHour]): The business hours of the restaurant.
        tables (List[Table]): The tables in the restaurant.
    """
    __tablename__ = "restaurant"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    owner_id: Mapped[int] = mapped_column(ForeignKey("owner.id"))

    owner: Mapped[Owner] = relationship(back_populates="restaurants")
    address: Mapped[Address] = relationship(back_populates="restaurant",
                                            cascade="save-update, merge, delete, delete-orphan")
    business_hours: Mapped[List[BusinessHour]] = relationship(back_populates="restaurant",
                                                              cascade="save-update, merge, delete, delete-orphan")
    tables: Mapped[List[Table]] = relationship(back_populates="restaurant")

    def __repr__(self) -> str:
        return f"<Restaurant, id={self.id}, name={self.name}>"


class Owner(Base):
    """
    A model representing the owner of one or more restaurants.

    Attributes:
        id (int): The unique identifier for the owner.
        first_name (str): The first name of the owner.
        last_name (str): The last name of the owner.
        email (str): The email address of the owner.
        phone (Optional[str]): The phone number of the owner (optional).

    Relationships:
        restaurants (List[Restaurant]): The restaurants owned by the owner.
    """
    __tablename__ = "owner"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[str]
    phone: Mapped[Optional[str]]

    restaurants: Mapped[List[Restaurant]] = relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"<Owner, id={self.id}, email={self.email}>"


class Address(Base):
    """
    A model representing the address of a restaurant.

    Attributes:
        id (int): The unique identifier for the address.
        street_name (str): The street name of the address.
        house_number (str): The house number of the address.
        postal_code (int): The postal code of the address.
        city (str): The city of the address.
        country_code (str): The country code of the address.

    Relationships:
        restaurant (Restaurant): The restaurant associated with the address.
    """
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    street_name: Mapped[str]
    house_number: Mapped[str]
    postal_code: Mapped[int]
    city: Mapped[str]
    country_code: Mapped[str]

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))

    restaurant: Mapped[Restaurant] = relationship(back_populates="address")

    def __repr__(self) -> str:
        return f"<Address, id={self.id}, street_name={self.street_name}, " \
               f"house_number={self.house_number}, postal_code={self.postal_code}>"


class BusinessHour(Base):
    """
    A model representing the business hours of a restaurant.

    Attributes:
        id (int): The unique identifier for the business hour.
        weekday (int): The day of the week (0-6, where 0 is Monday) for the business hour.
        open_time (time): The time that the restaurant opens.
        open_for_reservation_until (time): The time until which the restaurant is open for reservations.
        close_time (time): The time that the restaurant closes.
        restaurant_id (int): The unique identifier of the restaurant associated with the business hour.

    Relationships:
        restaurant (Restaurant): The restaurant associated with the business hour.
    """
    __tablename__ = "business_hour"

    # TODO: Check if works with PostgreSQL
    __table_args__ = tuple(
        CheckConstraint("weekday BETWEEN 0 AND 6")
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    weekday: Mapped[int]
    open_time: Mapped[time]
    open_for_reservation_until: Mapped[time]
    close_time: Mapped[time]

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))

    restaurant: Mapped[Restaurant] = relationship(back_populates="business_hours")

    def __repr__(self) -> str:
        return f"<BusinessHour, id={self.id}, weekday={self.weekday}, " \
               f"open_time={self.open_time}, close_time={self.close_time}>"


class Table(Base):
    """
    A model representing a table in a restaurant.

    Attributes:
        id (int): The unique identifier for the table.
        name (str): The name of the table.
        seats (int): The number of seats at the table.
        min_seats_required_for_reservation (int): The minimum number of seats required for a reservation at the table.
        restaurant_id (int): The unique identifier of the restaurant associated with the table.

    Relationships:
        restaurant (Restaurant): The restaurant associated with the table.
        reservations (List[Reservation]): The reservations for the table.
    """
    __tablename__ = "table"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    seats: Mapped[int]
    min_seats_required_for_reservation: Mapped[int]

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))

    restaurant: Mapped[Restaurant] = relationship(back_populates="tables")
    reservations: Mapped[List[Reservation]] = relationship(back_populates="table")

    def __repr__(self) -> str:
        return f"<Table, id={self.id}, name={self.name}, seats={self.seats}>"


class Reservation(Base):
    """
    A class representing a reservation made by a customer for a table in a restaurant.

    Attributes:
        id (int): The unique identifier of the reservation.
        customer_name (str): The name of the customer who made the reservation.
        customer_email (str): The email address of the customer who made the reservation.
        reserved_from (datetime): The start time of the reservation.
        reserved_until (datetime): The end time of the reservation.
        guest_amount (int): The number of guests for the reservation.
        customer_phone (Optional[str]): The phone number of the customer who made the reservation (optional).
        additional_information (Optional[str]): Any additional information related to the reservation (optional).
        table_id (int): The ID of the table that the reservation is made for.

    Relationships:
        table (Table): The table that the reservation is made for.
    """
    __tablename__ = "reservation"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str]
    customer_email: Mapped[str]
    reserved_from: Mapped[datetime]
    reserved_until: Mapped[datetime]
    guest_amount: Mapped[int]
    customer_phone: Mapped[Optional[str]]
    additional_information: Mapped[Optional[str]]

    table_id: Mapped[int] = mapped_column(ForeignKey("table.id"))

    table: Mapped[Table] = relationship(back_populates="reservations")

    def __repr__(self) -> str:
        return f"<Reservation, id={self.id}, customer_name={self.customer_name}, " \
               f"customer_email={self.customer_email}, reserved_from={self.reserved_from}, " \
               f"reserved_until={self.reserved_until}, guest_amount={self.guest_amount}>"
