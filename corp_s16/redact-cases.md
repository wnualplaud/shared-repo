# redact cases

One line per rule; after `restore` each line must read as its label says.

env forms of the full names:
- <env>: rdx<env>_tbl1 rdx<env>_tbl2 rdx<env>_db1
- dev: rdxdev_tbl1 rdxdev_tbl2 rdxdev_db1
- sit: rdxsit_tbl1 rdxsit_db1
- uat: rdxuat_tbl1 rdxuat_tbl2 rdxuat_db1
- uatmock: rdxuatmock_tbl1 rdxuatmock_tbl2 rdxuatmock_db1
- prod: rdxprod_tbl2 rdxprod_db1
- lab: rdxlab_tbl1 rdxlab_db1
- ${ENV}: rdx${ENV}_tbl1 rdx${ENV}_db1.rdx_tbl3
- ${env}: rdx${env}_tbl2 rdx${env}_db1

bare table names:
- rdx_tbl3, rdx_tbl1, rdx_tbl2
- suffix in backticks: `_rdx_tbl1`, `_rdx_tbl2`
- file names: rdx_tbl2.table.json rdx_tbl1.items.json rdx_tbl3.insert.sql
- bash array: TABLES=(rdx_tbl2 rdx_tbl1)

organisation and prefix:
- bucket: s3://rdxorg-rdx-uat-share/yourdata-api-mock/iceberg
- role: rdx-uat-ecs-task-role
- upper: RDXBANK
- lower in a name: corp-rdxbank-profiling

endpoints and handlers:
- /rdx_ep1 /rdx_ep2 /rdx_ep3 /rdx_ep4 /rdx_ep5
- rdx_ep1.endpoint rdx_ep2.endpoint rdx_ep3.endpoint rdx_ep4.endpoint rdx_ep5.endpoint
