from typing import Annotated, Optional

from fastapi import APIRouter, status, HTTPException, Depends, Query, Body
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select

from ...db.manager import SessionFacade
from .AuthenticationModels import Token as PydanticToken
from .authenticationUtils import authenticate_owner, create_access_token
from ..owners.ownerModels import OwnerNew as PydanticOwnerNew, \
    Owner as PydanticOwner,\
    OwnerModel

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    dependencies=[],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Data or endpoint not found"}
    }
)

session = SessionFacade()


# TODO: Docstring!
@router.post('/token')
def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> PydanticToken:
    owner = authenticate_owner(form_data.username, form_data.password)
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": owner.email}
    )
    return PydanticToken(access_token=access_token,
                         token_type="bearer")


@router.post('/register',
             summary="Register a new owner",
             response_description="The registered owner",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid request (e.g. Email already taken)"}
             })
def create_owner(new_owner: PydanticOwnerNew = Body(description="The owner object you want to register")
                 ) -> PydanticOwner:
    """
    Register a new owner.
    \f
    Parameters:
    -----------
    new_owner : PydanticOwnerNew
        The PydanticOwnerNew object to use as a template for the new owner.

    Raises:
    -------
    HTTPException
        Raised if the request body is empty or malformed or the email is already taken.

    Returns:
    --------
    PydanticOwner
        A PydanticOwner object representing the newly created owner.
    """

    look_for_owner_qry = select(OwnerModel).where(OwnerModel.email == new_owner.email)
    existing_owner = session.scalars(look_for_owner_qry).first()
    if existing_owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Email <{new_owner.email}> is already taken. Please choose another one.")

    owner_model = new_owner.cast_to_model()

    session.add(owner_model)
    session.commit()

    added_owner = PydanticOwner.cast_from_model(owner_model)

    return added_owner
