from fastapi import FastAPI


import graphene
from starlette_graphene3 import GraphQLApp, make_graphiql_handler


class Query(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(self, info):
        return "Hello World"


schema = graphene.Schema(query=Query, auto_camelcase=False)

app = FastAPI()
app.mount("/graphql", GraphQLApp(schema=schema, on_get=make_graphiql_handler()))
