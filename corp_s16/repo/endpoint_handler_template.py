from typing import Any
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from decimal import Decimal

import sql_builder



TZ_TH = timezone(timedelta(hours=7))  # Thai time, no daylight saving: every datetime becomes this on the way in and out


# ============ guard ============
def single_row(rows: list[dict]) -> dict:
        if len(rows) == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        if len(rows) > 1:
            raise RuntimeError(f"Expected 1 row, got {len(rows)}")
        return rows[0]


SUPPORTED_LANGUAGES = (None, "TH", "EN")


def require_rows(rows: list[dict], detail: str) -> list[dict]:
    if len(rows) == 0:
        raise HTTPException(status_code=404, detail=detail)
    return rows


def require_language(language: str):
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language!r}")
    return language


MART_SUBTYPES = {
    "CURRENT": "CURRENT",
    "SAVINGS": "SAVING",
    "TERM":    "TERM",
}


SUPPORTED_SUBTYPES = tuple(MART_SUBTYPES)


API_SUBTYPE = {}
for api, mart in MART_SUBTYPES.items():
    API_SUBTYPE[mart] = api


def require_subtype(sub_type: str):
    if sub_type not in SUPPORTED_SUBTYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported accountSubType: {sub_type!r}")
    return sub_type


# ============ transform ============
def select_by_language(th_value, en_value, language):
    if language is None or language == "TH":
        requested, fallback = th_value, en_value
    elif language == "EN":
        requested, fallback = en_value, th_value
    else:
        raise ValueError(f"Unsupported language: {language!r}")

    return requested or fallback or ""


def to_api_subtype(mart_value):
    # the mart's value -> the API's, for the  response
    return API_SUBTYPE.get(mart_value, mart_value)


def athena_to_th_iso(value):
    """
    Athena's timestamptz text ("2026-10-04 17:10:00.000000 UTC") 
    -> ISO in Thai time ("2026-10-05T00:10:00+07:00")
    """

    if value is None:
        return None

    return (
        datetime
        .strptime(value, "%Y-%m-%d %H:%M:%S.%f UTC")    # read the numbers; "UTC" only matched, tzinfo stays None
        .replace(tzinfo=timezone.utc)                   # say the numbers are UTC (Athena always sends UTC)
        .astimezone(TZ_TH)                              # the same instant, in Thai time
        .isoformat(timespec="seconds")                  # to text, down to seconds
    )


def iso_to_th_iso(value):
    """
    ISO 8601 with any offset ("2026-10-01T00:00:00+07:00")
    -> ISO in Thai time, down to seconds
    """

    if value is None:
        return None

    return (
        datetime
        .fromisoformat(value)
        .astimezone(TZ_TH)
        .isoformat(timespec="seconds")
    )

    
TWO_PLACES = Decimal("0.01")    

def to_amount(value: Decimal | str | None) -> Decimal:

    if value is None or value == "":
        return Decimal("0.00")

    if isinstance(value, float):
        raise TypeError(f"Amount must not be a float: {value!r}")

    return Decimal(value).quantize(TWO_PLACES)


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


    def bind_parameters(self) -> dict:
        return {}

         
    def execute_query(self, query_parameters):

        query, values = sql_builder.bind(sql_builder.load_query(self.query_path), query_parameters)

        return self.connector.execute(query, values)


    def build_mapping(self, query_result: Any):
        return {"items": query_result}


    