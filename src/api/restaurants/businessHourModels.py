"""
This module defines a Pydantic model representing business hours of a restaurant.
"""

from __future__ import annotations

from datetime import time

from pydantic import BaseModel as PydanticBase, Extra

from ...db.models import BusinessHour as BusinessHourModel


class BusinessHour(PydanticBase):
    """
    Represents a business hour of a restaurant.
    """
    weekday: int
    open_time: time
    open_for_reservation_until: time
    close_time: time

    class Config:
        schema_extra = {
            "example": {
                "weekday": 1,
                "open_time": "16:00:00",
                "open_for_reservation_until": "20:00:00",
                "close_time": "23:00:00",
            }
        }
        extra = Extra.forbid

    @staticmethod
    def cast_to_model(business_hour: BusinessHour) -> BusinessHourModel:
        """
        Returns a database model instance corresponding to the current BusinessHour instance.

        Args:
            business_hour (BusinessHour): The BusinessHour instance to be converted.

        Returns:
            BusinessHourModel: The database model instance of the BusinessHour.
        """
        business_hour_model = BusinessHourModel(
            weekday=business_hour.weekday,
            open_time=business_hour.open_time,
            open_for_reservation_until=business_hour.open_for_reservation_until,
            close_time=business_hour.close_time,
        )
        return business_hour_model

    @staticmethod
    def cast_from_model(business_hour_model: BusinessHourModel) -> BusinessHour:
        """
        Returns a BusinessHour instance corresponding to the database model instance.

        Args:
            business_hour_model (BusinessHourModel): The database model instance to be converted.

        Returns:
            BusinessHour: The BusinessHour instance corresponding to the database model instance.
        """
        business_hour = BusinessHour(
            weekday=business_hour_model.weekday,
            open_time=business_hour_model.open_time,
            open_for_reservation_until=business_hour_model.open_for_reservation_until,
            close_time=business_hour_model.close_time,
        )
        return business_hour
