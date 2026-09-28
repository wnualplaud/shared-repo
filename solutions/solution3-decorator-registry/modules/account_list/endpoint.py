from endpoint_handler_builder import EndpointHandlerBuilder


handler_builder = EndpointHandlerBuilder()


@handler_builder.override("bind_parameters")
def bind_parameters_account_list(handler) -> list:
    body = handler.request.json_body or {}

    account_name = body.get("account_name")
    customer_id = body.get("customer_id")
    return [account_name, customer_id]
