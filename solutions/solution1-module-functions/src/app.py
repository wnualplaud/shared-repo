import importlib

from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Request
from endpoint_registry import ENDPOINTS



app = APIGatewayRestResolver()

@app.get("/health")
def health_check():
    return {"message": "ok"}


def register_endpoint(endpoint):
    module = importlib.import_module(endpoint["module"])

    @app.route(endpoint["path"], method=endpoint["method"])
    def handler(request: Request):
        return module.endpoint_handler(
            endpoint=endpoint,
            module=module,
            request=request,
        )



for endpoint in ENDPOINTS:
    register_endpoint(endpoint)