import argparse, json
import lambda_function

def make_event(method, path, headers=None, body=None):
    return {
        "path": path,
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body) if body is not None else None,
        "requestContext": {"requestId": "test-1"},
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("method")
    parser.add_argument("path")
    parser.add_argument("--body")            # JSON string
    parser.add_argument("--header", action="append", default=[])  # key=value, ใส่ซ้ำได้หลายอัน
    args = parser.parse_args()

    headers = dict(h.split("=", 1) for h in args.header)
    body = json.loads(args.body) if args.body else None

    event = make_event(args.method, args.path, headers=headers, body=body)
    print(lambda_function.lambda_handler(event, None))
