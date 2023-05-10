"""
Module containing Pydantic models used for representing
and validating Owner data in API requests and responses.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel as PydanticBase, Field, Extra
from fastapi import Query
from sqlalchemy import select

from ...db.manager import SessionFacade
from ...db.models import Owner as OwnerModel

session = SessionFacade()


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
    def cast_to_model(owner: OwnerNew) -> OwnerModel:
        """
        Converts a PydanticOwnerNew instance to an OwnerModel instance.

        Parameters:
        -----------
        owner : OwnerNew
            The PydanticOwnerNew instance to convert.

        Returns:
        --------
        OwnerModel
            The converted OwnerModel instance.
        """
        owner_model = OwnerModel(
            first_name=owner.first_name,
            last_name=owner.last_name,
            email=owner.email,
            phone=owner.phone
        )
        return owner_model

    @staticmethod
    def cast_to_put(owner: OwnerNew, owner_id: int) -> OwnerPut:
        """
        Converts an instance of `OwnerNew` to an instance of `OwnerPut`.

        Args:
            owner: The `OwnerNew` instance to be converted.
            owner_id: The id (primary-key) of the restaurant.

        Returns:
            An instance of `OwnerPut` converted from the `OwnerNew` instance.
        """
        owner_put = OwnerPut(
            id=owner_id,
            first_name=owner.first_name,
            last_name=owner.last_name,
            email=owner.email,
            phone=owner.phone
        )
        return owner_put


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


class OwnerPut(PydanticBase):
    """
    Pydantic model representing an Owner instance to update.
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
    def cast_to_model(owner: OwnerPut) -> OwnerModel:
        """
        Converts a PydanticOwnerPut instance to an OwnerModel instance.

        Parameters:
        -----------
        owner : Owner
            The PydanticOwnerPut instance to convert.

        Returns:
        --------
        OwnerModel
            The converted OwnerModel instance.
        """
        get_existing_owner_model_qry = select(OwnerModel).where(OwnerModel.id == owner.id)
        owner_model = session.scalars(get_existing_owner_model_qry).first()

        owner_model.first_name = owner.first_name
        owner_model.last_name = owner.last_name
        owner_model.email = owner.email
        owner_model.phone = owner.phone

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
    first_name: Optional[str] = Field(Query(None,
                                            description="Get all owners with the given first name.",
                                            example="Max"))
    last_name: Optional[str] = Field(Query(None,
                                           description="Get all owners with the given last name.",
                                           example="Mustermann"))
    email: Optional[str] = Field(Query(None,
                                       description="Get all owners with the given email.",
                                       example="mustermax@mail.com"))
    phone: Optional[str] = Field(Query(None, description="Get all owners with the given phone-number.",
                                       example="+49-123-123-45678"))
