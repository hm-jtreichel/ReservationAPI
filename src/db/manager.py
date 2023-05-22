from typing import Iterable
import os

from sqlalchemy import create_engine, Executable, ScalarResult, URL
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import make_transient

url = URL.create(
    drivername=f'{os.environ.get("DATABASE_DIALECT")}+{os.environ.get("DATABASE_DRIVER")}',
    username=os.environ.get("DATABASE_USER"),
    password=os.environ.get("DATABASE_PASSWORD"),
    host=os.environ.get("DATABASE_HOST"),
    port=os.environ.get("DATABASE_PORT"),
    database=os.environ.get("DATABASE_NAME")
)
engine = create_engine(url, echo=False)

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

    @staticmethod
    def flush():
        """
        Flushes the session.
        """
        SessionFacade._session.flush()

    @staticmethod
    def make_transient(obj: object):
        """
        Returns a given object to a transient state.

        Args:
        -----
        obj : object
            The object to be deleted from the session.
        """
        make_transient(obj)
