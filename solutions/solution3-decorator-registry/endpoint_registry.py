# endpoint_registry.py

ENDPOINTS = [
    {
        "method": "POST",
        "path": "/account/list",
        "module": "modules.account_list.endpoint",
        "query": "modules/account_list/query.sql",
        "backend": "athena",
    },
    {
        "method": "POST",
        "path": "/account",
        "module": "modules.account.endpoint",
        "query": "modules/account/query.sql",
        "backend": "athena",
    },
    {
        "method": "POST",
        "path": "/balance",
        "module": "modules.balance.endpoint",
        "query": "modules/balance/query.sql",
        "backend": "athena",
    },
    {
        "method": "POST",
        "path": "/transaction",
        "module": "modules.transaction.endpoint",
        "query": "modules/transaction/query.sql",
        "backend": "dynamo",
    },
    {
        "method": "POST",
        "path": "/statement",
        "query": "modules/statement/query.sql",
        "backend": "athena",
    },
]
