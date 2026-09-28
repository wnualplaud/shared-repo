from typing import Any, Optional

from aws_lambda_powertools.event_handler import Request


class APIOperation:
    def __init__(self):
        self.endpoint_config: Optional[dict[str, Any]] = None
        self.request: Optional[Request] = None

    def auth(self):
        pass

    def handle(self, endpoint_config: dict[str, Any], request: Request):
        self.endpoint_config = endpoint_config
        self.request = request

        self.auth()

        query_result = self.query_handler()
        return self.mapping_handler(query_result)

    def query_handler(self):
        return {
            "context": f"{__class__.__name__}.query_handler",
            "query": self.endpoint_config["query"],
        }

    def mapping_handler(self, query_result: Any):
        return {
            "context": f"{__class__.__name__}.mapping_handler",
            "query_result": query_result,
        }
