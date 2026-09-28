# Solution 1 -- Module Functions

This is the direct module-function baseline. It is kept runnable so its
contract and tradeoffs can be compared with the inheritance and decorator
variants in this repository.

## Where the shape comes from

The code uses the following boundaries:

- **Resolver** -- path/method dispatch only, modeled on AWS Powertools for
  Lambda (Python)'s `APIGatewayRestResolver` (decorator registers a
  function, `resolve(event)` looks it up and calls it). Function +
  decorator, not class + inheritance.
- **Registry** -- `endpoint_registry.py` explicitly declares active
  method/path/module combinations. `app.py` imports each module and
  registers its route at initialization time.
- **Module** -- each endpoint package currently contains `endpoint.py`
  and `query.sql`. `endpoint_handler` owns that endpoint's request,
  execution, and output flow; `map_response` shapes the complete result.
  There is no shared runner.
- **Connector layer** -- `connectors/athena.py` and
  `connectors/dynamo.py` currently return fake rows. Modules select the
  connector they need directly.

## Currently open (not yet decided anywhere)

- Real Athena and DynamoDB client contracts and parameter binding.
- Logging, error mapping, and connector timeout/polling behavior.
- Whether deployment should split Lambda functions by backend type.
- Whether registry ownership eventually needs one definition file per
  endpoint instead of the current central Python list.
