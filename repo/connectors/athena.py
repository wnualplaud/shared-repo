import os
import time
from functools import cache

import boto3


ATHENA_DATABASE = os.environ["ATHENA_DATABASE"]
ATHENA_OUTPUT_LOCATION = os.environ["ATHENA_OUTPUT_LOCATION"]
ATHENA_WORKGROUP = os.environ["ATHENA_WORKGROUP"]

POLL_INTERVAL_SECONDS = 0.5

# Stay under API Gateway's 29-second integration timeout.
MAX_WAIT_SECONDS = int(os.environ.get("ATHENA_QUERY_TIMEOUT_SECONDS", 20))


@cache
def _client():
    return boto3.client("athena")


def _to_literal(value) -> str:
    if isinstance(value, bool):
        raise TypeError("Unsupported parameter type: bool")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    raise TypeError(f"Unsupported parameter type: {type(value).__name__}")


def _wait_for_query(query_execution_id: str) -> str:
    deadline = time.monotonic() + MAX_WAIT_SECONDS

    while True:
        status = _client().get_query_execution(
            QueryExecutionId=query_execution_id
        )["QueryExecution"]["Status"]
        state = status["State"]

        if state == "SUCCEEDED":
            return state
        if state in ("FAILED", "CANCELLED"):
            raise RuntimeError(
                f"Athena query {state}: {status.get('StateChangeReason')}"
            )
        if time.monotonic() > deadline:
            _client().stop_query_execution(QueryExecutionId=query_execution_id)
            raise TimeoutError(f"Athena query timed out after {MAX_WAIT_SECONDS}s")

        time.sleep(POLL_INTERVAL_SECONDS)


def _fetch_rows(query_execution_id: str) -> list[dict]:
    result_rows = _client().get_query_results(
        QueryExecutionId=query_execution_id
    )["ResultSet"]["Rows"]

    if not result_rows:
        return []

    # The first row holds column names; NULL cells have no VarCharValue.
    header = [cell.get("VarCharValue") for cell in result_rows[0]["Data"]]
    return [
        dict(zip(header, [cell.get("VarCharValue") for cell in row["Data"]]))
        for row in result_rows[1:]
    ]


def execute(sql: str, parameters: list) -> list[dict]:
    literals = [_to_literal(value) for value in parameters]

    request = {
        "QueryString": sql,
        "WorkGroup": ATHENA_WORKGROUP,
        "QueryExecutionContext": {"Database": ATHENA_DATABASE},
        "ResultConfiguration": {"OutputLocation": ATHENA_OUTPUT_LOCATION},
    }

    # Athena rejects an empty ExecutionParameters list.
    if literals:
        request["ExecutionParameters"] = literals

    query_execution_id = _client().start_query_execution(**request)["QueryExecutionId"]
    _wait_for_query(query_execution_id)

    return _fetch_rows(query_execution_id)
