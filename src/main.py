import os

from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse

if not os.environ.get("USE_IN_MEMORY_DB"):
    import conf.config

from .api.owners import owners
from .api.restaurants import restaurants
from .api.tables import tables
from .api.reservations import reservations

from .api.authentication.AuthenticationModels import Token as PydanticToken
from .api.authentication.autentication import authenticate_owner, create_access_token


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
        "name": "authentication",
        "description": "Operations to authenticate"
    },
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
    version="1.0",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Hide schemas from /docs
        "operationsSorter": "method",  # Sort endpoints by their methods
        "docExpansion": None
    },
    redoc_url=None
)

app.include_router(owners.router)
app.include_router(restaurants.router)
app.include_router(tables.router)
app.include_router(reservations.router)


@app.get('/', include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.post('/token', tags=['authentication'])
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
