---
kind: caveat
name: fixed_snapshot_and_cents
about:
  - { metric: booked_net_sales_cents }
  - { metric: paid_order_value_cents }
---
Monetary output is integer USD cents. Refund totals and whole-order product membership are prepared before the runtime runs. No live source or time-travel mechanism is present.
