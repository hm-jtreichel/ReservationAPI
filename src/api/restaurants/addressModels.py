"""
This module defines the `Address` class which represents the address of a restaurant.
"""

from __future__ import annotations

from pydantic import BaseModel as PydanticBase, Extra
from ...db.models import Address as AddressModel


class Address(PydanticBase):
    """
        Represents the address of a restaurant.
    """
    street_name: str
    house_number: str
    postal_code: int
    city: str
    country_code: str

    class Config:
        schema_extra = {
            "example": {
                "street_name": "Musterstraße",
                "house_number": "1A",
                "postal_code": 12345,
                "city": "Musterstadt",
                "country_code": "DE"
            }
        }
        extra = Extra.forbid

    @staticmethod
    def cast_to_model(address: Address) -> AddressModel:
        """
        Casts an `Address` object to a `AddressModel` object.

        Args:
            address (Address): The `Address` object to be cast.

        Returns:
            AddressModel: The corresponding `AddressModel` object.
        """
        address_model = AddressModel(
            street_name=address.street_name,
            house_number=address.house_number,
            postal_code=address.postal_code,
            city=address.city,
            country_code=address.country_code
        )
        return address_model

    @staticmethod
    def cast_from_model(address_model: AddressModel) -> Address:
        """
        Casts an `AddressModel` object to an `Address` object.

        Args:
            address_model (AddressModel): The `AddressModel` object to be cast.

        Returns:
            Address: The corresponding `Address` object.
        """
        address = Address(
            street_name=address_model.street_name,
            house_number=address_model.house_number,
            postal_code=address_model.postal_code,
            city=address_model.city,
            country_code=address_model.country_code
        )
        return address
