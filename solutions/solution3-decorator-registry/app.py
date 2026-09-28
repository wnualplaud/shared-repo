import importlib

from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Request
from endpoint_handler_builder import EndpointHandlerBuilder
from endpoint_registry import ENDPOINTS


app = APIGatewayRestResolver()


@app.get("/health")
def health_check():
    return {"message": "ok"}


def register_endpoint(endpoint_config):
    handler_class = resolve_endpoint_handler_class(endpoint_config)

    @app.route(endpoint_config["path"], method=endpoint_config["method"])
    def route_handler(request: Request):
        endpoint_handler = handler_class(
            endpoint_config=endpoint_config,
            request=request,
        )
        endpoint_handler.authenticate()
        return endpoint_handler.handle()


def resolve_endpoint_handler_class(endpoint_config):
    endpoint_module = endpoint_config.get("module")

    if endpoint_module is None:
        handler_builder = EndpointHandlerBuilder()

    else:
        module = importlib.import_module(endpoint_module)
        handler_builder = module.handler_builder

    return handler_builder.build()


for endpoint_config in ENDPOINTS:
    register_endpoint(endpoint_config)
