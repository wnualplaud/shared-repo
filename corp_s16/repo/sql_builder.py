import os
import re
from functools import cache
from pathlib import Path
from string import Template


APP_ENV = os.environ["APP_ENV"]

_PARAM = re.compile(r":([A-Za-z_]\w*)")


@cache
def load_query(query_path: Path) -> str:    
    return Template(query_path.read_text(encoding="utf-8")).substitute(env=APP_ENV)


def bind(query: str, params: dict) -> tuple[str, list]:

    values = []

    def to_marks(match):
        
        name = match.group(1)
        if name not in params:
            raise KeyError(f"the query has :{name}, no value given")
        
        value = params[name]

        if isinstance(value, tuple):
            values.extend(value)
            return ", ".join("?" for _ in value)
        
        values.append(value)
        return "?"
    
    return _PARAM.sub(to_marks, query), values