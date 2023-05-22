"""
This module defines Pydantic models for representing restaurant-related data.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel as PydanticBase, Field, Extra
from fastapi import Query
from sqlalchemy import select

from ...util import format_description_with_example
from ...db.manager import SessionFacade
from ...db.models import Restaurant as RestaurantModel
from .addressModels import Address
from .businessHourModels import BusinessHour

session = SessionFacade()


class RestaurantNew(PydanticBase):
    """
    A Pydantic model for creating a new restaurant
    """
    name: str
    address: Address
    business_hours: List[BusinessHour]

    class Config:
        schema_extra = {
            "example": {
                "name": "Mustermampf",
                "address": Address.Config.schema_extra['example'],
                "business_hours": [BusinessHour.Config.schema_extra['example']]
            }
        }
        extra = Extra.forbid

    def cast_to_model(self, owner_id: int) -> RestaurantModel:
        """
        Converts an instance of `RestaurantNew` to an instance of `RestaurantModel`.

        Args:
            owner_id: The id (primary-key) of the owner of this restaurant (foreign key).

        Returns:
            An instance of `RestaurantModel` converted from the `RestaurantNew` instance.
        """
        restaurant_model = RestaurantModel(
            name=self.name,
            address=self.address.cast_to_model(),
            business_hours=[business_hour.cast_to_model() for business_hour in self.business_hours],
            owner_id=owner_id
        )
        return restaurant_model

    def cast_to_put(self, restaurant_id: int) -> RestaurantPut:
        """
        Converts an instance of `RestaurantNew` to an instance of `RestaurantPut`.

        Args:
            restaurant_id: The id (primary-key) of the restaurant.

        Returns:
            An instance of `RestaurantPut` converted from the `RestaurantNew` instance.
        """
        restaurant_put = RestaurantPut(
            id=restaurant_id,
            name=self.name,
            address=self.address.cast_to_model(),
            business_hours=[business_hour.cast_to_model() for business_hour in self.business_hours]
        )
        return restaurant_put


class Restaurant(PydanticBase):
    """
    A Pydantic model for representing an existing restaurant.
    """
    id: int
    name: str
    owner_id: int
    address: Address
    business_hours: List[BusinessHour]

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Mustermampf",
                "owner_id": 1,
                "address": Address.Config.schema_extra['example'],
                "business_hours": [BusinessHour.Config.schema_extra['example']]
            }
        }
        extra = Extra.forbid

    @staticmethod
    def cast_from_model(restaurant_model: RestaurantModel) -> Restaurant:
        """
        Casts a `RestaurantModel` instance to a `Restaurant` instance.

        Args:
            restaurant_model: The `RestaurantModel` instance to cast.

        Returns:
            Restaurant instance created from the `RestaurantModel` instance.
        """
        restaurant = Restaurant(
            id=restaurant_model.id,
            name=restaurant_model.name,
            owner_id=restaurant_model.owner_id,
            address=Address.cast_from_model(restaurant_model.address),
            business_hours=[BusinessHour.cast_from_model(business_hour_model)
                            for business_hour_model in restaurant_model.business_hours]
        )
        return restaurant


class RestaurantPut(PydanticBase):
    """
    Represents a restaurant that can or will be updated in the system.
    """
    id: int = Field(gt=0)
    name: str
    address: Address
    business_hours: List[BusinessHour]

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Mustermampf",
                "address": Address.Config.schema_extra['example'],
                "business_hours": [BusinessHour.Config.schema_extra['example']]
            }
        }
        extra = Extra.forbid

    def cast_to_model(self) -> RestaurantModel:
        """
        Casts a RestaurantPut instance to a RestaurantModel instance.

        Returns:
            RestaurantModel: The RestaurantModel instance resulting from the cast.

        """
        get_existing_restaurant_model_qry = select(RestaurantModel).where(RestaurantModel.id == self.id)
        restaurant_model = session.scalars(get_existing_restaurant_model_qry).first()
        # Update existing model
        restaurant_model.name = self.name
        restaurant_model.address = self.address.cast_to_model()
        restaurant_model.business_hours = [business_hour.cast_to_model() for business_hour in self.business_hours]
        return restaurant_model


class RestaurantQuery(PydanticBase):
    """
    Represents a set of query parameters used to search for restaurants in the system.
    \f
    Attributes:
        name (Optional[str]): The name of the restaurant(s) to search for.
        owner_id (Optional[str]): The owner ID of the restaurant(s) to search for.
        street_name (Optional[str]): The street name of the restaurant(s) to search for.
        house_number (Optional[str]): The house number of the restaurant(s) to search for.
        postal_code (Optional[str]): The postal code of the restaurant(s) to search for.
        country_code (Optional[str]): The country code of the restaurant(s) to search for.

    """
    name: Optional[str] = Field(Query(None,
                                      description=format_description_with_example(
                                          "Get all restaurants with the given name.", "Mustermampf")))
    owner_id: Optional[int] = Field(Query(None,
                                          description=format_description_with_example(
                                              "Get all restaurants of an owner with the given ID.", 1)))
    street_name: Optional[str] = Field(Query(None,
                                             description=format_description_with_example(
                                                 "Get all restaurants with the given street name.", "Musterstraße")))
    house_number: Optional[str] = Field(Query(None,
                                              description=format_description_with_example(
                                                  "Get all restaurants with the given house number.", "1A")))
    postal_code: Optional[int] = Field(Query(None,
                                             description=format_description_with_example(
                                                 "Get all restaurants with the given postal code.", 12345)))
    country_code: Optional[str] = Field(Query(None,
                                              description=format_description_with_example(
                                                  "Get all restaurants with the given country code.", "DE")))
