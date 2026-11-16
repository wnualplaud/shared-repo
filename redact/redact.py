"""Redact / restore real names in a copy of a folder, by a rules file.

The engine holds no names; every name lives in the rules file, which stays
private. Only this engine may be shared.

    python redact.py redact  <rules.py> <dir>   # real -> sample names (content and file names)
    python redact.py restore <rules.py> <dir>   # sample -> real
    python redact.py check   <rules.py> <dir>   # exit 1 if any real name is left

A rules file is a Python file that defines:

    CONTENT_MAP  = [(real_regex, sample_template, sample_regex, real_template), ...]
                   applied in order on redact, and in the same order on restore
    REAL_PATTERN = re.compile(...)     # any hit after redact fails `check`
    ANCHOR       = "rdx"               # every sample name contains it; it must not
                                       # appear in the source before redact
    FOLDER_MAP   = {"real": "sample"}  # optional: folder names to rename
    FOLDER_PARENT = "handlers"         # optional: only folders under a parent of this name

Files are written with LF line ends whatever the platform.
"""
import importlib.util
import re
import sys
from pathlib import Path


def load_rules(path: Path):
    spec = importlib.util.spec_from_file_location("redact_rules", path)
    rules = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules)
    for name in ("CONTENT_MAP", "REAL_PATTERN", "ANCHOR"):
        if not hasattr(rules, name):
            sys.exit(f"{path}: {name} is not defined")
    rules.FOLDER_MAP = getattr(rules, "FOLDER_MAP", {})
    rules.FOLDER_PARENT = getattr(rules, "FOLDER_PARENT", None)
    return rules


def skip(p: Path) -> bool:
    return "__pycache__" in p.parts or ".git" in p.parts


def text_files(root: Path):
    """Every file that reads as UTF-8 text, whatever its suffix (.env, .example, .sh ...)."""
    for p in root.rglob("*"):
        if not p.is_file() or skip(p):
            continue
        try:
            p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield p


def apply_map(rules, text: str, forward: bool) -> str:
    for real_re, sample_t, sample_re, real_t in rules.CONTENT_MAP:
        text = re.sub(real_re, sample_t, text) if forward else re.sub(sample_re, real_t, text)
    return text


def folders(rules, root: Path):
    for d in root.rglob("*"):
        if d.is_dir() and not skip(d) and (rules.FOLDER_PARENT is None or d.parent.name == rules.FOLDER_PARENT):
            yield d


def rewrite(rules, root: Path, forward: bool):
    for p in text_files(root):
        text = p.read_text(encoding="utf-8")
        new = apply_map(rules, text, forward)
        if new != text:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(new)
            print(f"  edited {p.relative_to(root)}")

    for p in list(root.rglob("*")):   # list() first: renaming while walking
        if not p.is_file() or skip(p):
            continue
        name = apply_map(rules, p.name, forward)
        if name != p.name:
            p.rename(p.with_name(name))
            print(f"  renamed {p.relative_to(root)} -> {name}")

    renames = rules.FOLDER_MAP if forward else {v: k for k, v in rules.FOLDER_MAP.items()}
    for d in sorted(folders(rules, root), key=lambda d: -len(d.parts)):   # deepest first
        if d.name in renames:
            d.rename(d.with_name(renames[d.name]))
            print(f"  renamed {d.relative_to(root)} -> {renames[d.name]}")


def check(rules, root: Path) -> int:
    hits = []
    for p in text_files(root):
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if rules.REAL_PATTERN.search(line):
                hits.append(f"{p.relative_to(root)}:{n}: {line.strip()}")
    for p in root.rglob("*"):
        if skip(p):
            continue
        renamable = p.is_dir() and p.name in rules.FOLDER_MAP and (
            rules.FOLDER_PARENT is None or p.parent.name == rules.FOLDER_PARENT)
        if rules.REAL_PATTERN.search(p.name) or renamable:
            hits.append(f"name: {p.relative_to(root)}")
    for h in hits:
        print(h)
    print(f"real-name hits: {len(hits)}")
    return 1 if hits else 0


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in {"redact", "restore", "check"}:
        sys.exit(__doc__)
    mode, rules, root = sys.argv[1], load_rules(Path(sys.argv[2])), Path(sys.argv[3])
    if mode == "check":
        sys.exit(check(rules, root))
    if mode == "redact":
        clash = [str(p) for p in text_files(root) if rules.ANCHOR in p.read_text(encoding="utf-8")]
        if clash:
            sys.exit(f"anchor '{rules.ANCHOR}' already present, refusing to redact: {clash}")
    rewrite(rules, root, forward=(mode == "redact"))


if __name__ == "__main__":
    main()
