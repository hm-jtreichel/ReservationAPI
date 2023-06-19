"""
A module containing helper functions used for the authentication.
"""
import os

from passlib.context import CryptContext

from typing import Annotated

from ...db.manager import SessionFacade
from sqlalchemy import select

from datetime import timedelta, datetime

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..owners.ownerModels import OwnerModel
from .authenticationModels import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

session = SessionFacade()


def verify_password(plain_password, hashed_password) -> bool:
    """
        Returns a boolean value, validating if given plain password matches the hashed password.

        Parameters:
        -----------
        plain_password: plain password that should be checked
        hashed_password: hashed password as reference, that should match the plain password

        Returns:
        --------
        bool: True, if passwords match, false if they don't
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
        Returns a hashed password for the given input.

        Parameters:
        -----------
        Plain Password (str): Password to be hashed in plain text

        Returns:
        --------
        Hashed password (str): Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """
        Returns a JWT for the given input.

        Parameters:
        -----------
        data (dict): A dictionary containing information about the user/owner.

        Returns:
        --------
        JWT (str): JWT for authentication.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")))

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.environ.get("HASHING_SECRET_KEY"),
                             algorithm=os.environ.get("HASHING_ALGORITHM"))
    return encoded_jwt


def authenticate_owner(email: str, password: str):
    """
        Returns an owner if the given credentials match stored values in the database.

        Parameters:
        -----------
        email (str): The owners email address.
        password (str): The owners password in plain text.

        Returns:
        --------
        Owner (OwnerModel): The owner matching the credentials, False if they are invalid,.
    """
    qry = select(OwnerModel).where(OwnerModel.email == email)
    owner = session.scalars(qry).first()

    if not owner:
        return False
    if not verify_password(password, owner.hashed_password):
        return False

    return owner


def get_current_owner(token: Annotated[str, Depends(oauth2_scheme)]):
    """
        Returns the owner matching the given JWT.

        Parameters:
        -----------
        token (Annotated[str, Depends(oauth2_scheme)]): The JWT used for authentication.

        Returns:
        --------
        Owner: The owner matching the JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.environ.get("HASHING_SECRET_KEY"),
                             algorithms=[os.environ.get("HASHING_ALGORITHM")])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    qry = select(OwnerModel).where(OwnerModel.email == token_data.email)
    owner = session.scalars(qry).first()
    if owner is None:
        raise credentials_exception
    return owner
