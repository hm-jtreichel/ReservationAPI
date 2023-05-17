"""
This module defines a Pydantic model representing business hours of a restaurant.
"""

from __future__ import annotations

from datetime import time

from pydantic import BaseModel as PydanticBase, Extra, Field, root_validator

from ...db.models import BusinessHour as BusinessHourModel


class BusinessHour(PydanticBase):
    """
    Represents a business hour of a restaurant.
    """
    weekday: int = Field(ge=0, le=6)
    open_time: time
    open_for_reservation_until: time
    close_time: time

    @root_validator(skip_on_failure=True)
    def validate_times(cls, values):
        if values['open_time'] > values['close_time']:
            raise ValueError("Restaurant can't close before it has opened.")
        if (values['open_for_reservation_until'] > values['close_time'] or
                values['open_for_reservation_until'] < values['open_time']):
            raise ValueError("Open-for-reservation-until-time must be between opening and closing time.")
        return values

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

    def cast_to_model(self) -> BusinessHourModel:
        """
        Returns a database model instance corresponding to the current BusinessHour instance.

        Returns:
            BusinessHourModel: The database model instance of the BusinessHour.
        """
        business_hour_model = BusinessHourModel(
            weekday=self.weekday,
            open_time=self.open_time,
            open_for_reservation_until=self.open_for_reservation_until,
            close_time=self.close_time,
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
