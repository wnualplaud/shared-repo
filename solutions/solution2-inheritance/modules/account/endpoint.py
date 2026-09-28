from base_operation import APIOperation


class CustomAPIOperation(APIOperation):
    def query_handler(self):
        return {
            "context": f"{__class__.__name__}.query_handler",
            "query": self.endpoint_config["query"],
        }


OPERATION_CLASS = CustomAPIOperation
