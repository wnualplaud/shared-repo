from endpoint_handler_builder import EndpointHandlerBuilder


handler_builder = EndpointHandlerBuilder()


@handler_builder.override("build_query")
def build_account_query(handler):
    return {
        "context": f"{type(handler).__name__}.build_query",
        "query": handler.endpoint_config["query"],
    }
