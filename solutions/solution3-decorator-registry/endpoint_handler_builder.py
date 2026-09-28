from endpoint_handler_template import EndpointHandlerTemplate

ENDPOINT_HANDLER_CLASS_NAME = "EndpointHandler"


class EndpointHandlerBuilder:
    def __init__(self, template_class=EndpointHandlerTemplate):
        self.template_class = template_class
        self.overrides = {}

    def override(self, method_name):
        def decorator(function):
            self.overrides[method_name] = function
            return function

        return decorator

    def build(self):
        return type(
            ENDPOINT_HANDLER_CLASS_NAME,
            (self.template_class,),
            self.overrides,
        )
