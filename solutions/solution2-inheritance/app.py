import importlib

from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Request
from endpoint_registry import ENDPOINTS
from base_operation import APIOperation



app = APIGatewayRestResolver()


@app.get("/health")
def health_check():
    return {"message": "ok"}


def register_endpoint(endpoint_config):
    operation_class = resolve_operation_class(endpoint_config)

    @app.route(endpoint_config["path"], method=endpoint_config["method"])
    def handler(request: Request):
        instance = operation_class()
        return instance.handle(
            endpoint_config=endpoint_config,
            request=request,
        )


def resolve_operation_class(endpoint_config):
    operation_module = endpoint_config.get("module")

    if operation_module is None:
        return APIOperation

    module = importlib.import_module(operation_module)
    return module.OPERATION_CLASS


for endpoint_config in ENDPOINTS:
    register_endpoint(endpoint_config)
