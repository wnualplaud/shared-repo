# Operation Extension Research

## Question

The prototype needs a standard request-to-response flow that can run an endpoint
from registration data and a query resource. A routine endpoint should
not need an otherwise empty Python class or implementation file. An
endpoint with exceptional behavior must still be able to replace part
or all of that standard flow.

The research question is therefore not merely how to import an optional
class. It is how established systems separate these concerns:

1. selecting the default or custom implementation;
2. supplying endpoint-specific data such as backend and query resource;
3. extending behavior when the default is insufficient;
4. discovering and registering endpoints or plugins.

Registration/discovery is a separate axis from behavior extension. A
central registry, one-definition-per-file layout, and package discovery
could all use the same operation-extension mechanism.

## Confirmed Constraints

- A routine endpoint may contain only configuration and `query.sql`.
- The standard flow must be concrete and runnable, not an abstract
  interface whose methods only raise or return `None`.
- A custom Python class should be required only when an endpoint needs
  behavior outside the standard flow.
- Powertools remains the transport router. The operation abstraction is
  an application-level extension point behind its route callback.
- Missing optional customization may select a default. A declared but
  broken customization should fail clearly rather than fall back
  silently.
- Automatic plugin discovery is not required merely to make the custom
  operation class optional.

## Findings

| ID | Mechanism | Evidence | Consequence for the prototype |
|---|---|---|---|
| F1 | Concrete default class with optional custom subclass | Python `json` uses `JSONEncoder` when `cls` is not supplied; FastAPI uses `APIRoute` as the default `route_class` and accepts a subclass when customization is needed. [R1][R2][R3] | Routine endpoints need no subclass. Inheritance remains available, but only custom endpoints exercise it. |
| F2 | Framework-generated subclass | Celery turns a decorated function into a generated `Task` subclass and permits a custom task base. [R4][R5] | The framework could generate a subclass per endpoint, but an empty generated subclass adds class identity without adding behavior. |
| F3 | Conditional default implementation | Spring Boot auto-configuration supplies a bean only when the application has not supplied one. [R6] | This validates default-unless-overridden resolution, but reproducing a dependency-injection container would be disproportionate here. |
| F4 | Configured factory or strategy | Python logging configuration uses built-in construction by context and accepts a user-defined factory through the special `()` key. [R7] | The framework can inject functions for the provisional authorize, execute, and response-mapping stages, but should not invent additional strategy slots without evidence. |
| F5 | Resource-driven execution with optional typed interface | MyBatis can execute a mapped SQL statement directly by statement ID; a Mapper interface is an optional, cleaner and type-safe binding. [R8][R9] | A query resource can drive the default path without a per-endpoint class. The Mapper interface is evidence for an optional typed facade, not for custom inheritance. |
| F6 | Package resource loading | `importlib.resources` reads non-Python resources associated with a module or package. [R10] | Resource loading is a supporting mechanism beneath F4/F5, not an operation-extension candidate. A routine endpoint need not have a Python module merely to locate its SQL resource. |
| F7 | Plugin discovery is independent | Python packaging documents naming conventions, namespace packages, and package metadata as three plugin-discovery approaches. [R11] | Discovery can remove a central registration index, but it is shared infrastructure rather than an operation-extension candidate and does not by itself isolate deployment impact. |

## Finding Review Status

| Finding | Status | Interpretation |
|---|---|---|
| F1 | Closed | Validates Solution 2's existing custom-or-default class selection; it is evidence for that solution, not another candidate. |
| F2 | Closed | Validates a distinct generated-operation candidate; its first version binds named stage overrides or one custom handle to a generated subclass. |
| F3 | Closed | Treat as a shared resolution policy, not a standalone implementation candidate. |
| F4 | Closed | Strategy injection is a valid binding option for the provisional base stages; a whole-operation factory remains only a deferred escape hatch. |
| F5 | Closed | Supports a resource-driven default path, but this design keeps response shaping in Python instead of adopting a declarative result-mapping language. |
| F6 | Closed | Treat resource loading as shared infrastructure usable by every candidate; defer package-resource versus explicit-path syntax to the packaging design. |
| F7 | Closed | Preserve discovery as a deferred registration mechanism for self-contained endpoints; do not treat it as a sibling solution or as deployment isolation. |

### F1 Review --- Concrete Default Class with Optional Subclass

Python `json`, FastAPI, and the current Solution 2 scaffold share the
same core mechanism: choose a class object, use a concrete default when
no customization is supplied, then instantiate the selected class. They
differ only in where the optional class comes from:

| System | Custom class source |
|---|---|
| Python `json` | Function parameter `cls` |
| FastAPI | Constructor parameter `route_class` |
| Current Solution 2 scaffold | Optional `module.OPERATION_CLASS` attribute |
| Possible explicit contract | Endpoint configuration or an explicitly named operation module |

F1 therefore does not add a new architecture. It validates the
direction already present in Solution 2:

```text
resolve custom or default class
-> instantiate the selected class
-> run its operation contract
```

The remaining Solution 2 work is not to prove this selection pattern.
It is to remove the unconditional endpoint-module import if resource-only
endpoints are allowed, make `APIOperation` a usable default, and validate
that an explicitly supplied custom class satisfies the operation class
contract.

### F2 Review --- Framework-Generated Subclass

Celery demonstrates that function-based authoring and a class-based
runtime can coexist: a decorator registers a function and the framework
adapts it to its task-class contract. This validates a distinct
candidate in which module authors supply decorated functions while the
framework creates an `APIOperation` subclass that owns the registered
sequence.

This generated-subclass form is the selected first shape for Solution 3.
Keeping decorated callbacks inside a concrete operation instance is a
separate composition variant; it is deferred because it overlaps with
strategy injection and requires another callback-context contract.

The first version is deliberately narrower than Celery's workflow
model:

```python
@operation.override("map_response")
def map_response(operation, query_result):
    ...


@operation.handle
def handle(operation):
    ...
```

- With no custom `handle`, inherited `APIOperation.handle()` owns the flow
  and named decorators replace only known lifecycle stages.
- With a custom `handle`, that function owns the flow and the framework
  does not automatically run the default sequence as well.
- The decorated function receives the fresh operation instance as its
  request-scoped runtime. It may access state and call inherited or
  overridden methods on that instance.
- Undecorated functions remain ordinary Python helpers and are called
  only by code that names them.
- A generic ordered task registry is deferred because registration order
  alone does not explain where arbitrary functions belong in the
  operation lifecycle.

The generated subclass is therefore an adapter between function-based
authoring and the same class-based runtime used by Solution 2. It does
not introduce a second workflow engine.

### F3 Review --- Conditional Default Implementation

Conditional defaulting defines policy rather than an authoring or
runtime model:

```text
no custom declaration -> use the default implementation
explicit custom declaration -> resolve it successfully or fail clearly
```

It does not determine whether customization is a class, decorated
function sequence, strategy, or factory. Solution 2 and the generated-
operation candidate should both apply this policy at registration time.
This prototype needs only a small explicit resolver for it, not a dependency-
injection container.

## Provisional V1 Base Case

Current endpoint evidence is sufficient to name a mandatory invocation
boundary and a small operation lifecycle without defining a general
workflow language:

```text
framework invocation
-> authenticate
-> operation.handle
   -> bind_parameters
   -> execute
   -> map_response
```

The framework invokes `authenticate()` before every `handle()`. An
endpoint may replace its implementation, including with an explicit
allow policy, but a custom handle cannot bypass the invocation point by
accident. Business authorization that depends on endpoint data may later
remain an operation stage distinct from caller authentication.

`APIOperation.handle()` binds those stages for the default-flow mode.
Endpoint configuration and query resources provide data; Python supplies
endpoint-specific behavior. Current evidence suggests that
`map_response` is endpoint-owned rather than a complete generic default,
and `bind_parameters` may also differ by endpoint. Shared orchestration
does not require every stage to have useful no-code behavior.

A custom `execute()` may still own multiple queries, conditional work,
or other internal steps, so this base case does not require the framework
to model those steps. A custom `handle()` is the explicit escape hatch
when even the broad stage sequence is unsuitable.

Response shaping remains executable Python rather than declarative
mapping configuration. This avoids requiring the project to design, parse,
validate, version, and debug a result-mapping language before real
response variation is understood.

## Post-Decision Pattern Comparison

The selected shape combines established mechanisms rather than copying
one framework contract exactly:

| Design decision | Comparable mechanism | Interpretation |
|---|---|---|
| Fresh operation instance per request | Django class-based views keep independent state per request. [R12] | Request state on the operation instance is conventional. |
| Default flow with overridable methods | Django adapts a class to a callable and delegates through `dispatch()`. [R13] | A base flow plus method overrides is a normal framework boundary. |
| Decorated function receives the operation instance | Celery bound tasks receive their task instance as the first argument. [R4] | Supplying the operation as runtime has precedent; its public surface should remain small. |
| Decorated function becomes generated class behavior | Celery turns a task function into a generated `Task` subclass. [R4] | The generated-subclass adapter is valid, though this combined decorator API remains custom. |
| Named stage registration | pluggy validates hook implementations against named hook specifications. [R14] | Unknown stages and incompatible signatures should fail during registration. |
| Mandatory cross-cutting boundary | Powertools middleware can continue to the next handler or return early and recommends narrow middleware responsibilities. [R15] | Authentication, logging, and error handling should not be confused with query stages. |
| Request data remains invocation-local | AWS recommends reusing clients and connections while avoiding user or event data in execution-environment state. [R16] | Generate classes and reuse clients globally; instantiate the operation per request. |

No reviewed framework recommends this exact two-mode decorator API.
Its individual mechanisms have precedent, while their combination is a
small application framework that must remain explicit and be validated at
registration time.

The first draft should reject duplicate handles, duplicate stage
overrides, unknown stage names, and incompatible callback signatures. In
default-flow mode it should also reject a missing required response
mapper. In custom-handle mode, stage overrides remain callable through
the operation runtime but are not executed automatically.

Parameter validation remains separate from backend parameter encoding.
Athena execution parameters are positional `?` values applied in query
order, while DynamoDB has a different expression model. [R17] The
connector boundary must preserve those backend-specific contracts and
must not interpolate request values with Python string operations.

### F4 Review --- Configured Factory or Strategy

The provisional base case gives strategy injection meaningful
counterparts without inventing finer-grained workflow stages:

```python
APIOperation(
    authorizer=custom_authorizer,
    executor=custom_executor,
    mapper=custom_mapper,
)
```

This is a valid binding alternative to subclass overrides and generated
methods. It stores supplied functions as dependencies of a concrete
operation instead of turning them into class methods. It remains a
distinct runtime choice inside the broader function-supplied design
family, not evidence for additional stages.

The generated-operation candidate binds functions to named lifecycle
stages or to the complete `handle`; it does not infer stage placement
from function order. A factory that constructs an entire operation
remains possible as a deferred escape hatch, but it is not an
architecture candidate without a concrete need for custom construction.

The current scaffold's `query_handler()` and `mapping_handler()` names
are exploratory code and do not yet implement the provisional contract.
In particular, `map_response` describes the accepted broad stage more
directly than `mapping_handler`.

### F5 Review --- Resource-Driven Execution with Optional Interface

MyBatis confirms that a stable engine can execute a query resource
without requiring a handwritten implementation class for every query.
Its full shape is more declarative than this prototype: mapped statements include
parameter and result-mapping metadata, and its optional Mapper interface
is a typed facade over that engine rather than a business-flow override.

This design adopts only the resource-driven base case:

```text
endpoint configuration + query resource
-> default APIOperation lifecycle
```

It does not adopt MyBatis's declarative result-mapping model. Query and
backend configuration remain data, while non-trivial response shaping is
supplied as Python behavior. F5 therefore supports the routine no-class
path but does not determine whether custom behavior is bound through a
subclass, generated operation, or injected function.

### F6 Review --- Package Resource Loading

F6 answers how a query or another non-Python resource is located and
read. It does not answer who owns the operation flow or how an endpoint
customizes that flow, so it is not a separate solution candidate.

For the current base case, resource loading sits beneath F5's default
`execute` stage. F4 may replace that executor, and the subclass or
generated-operation candidates may also use the same loader. A routine
endpoint can therefore point from its registration data directly to a
query resource without an otherwise empty `endpoint.py` or another
Python layer in between.

Whether the project addresses that resource through an importable package and
`importlib.resources` or through an explicit deployment-relative
`query_file` is a later packaging decision. It does not need to be
settled to choose the operation-extension model.

### F7 Review --- Plugin Discovery

F7 can support an endpoint package that registers itself without editing
a central registry. Naming conventions, folder scanning, namespace
packages, or package metadata are possible discovery mechanisms, and any
of them could feed the same F4/F5 operation model.

Discovery is therefore not a sibling solution. It changes how endpoint
definitions enter the registry, not how the resulting operation runs or
is customized. It also removes only the central-file edit: when all
endpoints remain in one Lambda artifact, adding one still rebuilds and
deploys that shared artifact. Independent deployment would additionally
require a deployment-unit and routing design.

The prototype does not need this mechanism to complete the core operation contract.
Keep it with the deferred self-contained-endpoint topic and revisit it
when registry ownership, merge conflicts, or deployment topology makes
the central registry an observed problem.

## Working Solution Index

The earlier research candidates mixed operation models with discovery,
resource-loading, and factory mechanisms. The normalized working index is
summarized in the [repository README](../../README.md):

1. direct module handler;
2. class inheritance;
3. decorator registry and generated operation;
4. strategy injection, currently deferred.

This research note remains the evidence and interpretation record for
F1-F7. In particular, discovery, resource loading, and whole-operation
factories no longer appear as sibling solutions.

## Comparison Questions

Discuss each candidate against the same questions:

| Question | Why it matters |
|---|---|
| What is the smallest artifact for a routine endpoint? | Tests the `config + query.sql` requirement. |
| What must a custom endpoint export? | Defines the authoring contract. |
| When does a bad declaration fail? | Distinguishes safe startup validation from silent fallback. |
| Which values are configuration and which are executable behavior? | Prevents the registry from becoming a programming language. |
| Can the team understand the request path from files alone? | Limits hidden discovery and generated behavior. |
| Does the mechanism solve a current variation or only a hypothetical one? | Controls abstraction cost. |

## Current Boundary

Solution 2 now has a completed dispatch proof. It demonstrates route
wrapping, concrete default selection, explicit custom-module selection,
fresh operation construction, inherited methods, selective overrides,
and a full `handle()` override. A declared missing module also surfaces
instead of silently selecting the default.

The proof deliberately returns diagnostic query and mapping data. It does
not read SQL, bind request parameters, execute connectors, implement an
auth policy, or establish its exploratory `query_handler()` and
`mapping_handler()` names as the final operation vocabulary. Those are
separate implementation and naming decisions.

## References

- **R1.** Python Software Foundation. *`json` - JSON encoder and decoder*. https://docs.python.org/3/library/json.html
- **R2.** FastAPI. *APIRouter class reference*. https://fastapi.tiangolo.com/reference/apirouter/
- **R3.** FastAPI. *Custom Request and APIRoute class*. https://fastapi.tiangolo.com/how-to/custom-request-and-route/
- **R4.** Celery. *Tasks: Custom task classes*. https://docs.celeryq.dev/en/stable/userguide/tasks.html#custom-task-classes
- **R5.** Celery. *Application: Abstract Tasks*. https://docs.celeryq.dev/en/stable/userguide/application.html#abstract-tasks
- **R6.** Spring. *Creating Your Own Auto-configuration*. https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html
- **R7.** Python Software Foundation. *`logging.config` - Logging configuration*. https://docs.python.org/3/library/logging.config.html#user-defined-objects
- **R8.** MyBatis. *Getting started*. https://mybatis.org/mybatis-3/getting-started.html
- **R9.** MyBatis. *Java API: SqlSession*. https://mybatis.org/mybatis-3/java-api.html#sqlsession
- **R10.** Python Software Foundation. *`importlib.resources` - Package resource reading, opening and access*. https://docs.python.org/3/library/importlib.resources.html
- **R11.** Python Packaging Authority. *Creating and discovering plugins*. https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
- **R12.** Django Software Foundation. *Built-in class-based views API*. https://docs.djangoproject.com/en/5.2/ref/class-based-views/
- **R13.** Django Software Foundation. *Base views*. https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/
- **R14.** pluggy. *Specifications and implementation validation*. https://pluggy.readthedocs.io/en/latest/
- **R15.** AWS Lambda Powertools. *REST API event handler middleware*. https://docs.aws.amazon.com/powertools/python/latest/core/event_handler/api_gateway/
- **R16.** Amazon Web Services. *Best practices for working with AWS Lambda functions*. https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
- **R17.** Amazon Web Services. *Use parameterized queries in Amazon Athena*. https://docs.aws.amazon.com/athena/latest/ug/querying-with-prepared-statements.html
