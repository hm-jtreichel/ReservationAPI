"""
Module containing Pydantic models used for representing
and validating Owner data in API requests and responses.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel as PydanticBase, Field, Extra
from fastapi import Query

from ...db.models import Owner as OwnerModel


class OwnerNew(PydanticBase):
    """
    Pydantic model representing a new owner to be created.
    """
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "first_name": "Max",
                "last_name": "Muster",
                "email": "mustermax@mail.com",
                "phone": "+49-123-123-45678"
            }
        }
        extra = Extra.forbid

    @staticmethod
    def cast_to_model(owner_base: OwnerNew) -> OwnerModel:
        """
        Converts a PydanticOwnerNew instance to an OwnerModel instance.

        Parameters:
        -----------
        owner_base : OwnerNew
            The PydanticOwnerNew instance to convert.

        Returns:
        --------
        OwnerModel
            The converted OwnerModel instance.
        """
        owner_model = OwnerModel(
            first_name=owner_base.first_name,
            last_name=owner_base.last_name,
            email=owner_base.email,
            phone=owner_base.phone
        )
        return owner_model


class Owner(PydanticBase):
    """
    Pydantic model representing an Owner instance.
    """
    id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "first_name": "Max",
                "last_name": "Muster",
                "email": "mustermax@mail.com",
                "phone": "+49-123-123-45678"
            }
        }
        extra = Extra.forbid

    @staticmethod
    def cast_from_model(owner_model: OwnerModel) -> Owner:
        """
        Casts an OwnerModel instance to a PydanticOwner instance.

        Parameters:
        -----------
        owner_model : OwnerModel
            The OwnerModel instance to cast.

        Returns:
        --------
        PydanticOwner
            The cast PydanticOwner instance.
        """
        owner = Owner(
            id=owner_model.id,
            first_name=owner_model.first_name,
            last_name=owner_model.last_name,
            email=owner_model.email,
            phone=owner_model.phone
        )
        return owner

    @staticmethod
    def cast_to_model(owner: Owner) -> OwnerModel:
        """
        Converts a PydanticOwner instance to an OwnerModel instance.

        Parameters:
        -----------
        owner : Owner
            The PydanticOwner instance to convert.

        Returns:
        --------
        OwnerModel
            The converted OwnerModel instance.
        """
        owner_model = OwnerModel(
            id=owner.id,
            first_name=owner.first_name,
            last_name=owner.last_name,
            email=owner.email,
            phone=owner.phone
        )
        return owner_model


class OwnerQuery(PydanticBase):
    """
    Pydantic model representing query-parameters for Owners.
    \f
    Attributes:
    -----------
    first_name : Optional[str]
        The first name of the Owner(s).
    last_name : Optional[str]
        The last name of the Owner(s).
    email : Optional[str]
        The email address of the Owner(s).
    phone : Optional[str]
        The phone number of the Owner(s).
    """
    first_name: Optional[str] = Field(Query(None, description="The first name of the owner(s) you are looking for."))
    last_name: Optional[str] = Field(Query(None, description="The last name of the owner(s) you are looking for."))
    email: Optional[str] = Field(Query(None, description="The email address of the owner(s) you are looking for."))
    phone: Optional[str] = Field(Query(None, description="The phone number of the owner(s) you are looking for."))