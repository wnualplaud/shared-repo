import importlib
from functools import cache
from pathlib import Path
from typing import Any

from aws_lambda_powertools.event_handler import Request


APP_ROOT = Path(__file__).resolve().parent


@cache
def _load_query(query_path: str) -> str:
    full_path = (APP_ROOT / query_path).resolve()

    if not full_path.is_relative_to(APP_ROOT):
        raise ValueError(f"Invalid query path: {query_path}")

    return full_path.read_text(encoding="utf-8")


class EndpointHandlerTemplate:
    def __init__(self, endpoint_config: dict[str, Any], request: Request):
        self.endpoint_config = endpoint_config
        self.request = request
        self.connector = importlib.import_module(
            f"connectors.{endpoint_config['backend']}"
        )

    def authenticate(self):
        pass

    def handle(self):
        query_result = self.execute_query()
        return self.build_mapping(query_result)

    def bind_parameters(self) -> list:
        return []

    def execute_query(self):
        raw_query = _load_query(self.endpoint_config["query"])
        query_parameters = self.bind_parameters()
        return self.connector.execute(raw_query, query_parameters)

    def build_mapping(self, query_result: Any):
        return {"items": query_result}
