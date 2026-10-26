# endpoint_registry.py

ENDPOINTS = [
    {
        "method": "POST",
        "path": "/rdx_ep1",
        "handler": "rdx_ep1.endpoint",
        "enabled": True,
    },
    {
        "method": "POST",
        "path": "/rdx_ep2",
        "handler": "rdx_ep2.endpoint",
        "enabled": True,
    },
    {
        "method": "POST",
        "path": "/rdx_ep3",
        "handler": "rdx_ep3.endpoint",
        "enabled": True,
    },
    {
        "method": "POST",
        "path": "/rdx_ep4",
        "handler": "rdx_ep4.endpoint",
        "enabled": True,
    },
    {
        "method": "POST",
        "path": "/rdx_ep5",
        "handler": "rdx_ep5.endpoint",
        "enabled": False,
    },
]
