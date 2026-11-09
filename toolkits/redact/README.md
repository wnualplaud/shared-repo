# toolkits/redact

Reversible redaction of a folder copy: real names are replaced by sample
names before a folder is shared, and put back when it returns.

The engine holds no names. Names live in a rules file, which is kept
private and is not in this repository. The file format is in the
docstring of `redact.py`.

```sh
python redact.py check   <rules.py> <dir>   # list real names still present
python redact.py redact  <rules.py> <dir>   # real -> sample
python redact.py restore <rules.py> <dir>   # sample -> real
```

Notes:

- Every text file (UTF-8) is processed, whatever its suffix; file names
  too, and optionally folder names.
- Files are written with LF line ends.
- `redact` refuses a folder that already contains the anchor (the
  marker every sample name carries), so `restore` stays exact.
