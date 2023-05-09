from fastapi import FastAPI

from .owners import owners

description = """
This project was being developed during the class "Enterprise-Information-Management" in Summer 2023.

***

The ReservationAPI provides basic services to manage reservations for restaurants such as:
- Creating/Updating/Deleting a restaurant.
- Managing tables inside the restaurant.
- Creating/Updating/Deleting reservations for certain tables.
"""

tags_metadata = [
    {
        "name": "owners",
        "description": "Operations with owners"
    }
]

app = FastAPI(
    title="ReservationAPI",
    description=description,
    version="0.1",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1  # Hide schemas from /docs
    },
    redoc_url=None
)

app.include_router(owners.router)
