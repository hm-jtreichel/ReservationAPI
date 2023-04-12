from typing import List, Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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


class Address(Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="addresses")

    def __repr__(self) -> str:
        return f"<Address, id={self.id}, email_address={self.email_address}>"


if __name__ == "__main__":
    from sqlalchemy import create_engine
    # Engine using SQLite (later PostgreSQL)
    engine = create_engine("sqlite://", echo=False)

    Base.metadata.create_all(engine)

    from sqlalchemy.orm import Session
    session = Session(engine)

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

    session.add_all([vroni, valle, jannik])
    session.commit()

    from sqlalchemy import select
    statement = select(User).where(User.name.in_(["Vroni", "Jannik", "Valle"]))

    print("Run before name-edit")
    for user in session.scalars(statement):
        print(user)
        if user.name == "Jannik":
            # Update attributes like objects in python
            user.name = "Not Jannik anymore"
            session.add(user)
            session.commit()

    print("Run after name-edit (same query)")
    for user in session.scalars(statement):
        print(user)

    print("Join Example")
    statement = (
        select(Address.email_address)
        .join(Address.user)
        .where(User.name == "Valle")
        .where(Address.email_address == "valentin.bumeder@hm.edu")
    )

    valle_address = session.scalars(statement).one()

    print(valle_address)
