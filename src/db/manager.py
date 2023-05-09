from typing import Iterable

from sqlalchemy import create_engine, Executable, ScalarResult
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# TODO: Engine using SQLite (currently connection + creation /
#  later split with PostgreSQL) - also probably remove connect_args and poolclass (+import)
engine = create_engine("sqlite://",
                       echo=False,
                       connect_args={"check_same_thread": False},
                       poolclass=StaticPool)

from .models import Base
Base.metadata.create_all(engine)


class SessionFacade:
    """
    A session facade for SQLAlchemy ORM.

    This class provides a simplified interface to the SQLAlchemy ORM session
    object. It exposes only the session methods needed by the project.
    """

    def __init__(self):
        """
        Initializes a new SessionFacade object.

        Creates a new instance of SQLAlchemy's Session class and assigns it to
        the 'session' attribute of this object.
        """
        self._session = Session(engine)

    def add(self, obj: object):
        """
        Adds a single object to the session.

        Args:
            obj (object): The object to add to the session.
        """
        self._session.add(obj)

    def add_all(self, instances: Iterable[object]):
        """
        Adds a collection of objects to the session.

        Args:
            instances (Iterable[object]): An iterable containing the objects to
                add to the session.
        """
        self._session.add_all(instances)

    def merge(self, obj: object):
        """
        Merges the given object into the session.

        Args:
        -----
        obj : object
            The object to be merged into the session
        """
        self._session.merge(obj)

    def merge_all(self, instances: Iterable[object]):
        """
        Merges all instances in the given iterable into the session.

        Args:
        -----
        instances : Iterable[object]
            The instances to be merged into the session.
        """
        for instance in instances:
            self.merge(instance)

    def commit(self):
        """
        Commits the current transaction.

        Commits any changes made to objects in the session since the last commit
        or rollback. If there are no changes, this method does nothing.
        """
        self._session.commit()

    def rollback(self):
        """
        Roll back the current transaction in the session.

        This method rolls back the current transaction in the session. It undoes all changes made to the objects
        since the last commit. Any objects that were added to the session will be removed.
        """
        self._session.rollback()

    def scalars(self, statement: Executable) -> ScalarResult:
        """
        Executes a SQL statement and returns a scalar result.

        Args:
            statement (Executable): The SQL statement to execute.

        Returns:
            ScalarResult: The result of executing the statement as a scalar value.
        """
        return self._session.scalars(statement)

    def delete(self, obj: object):
        """
        Deletes the given object from the session.

        Args:
        -----
        obj : object
            The object to be deleted from the session.
        """
        self._session.delete(obj)

    def delete_all(self, instances: Iterable[object]):
        """
        Deletes all instances in the given iterable from the session.

        Args:
        -----
        instances : Iterable[object]
            The instances to be deleted from the session.
        """
        for instance in instances:
            self.delete(instance)
