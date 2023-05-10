from fastapi import FastAPI

from .owners import owners
from .restaurants import restaurants
from .tables import tables
from .reservations import reservations

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
    },
    {
        "name": "restaurants",
        "description": "Operations with restaurants"
    },
    {
        "name": "tables",
        "description": "Operations with tables"
    },
    {
        "name": "reservations",
        "description": "Operations with reservations"
    }
]

app = FastAPI(
    title="ReservationAPI",
    description=description,
    version="0.1",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Hide schemas from /docs
        "operationsSorter": "method"  # Sort endpoints by their methods
    },
    redoc_url=None
)

app.include_router(owners.router)
app.include_router(restaurants.router)
app.include_router(tables.router)
app.include_router(reservations.router)
