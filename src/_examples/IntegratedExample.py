from __future__ import annotations

# --------------------------------------------------------- #
# Database setup
# --------------------------------------------------------- #

from typing import List, Optional
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session


class Base(DeclarativeBase):
    pass


class SessionWrapper:
    engine = create_engine("sqlite://", echo=False)
    session = Session(engine)

    @staticmethod
    def create_database():
        Base.metadata.create_all(SessionWrapper.engine)


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]

    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User, id={self.id}, name={self.name}>"

    @staticmethod
    def get_dummy_data() -> List[User]:
        vroni = User(
            name="Vroni",
            fullname="Veronika Reichling",
            addresses=[Address(email_address="vvolk@hm.edu")]
        )
        valle = User(
            name="Valle",
            fullname="Valentin Bumeder",
            addresses=[Address(email_address="valentin.bumeder@hm.edu")]
        )
        jannik = User(
            name="Jannik",
            fullname="Jannik Treichel",
            addresses=[Address(email_address="jtreiche@hm.edu"),
                       Address(email_address="treicheljannik@gmail.com")]
        )
        return [vroni, valle, jannik]


class Address(Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="addresses")

    def __repr__(self) -> str:
        return f"<Address, id={self.id}, email_address={self.email_address}>"


SessionWrapper.create_database()
SessionWrapper.session.add_all(User.get_dummy_data())
SessionWrapper.session.commit()

# --------------------------------------------------------- #
# GraphQL setup
# --------------------------------------------------------- #

import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from starlette_graphene3 import GraphQLApp, make_graphiql_handler


class UserType(SQLAlchemyObjectType):
    class Meta:
        model = User


class AddressType(SQLAlchemyObjectType):
    class Meta:
        model = Address


class Query(graphene.ObjectType):

    users = graphene.List(UserType)

    def resolve_users(self, info):
        return SessionWrapper.session.scalars(
            select(User)
        ).all()

    addresses = graphene.List(AddressType)

    def resolve_addresses(self, info):
        return SessionWrapper.session.scalars(
            select(Address)
        ).all()


schema = graphene.Schema(query=Query, auto_camelcase=False)

# --------------------------------------------------------- #
# FastAPI setup
# --------------------------------------------------------- #

from fastapi import FastAPI

app = FastAPI()
app.mount("/graphql", GraphQLApp(schema=schema, on_get=make_graphiql_handler()))


@app.get("/")
async def root():
    return {"message": "Hello integrated example!"}
