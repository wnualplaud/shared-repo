from typing import Any

from aws_lambda_powertools.event_handler import Request


class EndpointHandlerTemplate:
    def __init__(self, endpoint_config: dict[str, Any], request: Request):
        self.endpoint_config = endpoint_config
        self.request = request

    def authenticate(self):
        pass

    def handle(self):
        query = self.build_query()
        query_result = self.execute_query(query)

        return self.build_mapping(query_result)

    def build_query(self):
        return self.endpoint_config["query"]

    def execute_query(self, query):
        return {
            "context": f"{__class__.__name__}.execute_query",
            "query": query,
        }

    def build_mapping(self, query_result: Any):
        return {
            "context": f"{__class__.__name__}.build_mapping",
            "query_result": query_result,
        }
