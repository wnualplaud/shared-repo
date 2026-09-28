MOCK_RESULT = [
    {
        "account_id": "mock-account-001",
        "account_name": "Example Account",
        "balance": 1250.50,
        "currency": "THB",
    }
]


def execute(sql: str, parameters: list) -> list[dict]:
    return [item.copy() for item in MOCK_RESULT]
