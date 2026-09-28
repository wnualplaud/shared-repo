from base_operation import APIOperation


class CustomAPIOperation(APIOperation):
    def handle(self, endpoint_config, request):
        self.endpoint_config = endpoint_config
        self.request = request

        self.auth()

        query_result = self.query_handler()
        return self.mapping_handler(query_result)

    def mapping_handler(self, query_result):
        return {
            "context": f"{__class__.__name__}.mapping_handler",
            "query_result": query_result,
        }

    def query_handler(self):
        return {
            "context": f"{__class__.__name__}.query_handler",
            "query": self.endpoint_config["query"],
        }


OPERATION_CLASS = CustomAPIOperation
