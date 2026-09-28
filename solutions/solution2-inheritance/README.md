# Solution 2 -- Operation Extension

This solution proves a concrete `APIOperation` that owns the standard
endpoint lifecycle and permits custom behavior without requiring an
otherwise empty subclass for every endpoint.

Current invariants:

- Powertools remains responsible for transport routing, middleware, and
  proxy response serialization.
- A generated route callback creates a fresh operation instance for each
  invocation.
- A routine endpoint uses the concrete `APIOperation` directly when its
  endpoint definition has no `module` field.
- An endpoint needing custom behavior declares a module that exports
  `OPERATION_CLASS`.
- A declared module must import successfully and provide that export;
  broken declarations surface during route registration rather than
  silently falling back to the default.
- SQL templates and reusable clients may be initialized at module scope;
  request payloads and endpoint instances remain invocation-scoped.

The current implementation is a dispatch and inheritance proof. Its
query and mapping methods return diagnostic data; they do not yet read
SQL, bind request parameters, call a connector, or implement an auth
policy. Those behaviors are outside this proof and must not be inferred
from a successful `200` response.

## Proven Dispatch Matrix

| Route | Operation selection | Method behavior |
|---|---|---|
| `POST /statement` | Concrete default | Base query and base mapping |
| `POST /account/list` | Custom class | Base query and custom mapping |
| `POST /account` | Custom class | Custom query and base mapping |
| `POST /transaction` | Custom class | Custom query and custom mapping |
| `POST /balance` | Custom class | Full handle override |

The `/statement` definition intentionally has no `module`. An
`endpoint.py` file may exist beside its query resource, but file presence
does not select custom behavior; only the explicit registry field does.

From the repository root, the smoke commands use the same Lambda and Powertools
resolution path as the other local solution:

```sh
python3 solutions/solution2-inheritance/test_local.py POST /statement \
  --body '{"query":"test"}'
python3 solutions/solution2-inheritance/test_local.py POST /account/list \
  --body '{"query":"test"}'
python3 solutions/solution2-inheritance/test_local.py POST /account \
  --body '{"query":"test"}'
python3 solutions/solution2-inheritance/test_local.py POST /transaction \
  --body '{"query":"test"}'
python3 solutions/solution2-inheritance/test_local.py POST /balance \
  --body '{"query":"test"}'
```

The resolver was also checked directly for both policy branches:

```text
definition without module -> APIOperation
declared missing module    -> ModuleNotFoundError surfaces
```

Research findings, source references, and the candidate mechanisms to
discuss are recorded in
[`operation-extension-research.md`](operation-extension-research.md).
The repository-level comparison is maintained in
[`../../README.md`](../../README.md).

## Evolution Policy

This directory is the continuing implementation line for the operation-
extension intent. Enhancements that preserve that intent should replace
the proof in place and remain inspectable through Git history. Create
another solution directory only for a meaningfully different design that
must remain runnable side by side, not for the next revision of this one.

Dependencies remain shared through the repository root `requirements.txt` and
`.venv`.
