# Solution 3 -- Decorator Registry and Generated Endpoint Handler

This design proof lets endpoint modules provide ordinary functions while
the framework binds those functions to a concrete `EndpointHandler`
subclass of `EndpointHandlerTemplate`.

The proven path is:

```text
endpoint config
-> import optional endpoint module
-> obtain an EndpointHandlerBuilder
-> build a concrete EndpointHandler subclass
-> create a fresh instance for each request
-> authenticate
-> handle
```

An endpoint without a configured module receives an empty
`EndpointHandlerBuilder`. Its generated class therefore inherits every
method from `EndpointHandlerTemplate`. A configured module exports
`handler_builder`; decorators register functions in that
builder, and matching names become methods on the generated class.
Unregistered methods continue to resolve through normal Python MRO.

The registration decorator returns the original function. It does not
wrap request-time calls. `EndpointHandlerBuilder.build()` supplies the
registered functions as the namespace dictionary passed to
`type(name, bases, namespace)`.

## Completed Scope

| Anchor | Goal | Status |
|---|---|---|
| S3-0 | Copy the runnable Solution 2 scaffold | Complete |
| S3-1 | Bind request state in the constructor and invoke authentication before `handle()` | Complete |
| S3-2 | Bind named decorated overrides to a generated subclass | Complete |
| S3-3 | Allow a decorated custom `handle` to own the flow | Complete |
| S3-4 | Validate names, duplicates, callback signatures, and module exports | Deferred |
| S3-5 | Exercise the default, selective-override, combined-override, and custom-handle paths | Complete |
| S3-6 | Record the final smoke matrix and close the core proof | Complete |

The proof uses diagnostic methods only. It does not read SQL files,
bind request parameters, call real connectors, implement an auth policy,
or define production response and error mapping.

## Smoke Matrix

All commands run from the repository root with its virtual environment active.
The request body is accepted by the local harness but is not consumed by
the diagnostic handler methods yet.

| Route | Proven behavior |
|---|---|
| `POST /statement` | Empty builder; inherited query, execution, and mapping |
| `POST /account/list` | Inherited query/execution and decorated mapping |
| `POST /account` | Decorated query and inherited execution/mapping |
| `POST /transaction` | Decorated query and mapping with inherited execution |
| `POST /balance` | Decorated `handle` owns the flow and calls inherited stages explicitly |

### Default Handler

```sh
python3 solutions/solution3-decorator-registry/test_local.py \
  POST /statement --body '{"query":"test"}'
```

```text
{'statusCode': 200, 'body': '{"context":"EndpointHandlerTemplate.build_mapping","query_result":{"context":"EndpointHandlerTemplate.execute_query","query":"modules/statement/query.sql"}}', 'isBase64Encoded': False, 'multiValueHeaders': defaultdict(<class 'list'>, {'Content-Type': ['application/json']})}
```

### Mapping Override

```sh
python3 solutions/solution3-decorator-registry/test_local.py \
  POST /account/list --body '{"query":"test"}'
```

```text
{'statusCode': 200, 'body': '{"context":"EndpointHandler.build_mapping","query_result":{"context":"EndpointHandlerTemplate.execute_query","query":"modules/account_list/query.sql"}}', 'isBase64Encoded': False, 'multiValueHeaders': defaultdict(<class 'list'>, {'Content-Type': ['application/json']})}
```

### Query Override

```sh
python3 solutions/solution3-decorator-registry/test_local.py \
  POST /account --body '{"query":"test"}'
```

```text
{'statusCode': 200, 'body': '{"context":"EndpointHandlerTemplate.build_mapping","query_result":{"context":"EndpointHandlerTemplate.execute_query","query":{"context":"EndpointHandler.build_query","query":"modules/account/query.sql"}}}', 'isBase64Encoded': False, 'multiValueHeaders': defaultdict(<class 'list'>, {'Content-Type': ['application/json']})}
```

### Query and Mapping Overrides

```sh
python3 solutions/solution3-decorator-registry/test_local.py \
  POST /transaction --body '{"query":"test"}'
```

```text
{'statusCode': 200, 'body': '{"context":"EndpointHandler.build_mapping","query_result":{"context":"EndpointHandlerTemplate.execute_query","query":{"context":"EndpointHandler.build_query","query":"modules/transaction/query.sql"}}}', 'isBase64Encoded': False, 'multiValueHeaders': defaultdict(<class 'list'>, {'Content-Type': ['application/json']})}
```

### Custom Handle

```sh
python3 solutions/solution3-decorator-registry/test_local.py \
  POST /balance --body '{"query":"test"}'
```

```text
{'statusCode': 200, 'body': '{"context":"EndpointHandler.handle","response":{"context":"EndpointHandlerTemplate.build_mapping","query_result":{"context":"EndpointHandlerTemplate.execute_query","query":"modules/balance/query.sql"}}}', 'isBase64Encoded': False, 'multiValueHeaders': defaultdict(<class 'list'>, {'Content-Type': ['application/json']})}
```

The outer `EndpointHandler.handle` context and the additional
`response` level in the final case demonstrate that the decorated
custom handle ran instead of the inherited default handle. Its nested
contexts show that it then chose to call inherited stages.

## Deferred Work

Registration validation, wrapper-based decorators, a possible common
provider contract for prebuilt and generated classes, and richer flow
metadata remain deferred. These do not block the generated-subclass
mechanism proven here.

Python decorator mechanics used by the registry are documented in
[`decorator-mechanics.md`](decorator-mechanics.md). The repository-level
comparison is in [`../../README.md`](../../README.md). Research evidence remains in
[`../solution2-inheritance/operation-extension-research.md`](../solution2-inheritance/operation-extension-research.md).

Dependencies are shared through the repository root `requirements.txt` and
`.venv`.
