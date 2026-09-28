from functools import cache

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

_serializer = TypeSerializer()
_deserializer = TypeDeserializer()


@cache
def _client():
    return boto3.client("dynamodb")


def execute(sql: str, parameters: list) -> list[dict]:
    typed_parameters = [_serializer.serialize(value) for value in parameters]

    response = _client().execute_statement(
        Statement=sql,
        Parameters=typed_parameters,
    )

    return [
        {name: _deserializer.deserialize(value) for name, value in item.items()}
        for item in response["Items"]
    ]
