# Lambda Endpoint Design Prototypes

This repository contains three runnable Python design prototypes for
config-registered API Gateway endpoints hosted by AWS Lambda and routed with
AWS Lambda Powertools.

The implementations compare three endpoint behavior-binding mechanisms:

1. `solution1-module-functions`: a route invokes an ordinary module function.
2. `solution2-inheritance`: a route instantiates a concrete default handler or
   an explicitly configured subclass.
3. `solution3-decorator-registry`: decorated functions are registered and
   bound to a generated handler subclass.

Solutions 1 and 2 are local design proofs whose Athena and DynamoDB
connectors return stub data. Solution 3 has real connectors that call
Athena and DynamoDB (PartiQL) through boto3; running it needs AWS
credentials from the default boto3 chain and the resources described in
its README. No credentials, account identifiers, or real customer data are
stored in this repository.

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Run commands from the repository root. For example:

```sh
python3 solutions/solution1-module-functions/src/test_local.py \
  POST /account/list --body '{"query":"test"}'

python3 solutions/solution2-inheritance/test_local.py \
  POST /account/list --body '{"query":"test"}'

python3 solutions/solution3-decorator-registry/test_local.py \
  POST /account/list --body '{"query":"test"}'
```

Each harness constructs an API Gateway REST API event and calls the same
`lambda_handler` entry point that a deployed Lambda integration would invoke.
See each solution's README for its contract, limitations, and smoke cases.
