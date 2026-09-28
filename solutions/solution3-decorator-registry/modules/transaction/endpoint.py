from endpoint_handler_builder import EndpointHandlerBuilder


handler_builder = EndpointHandlerBuilder()


@handler_builder.override("bind_parameters")
def bind_parameters_transaction(handler) -> list:
    body = handler.request.json_body or {}

    account_id = body.get("account_id")
    return [account_id]
