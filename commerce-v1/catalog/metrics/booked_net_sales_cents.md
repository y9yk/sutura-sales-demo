---
kind: metric
name: booked_net_sales_cents
model: order_facts
measure:
  simple: { aggregate: sum, column: net_cents }
required_filters:
  - equals: { column: status, value: paid }
  - is_true: { column: is_production }
time_column: invoice_date
grains: [month, day]
dimensions:
  - name: region
    column: region
    via: order_customer
    values: [East, West]
  - name: contains_widget
    column: contains_widget
    values: ['yes', 'no']
anchor:
  range:
    start: 2026-10-01
    end: 2026-11-01
  value: 37500
audience: open
---
Version 1: paid, non-test invoice cohort. Integer USD cents except order count. All refunds known in this fixed fixture have already been subtracted in net_cents. This preparation is our work, not a sutura-generated refund policy.
