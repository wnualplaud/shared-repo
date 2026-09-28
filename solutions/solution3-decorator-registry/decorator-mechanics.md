# Python Decorator Mechanics

This is side reading for Solution 3. It explains the Python language
mechanism used by the endpoint handler registry; it is not an implementation
contract or another solution candidate.

## Stage 1 --- Function Decoration Rebinds a Name

Start with syntax only:

```python
@decorator
def target():
    pass
```

Python defines this approximately as:

```python
def target():
    pass


target = decorator(target)
```

### Language Facts

For this function-decorator syntax:

1. The `def` statement creates the original function object.
2. Defining the function does not execute its body.
3. Python invokes the decorator callable with that function object as one
   argument.
4. The initial object passed into the decorator is therefore a function,
   regardless of whether the decorator parameter has a type annotation.
5. Python binds the value returned by the decorator call to the name
   `target`.
6. Python does not require that returned value to be a function or to be
   the original function.
7. If a Python decorator function finishes without an explicit `return`,
   it returns `None`, which is then bound to `target`.
8. After decoration, `target` may therefore refer to the original
   function, another function, or a value of another type.
9. For the direct `@decorator` form, Python supplies the decorated
   function as one call argument. The decorator callable must be able to
   accept that argument; a callable that accepts no arguments cannot be
   used in this direct form.

This has the same rebinding shape as an assignment such as `i = i + 1`:
the right-hand side reads the previous value, computes a result, and the
result is assigned back to the same name. The original function object
is not modified merely by this syntax; the name is rebound to the
decorator's result.

### Current Interpretation

If callers are expected to continue using `target()`, the returned value
will normally be a function or another callable so the name preserves
that callable contract. This is a usage expectation, not a Python type
requirement. Even when the returned value is a function, Stage 1 does not
assume whether it is the original function or a different function.

At this stage, do not introduce decorator factories, closures, or
wrappers. The syntax checkpoint is only:

```text
@decorator + def target
is approximately
target = decorator(target)
```

### Stage 1 Summary

```text
original function object
-> passed into decorator
-> decorator returns a value
-> that value is bound back to the original name
```

The input object is known to be the function produced by `def`. The
returned value deliberately remains open: it may be the original
function, a different function, or another kind of object.

## Stage 2 --- Direct and Configured Decorator Call Shapes

The direct form:

```python
@decorator
def target():
    pass
```

has this approximate call shape:

```python
target = decorator(target)
```

Its two conceptual phases are:

```text
decorate -> bind
```

Here, `decorator` is the actual decorator. It receives the original
function and returns the value that Python binds to `target`.

The configured form:

```python
@decorator(config)
def target():
    pass
```

has a different call shape:

```python
target = decorator(config)(target)
```

Separating the calls makes the two scopes visible:

```python
actual_decorator = decorator(config)
replacement = actual_decorator(target)
target = replacement
```

Its three conceptual phases are:

```text
configure -> decorate -> bind
```

The outer function therefore has a different contract in each form:

```text
direct form:
decorator(target) -> replacement

configured form:
decorator(config) -> actual decorator
actual decorator(target) -> replacement
```

The configured form is not merely the direct implementation with one
more required parameter. The outer call now receives configuration and
must first return the callable that performs decoration. The shared rule
is that the final decorator callable receives `target` and returns the
value that Python binds back to that name.

Stage 2 still makes no claim about whether the replacement is the
original function or a new function, and it does not introduce call-time
wrapping behavior.

### Stage 2 Summary

Let `D` mean the actual decorator callable that receives `target`.

For the direct form:

```python
D = decorator
```

This is an assignment. `decorator` is an existing function object, and
the same object is assigned to `D`; no function call occurs here.

For the configured form:

```python
D = decorator(config)
```

This includes a function call before the assignment. Python first calls
`decorator(config)`, then assigns that call's returned value to `D`.
The returned value is the actual decorator that will receive `target`.

After `D` has been selected, both forms use the same remaining equation:

```python
replacement = D(target)
target = replacement
```

In the configured form, the outer function has changed role: it accepts
configuration and returns `D`. The decorator role from the direct form
has moved to the second call. This describes role equivalence; `D` does
not need to be the same function object in both forms.

## Stage 3 --- Factory and Decorator Responsibilities

Stage 2 established the two calls in the configured form:

```python
D = decorator(config)
replacement = D(target)
```

These calls operate with different available context:

- The decorator factory, `decorator(config)`, has the supplied
  configuration but has not received `target`.
- The actual decorator, `D(target)`, receives the object being decorated
  and can return its replacement.

Python does not restrict the factory to one responsibility. While it is
running, it may validate values, mutate state, register configuration,
write logs, or perform other side effects. Its language-level requirement
for this use is only to return a callable that can serve as `D`.

### Current Interpretation

Although the factory can perform arbitrary work, its main useful
responsibility in this context is preparing, configuring, or selecting
the actual decorator. Unrelated registration, logging, or other side
effects usually add little value at this level and make execution timing
less obvious.

Work concerning the decorated `target` naturally belongs to the actual
decorator because the factory has not received `target` yet. Factory work
that remains useful is normally limited to concerns such as validating or
normalizing its configuration and constructing the actual decorator.

### Stage 3 Summary

```text
decorator factory:
configuration -> prepare actual decorator -> D

actual decorator:
target -> perform decoration -> replacement
```

The first line is a responsibility guideline, not a Python restriction.
The factory is technically free to do more work, but the available
context gives most of that work little reason to live there.

## Stage 4 --- Classifying the Decorator Result

The actual decorator performs the decoration step:

```python
replacement = actual_decorator(target)
target = replacement
```

Its result can first be classified by object identity rather than by its
internal implementation.

### Category 1: Return the Original Target

```python
replacement is target
```

The decorator returns the same object it received. Before returning, it
may do nothing, register the target, attach information to it, or perform
another side effect. Those actions do not change this category as long
as the returned object is still `target`.

### Category 2: Return a Different Object

```python
replacement is not target
```

The name is rebound to another object. That replacement may be:

- a newly created function, such as a wrapper;
- a different function that already exists; or
- another kind of object, whether callable or non-callable.

Calling this category "modifying the function" would be imprecise. The
original function does not need to be modified; the decorator may simply
return a different object and cause the original name to be rebound.

### Stage 4 Frame

```text
actual_decorator(target)
|
|-- Category 1: return the same target object
|
`-- Category 2: return a different object
    |-- another function
    `-- another kind of object
```

This frame extends the open result identified in Stage 1. Later stages
can examine the behavior inside each category without changing the
language-level classification.

## Stage 5 --- Reduce a Configured Decorator to the Base Case

When reading a configured decorator:

```python
@dec(args)
def target():
    pass
```

first find the callable returned by `dec(args)`. Let `D` represent that
returned callable:

```python
D = dec(args)
```

`D` is the actual decorator. The configured form can now be reduced to
the direct base case:

```python
@D
def target():
    pass
```

which has the Stage 1 equation:

```python
target = D(target)
```

The complete reading model is therefore:

```python
D = dec(args)
target = D(target)
```

When inspecting `dec`, the immediate question is what callable it
returns as `D`. That callable does not need to be named
`actual_decorator` in the source; the name describes its role.

## Sources

- Python Language Reference, *Function definitions*:
  https://docs.python.org/3/reference/compound_stmts.html#function-definitions
- Python Glossary, *decorator*:
  https://docs.python.org/3/glossary.html#term-decorator
- Python Tutorial, *Defining Functions*:
  https://docs.python.org/3/tutorial/controlflow.html#defining-functions
