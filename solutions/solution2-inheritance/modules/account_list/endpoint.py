from base_operation import APIOperation


class CustomAPIOperation(APIOperation):
    def mapping_handler(self, query_result):
        return {
            "context": f"{__class__.__name__}.mapping_handler",
            "query_result": query_result,
        }


OPERATION_CLASS = CustomAPIOperation
