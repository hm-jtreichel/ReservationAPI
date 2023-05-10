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
    _session = Session(engine)

    @staticmethod
    def add(obj: object):
        """
        Adds a single object to the session.

        Args:
            obj (object): The object to add to the session.
        """
        SessionFacade._session.add(obj)

    @staticmethod
    def add_all(instances: Iterable[object]):
        """
        Adds a collection of objects to the session.

        Args:
            instances (Iterable[object]): An iterable containing the objects to
                add to the session.
        """
        SessionFacade._session.add_all(instances)

    @staticmethod
    def merge(obj: object):
        """
        Merges the given object into the session.

        Args:
        -----
        obj : object
            The object to be merged into the session
        """
        SessionFacade._session.merge(obj)

    @staticmethod
    def merge_all(instances: Iterable[object]):
        """
        Merges all instances in the given iterable into the session.

        Args:
        -----
        instances : Iterable[object]
            The instances to be merged into the session.
        """
        for instance in instances:
            SessionFacade.merge(instance)

    @staticmethod
    def commit():
        """
        Commits the current transaction.

        Commits any changes made to objects in the session since the last commit
        or rollback. If there are no changes, this method does nothing.
        """
        SessionFacade._session.commit()

    @staticmethod
    def rollback():
        """
        Roll back the current transaction in the session.

        This method rolls back the current transaction in the session. It undoes all changes made to the objects
        since the last commit. Any objects that were added to the session will be removed.
        """
        SessionFacade._session.rollback()

    @staticmethod
    def scalars(statement: Executable) -> ScalarResult:
        """
        Executes a SQL statement and returns a scalar result.

        Args:
            statement (Executable): The SQL statement to execute.

        Returns:
            ScalarResult: The result of executing the statement as a scalar value.
        """
        return SessionFacade._session.scalars(statement)

    @staticmethod
    def delete(obj: object):
        """
        Deletes the given object from the session.

        Args:
        -----
        obj : object
            The object to be deleted from the session.
        """
        SessionFacade._session.delete(obj)

    @staticmethod
    def delete_all(instances: Iterable[object]):
        """
        Deletes all instances in the given iterable from the session.

        Args:
        -----
        instances : Iterable[object]
            The instances to be deleted from the session.
        """
        for instance in instances:
            SessionFacade.delete(instance)
