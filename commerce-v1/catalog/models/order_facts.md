---
kind: model
name: order_facts
source: local
table: order_facts
columns:
  - name: order_id
    type: BIGINT
    nullable: false
  - name: customer_id
    type: BIGINT
    nullable: false
  - name: invoice_date
    type: DATE
    nullable: false
  - name: status
    type: VARCHAR
    nullable: false
  - name: is_test
    type: BOOLEAN
    nullable: false
  - name: gross_cents
    type: NUMERIC
    nullable: false
  - name: net_cents
    type: NUMERIC
    nullable: false
  - name: contains_widget
    type: VARCHAR
    nullable: false
  - name: is_production
    type: BOOLEAN
    nullable: false
primary_key: [order_id]
---
One prepared row per order. Refund sums and whole-order WIDGET membership are prepared in Python before sutura runs. Fixed synthetic snapshot; no historical as-of engine is implemented.
