---
kind: model
name: customers
source: local
table: customers
columns:
  - name: customer_id
    type: BIGINT
    nullable: false
  - name: region
    type: VARCHAR
    nullable: false
primary_key: [customer_id]
---
One row per synthetic customer. Region is East or West.
