# Serving API

The image build context: the app's code, `Dockerfile`, `requirements.txt`.

## Configuration

Environment variables the app reads. Real values are set per
environment at deploy time; none are stored here.

| Variable | Meaning | Default |
|---|---|---|
| `APP_ENV` | environment name; fills `<env>` in the table names the queries use | required |
| `ATHENA_DATABASE` | Athena database the queries run in | required |
| `ATHENA_OUTPUT_LOCATION` | S3 URI where Athena writes query results | required |
| `ATHENA_WORKGROUP` | Athena workgroup the queries run in | required |
| `ATHENA_QUERY_TIMEOUT_SECONDS` | how long to wait for a query before giving up | `20` |
