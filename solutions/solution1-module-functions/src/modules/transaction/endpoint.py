from pathlib import Path

from connectors.dynamo import execute

QUERY = Path(__file__).with_name("query.sql").read_text()

def endpoint_handler(endpoint, module, request):
    payload = request.json_body or {}

    rows = execute(sql=QUERY, parameters=payload)

    return map_response(rows, payload=payload)


def map_response(rows, **params):

    return {
        "endpoint": "transaction",
        "source": "dynamo",
        "request_body": params["payload"],
        "entries": rows
    }
