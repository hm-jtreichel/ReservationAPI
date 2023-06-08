"""
Module containing simple Pydantic models used for representing
and validating Authentication data in API requests and responses.
"""
from pydantic import BaseModel


class Token(BaseModel):
    """
        Pydantic model representing a Token.
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
        Pydantic model representing Token Data.
    """
    email: str | None = None
