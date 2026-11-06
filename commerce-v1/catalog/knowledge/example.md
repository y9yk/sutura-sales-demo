---
kind: example
name: monthly_net_sales
asked: [show order-cohort net sales for October 2026]
question:
  metrics: [booked_net_sales_cents]
  grain: month
  range: { start: 2026-10-01, end: 2026-11-01 }
---
Request the agreed metric by a half-open invoice period. The example specifies query structure, not an expected numeric answer.
