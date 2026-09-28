from endpoint_handler_builder import EndpointHandlerBuilder


handler_builder = EndpointHandlerBuilder()


@handler_builder.override("handle")
def handle_balance(handler):
    query = handler.build_query()
    query_result = handler.execute_query(query)
    response = handler.build_mapping(query_result)

    return {
        "context": f"{type(handler).__name__}.handle",
        "response": response,
    }
