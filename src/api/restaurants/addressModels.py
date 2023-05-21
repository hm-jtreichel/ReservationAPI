"""
This module defines the `Address` class which represents the address of a restaurant.
"""

from __future__ import annotations

from pydantic import BaseModel as PydanticBase, Extra, Field, root_validator

from ...db.models import Address as AddressModel
from ..util import is_valid_country_code


class Address(PydanticBase):
    """
        Represents the address of a restaurant.
    """
    street_name: str
    house_number: str
    postal_code: int = Field(gt=0)
    city: str
    country_code: str = Field(regex="^[A-Z]{2}$")  # Regex: Exactly two upper-case letters.

    @root_validator(skip_on_failure=True)
    def validate_country_code(cls, values):
        if not is_valid_country_code(values['country_code']):
            raise ValueError(f"<{values['country_code']}> is an invalid country-code!")
        return values

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

    def cast_to_model(self) -> AddressModel:
        """
        Casts an `Address` object to a `AddressModel` object.

        Returns:
            AddressModel: The corresponding `AddressModel` object.
        """
        address_model = AddressModel(
            street_name=self.street_name,
            house_number=self.house_number,
            postal_code=self.postal_code,
            city=self.city,
            country_code=self.country_code
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
