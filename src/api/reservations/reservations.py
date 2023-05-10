from typing import List, Union

from fastapi import APIRouter, status, Depends, Path, HTTPException, Body
from sqlalchemy import select

from ..util import validate_ids_in_put_request
from ...db.manager import SessionFacade
from .reservationModels import Reservation as PydanticReservation, \
    ReservationNew as PydanticReservationNew, \
    ReservationQuery as PydanticReservationQuery, \
    ReservationPut as PydanticReservationPut, \
    ReservationModel


router = APIRouter(
    prefix="/reservations",
    tags=["reservations"],
    dependencies=[],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Data or endpoint not found"}
    }
)

session = SessionFacade()
