from typing import Any
from functools import cache
from pathlib import Path

from fastapi import HTTPException

import os

APP_ENV = os.environ["APP_ENV"]



@cache
def _load_query(query_path: Path) -> str:    
    return query_path.read_text(encoding="utf-8").replace("<env>", APP_ENV)


def single_row(rows: list[dict]) -> dict:
        if len(rows) == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        if len(rows) > 1:
            raise RuntimeError(f"Expected 1 row, got {len(rows)}")
        return rows[0]


SUPPORTED_LANGUAGES = (None, "TH", "EN")


def require_language(language: str):
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language!r}")
    return language


def select_by_language(th_value, en_value, language):
    if language is None or language == "TH":
        requested, fallback = th_value, en_value
    elif language == "EN":
        requested, fallback = en_value, th_value
    else:
        raise ValueError(f"Unsupported language: {language!r}")

    return requested or fallback or ""



class EndpointHandlerTemplate:

    connector: Any
    query_path: Path

    def __init__(self, body: dict):
        self.body = body


    def authenticate(self):
        pass


    def handle(self):

        query_parameters = self.bind_parameters()
        query_result = self.execute_query(query_parameters)

        return self.build_mapping(query_result)


    def bind_parameters(self) -> list:
        return []

         
    def execute_query(self, query_parameters):

        raw_query = _load_query(self.query_path)

        return self.connector.execute(raw_query, query_parameters)


    def build_mapping(self, query_result: Any):
        return {"items": query_result}


    