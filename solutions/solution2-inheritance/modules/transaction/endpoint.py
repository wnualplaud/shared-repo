from base_operation import APIOperation


class CustomAPIOperation(APIOperation):
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
