---
kind: relationship
name: order_customer
origin:
  model: order_facts
  column: customer_id
target:
  model: customers
  column: customer_id
join_type: many_to_one
---
Each prepared order maps to one customer.
