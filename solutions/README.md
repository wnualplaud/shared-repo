# Solutions

This directory keeps runnable implementation variants side by side so
their contracts and tradeoffs can be compared without checking out an
older Git revision.

- `solution1-module-functions/` is the config-registered, module-owned
  function implementation baseline.
- `solution2-inheritance/` contains the exploratory concrete `APIOperation`
  inheritance implementation.
- `solution3-decorator-registry/` contains the implemented design proof
  that binds decorated functions to a generated endpoint handler. Its
  Python decorator background is kept as a local side read, separate
  from the architecture decision record.

See the [repository README](../README.md) for the standalone comparison
and setup instructions.

All solutions use the virtual environment and dependency manifest at
the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Solution 1 currently keeps runnable code below its `src/` directory,
while the Solution 2 scaffold is directly below its solution directory.
This comparison workspace is not itself a Lambda deployment root; the
selected solution's final package boundary remains to be normalized.
