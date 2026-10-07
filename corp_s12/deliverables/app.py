import importlib

from fastapi import FastAPI

from endpoint_registry import ENDPOINTS



app = FastAPI()


@app.get("/health")
def health_check():
    return {"message": "ok"}


def register_endpoint(endpoint_config):
    
    endpoint_handler_class = resolve_endpoing_handler(endpoint_config)

    def route_handler(body: dict):
        handler = endpoint_handler_class(body=body)
        handler.authenticate()
        return handler.handle()

    app.add_api_route(
        endpoint_config["path"],
        route_handler,
        methods=[endpoint_config["method"]],
    )


def resolve_endpoing_handler(endpoint_config):
    
    endpoint_handler_package = endpoint_config.get("handler")

    if endpoint_handler_package is None:
        raise ValueError(f"Missing 'handler' for endpoint {endpoint_config['path']}")

    module = importlib.import_module(f"handlers.{endpoint_handler_package}")
    return module.OPERATION_CLASS


for endpoint_config in ENDPOINTS:
    
    # Skip anything but bool True; bool False, any string "true", "false",  None (no enabled key)
    if endpoint_config.get("enabled", False) is True:
        register_endpoint(endpoint_config)
