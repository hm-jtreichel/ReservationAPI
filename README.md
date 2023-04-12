# ReservationAPI

This project is being developed during the class "Enterprise-Information-Management" in Summer 2023.

***

The goal is to provide a REST-API with basic reservation-services for restaurants such as:
- Creating/Updating/Deleting a restaurant.
- Managing tables inside the restaurant.
- Creating/Updating/Deleting reservations for certain tables.
- And probably more.

Furthermore, depending on the required time there might be an additional implementation of a GraphQL-endpoint as well.

The project is mainly built upon the following frameworks and technologies:
- [FastAPI](https://fastapi.tiangolo.com/) - A modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
- [SQLAlchemy](https://www.sqlalchemy.org/) - A Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.
- [Graphene](https://graphene-python.org/) (if GraphQL will be implemented) - GraphQL in Python made easy. Implemented using:
  - [starlette-graphene3](https://pypi.org/project/starlette-graphene3/) - A simple ASGI app for using Graphene v3 with Starlette and FastAPI.
  - [Graphene-SQLAlchemy](https://docs.graphene-python.org/projects/sqlalchemy/en/latest/) - Allowing developers to quickly and easily create a GraphQL API that seamlessly interacts with a SQLAlchemy-managed database.
- [PostgreSQL](https://www.postgresql.org/) - A powerful, open source object-relational database.

***

The development-process is heavily influenced by the agile-framework "Kanban" - the corresponding board with all issues can be found [here](https://gitlab.lrz.de/000000003B9BFFC4/reservationapi/-/boards/12285).

The team members of this project are:
- [Veronika Reichling](https://gitlab.lrz.de/000000003B9BFF79)
- [Valentin Bumeder](https://gitlab.lrz.de/000000003B9BFFC1)
- [Jannik Treichel](https://gitlab.lrz.de/000000003B9BFFC4)
