from endpoint_handler_builder import EndpointHandlerBuilder

handler_builder = EndpointHandlerBuilder()


@handler_builder.override("build_mapping")
def build_account_list_mapping(handler, query_result):
    return {
        "context": f"{type(handler).__name__}.build_mapping",
        "query_result": query_result,
    }
