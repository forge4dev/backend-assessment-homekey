# Homekey Backend Assessment

## Context

When a property goes on the market, buyers submit offers on our website. A popular listing can receive multiple offers in a few hours.

The codebase uses:
- **Flask** for the API layer
- **MongoDB** as the primary database
- **Redis** for caching
- **A multi-agent AI system** for property valuation

---

## Task 1

**Format:** code + explanation

A listing received a burst of concurrent offer submissions. Under load, you observe:
- Duplicate offers appearing in the database for the same buyer
- MongoDB CPU spiking to 87%
- Stale offer lists being served to the seller's dashboard

There are multiple bugs in file `app/services/offer_service.py`. Fix only the most critical one. 

For the other ones, explain
1. What the bug is
2. What it causes under load
3. How you would fix it (code or pseudocode)
4. Why you chose not to fix it first

The constraint is intentional. We want to see how you triage.

---

## Task 2

**Format:** explanation

A colleague proposes storing offers embedded in the property document:

```json
{
  "_id": "property_abc",
  "address": "123 Main St",
  "asking_price": 1200000,
  "offers": [
    { "buyer_id": "u1", "amount": 1150000, "status": "pending", "submitted_at": "2025-11-01T10:00:00Z", ... },
    { "buyer_id": "u2", "amount": 1180000, "status": "accepted", "submitted_at": "2025-11-01T11:30:00Z", ... }
  ]
}
```

This works fine in staging.

1. What can break in production, and why?
2. Propose an alternative schema.
3. There is no schema that solves everything. What does your alternative make harder compared to the embedded approach?

---

## Task 3

**Format:** code + explanation

Review `get_comparable_sales` method in `app/services/valuation_service.py`. 
Leave comments on any issue you'd flag and order them by priority as we scale up.

---

## Task 4

**Format:** explanation

An AI system routes user requests through an Orchestrator that manages a stateful workflow. Each downstream agent runs a multi-step LLM chain. Agents call external tools through a service layer. Some workflows pause mid-execution waiting for user input.

In production you observe p99 response times exceeding 50 seconds, occasional cascading failures when a downstream agent is slow, and paused workflows that are never cleaned up.

You have 1 week before a product demo.

1. What reliability problems would you expect in a system like this?
2. How would you prioritize fixing them, and what does your prioritization give up?
3. Given all of the knowledge you know, provide a 1-week timeline of your implementation details and how it will impact the users.
4. What makes the tool service layer harder to make resilient than a typical stateless API?
