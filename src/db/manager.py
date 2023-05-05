from typing import Iterable

from sqlalchemy import create_engine, Executable, ScalarResult
from sqlalchemy.orm import Session

# TODO: Engine using SQLite (currently connection + creation /
#  later split with PostgreSQL)
engine = create_engine("sqlite:///:memory:", echo=True)

from models import Base
Base.metadata.create_all(engine)


class SessionFacade:
    """
    A session facade for SQLAlchemy ORM.

    This class provides a simplified interface to the SQLAlchemy ORM session
    object. It exposes only the session methods needed by the project.

    Attributes:
        session (Session): An instance of SQLAlchemy's Session class.
    """

    def __init__(self):
        """
        Initializes a new SessionFacade object.

        Creates a new instance of SQLAlchemy's Session class and assigns it to
        the 'session' attribute of this object.
        """
        self.session = Session(engine)

    def add(self, obj: object):
        """
        Adds a single object to the session.

        Args:
            obj (object): The object to add to the session.
        """
        self.session.add(obj)

    def add_all(self, instances: Iterable[object]):
        """
        Adds a collection of objects to the session.

        Args:
            instances (Iterable[object]): An iterable containing the objects to
                add to the session.
        """
        self.session.add_all(instances)

    def commit(self):
        """
        Commits the current transaction.

        Commits any changes made to objects in the session since the last commit
        or rollback. If there are no changes, this method does nothing.
        """
        self.session.commit()

    def rollback(self):
        """
        Roll back the current transaction in the session.

        This method rolls back the current transaction in the session. It undoes all changes made to the objects
        since the last commit. Any objects that were added to the session will be removed.
        """
        self.session.rollback()

    def scalars(self, statement: Executable) -> ScalarResult:
        """
        Executes a SQL statement and returns a scalar result.

        Args:
            statement (Executable): The SQL statement to execute.

        Returns:
            ScalarResult: The result of executing the statement as a scalar value.
        """
        return self.session.scalars(statement)
