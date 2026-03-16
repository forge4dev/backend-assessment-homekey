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

### Task 1 Response

The most critical bug is a race condition in `submit_offer`, where the code checks for an existing offer using `find_one` before inserting. Under concurrent requests, multiple submissions can pass this check and insert duplicate offers for the same `(property_id, buyer_id)`. I fixed this by enforcing a MongoDB **compound unique index** on `(property_id, buyer_id)` and handling `DuplicateKeyError` during insertion, ensuring atomic deduplication at the database level. I also identified two additional issues: Redis cache staleness due to missing invalidation after new offers, and an N+1 query pattern when loading buyer data for each offer. These were not prioritized first because they affect performance and UI freshness, while the race condition directly impacts data integrity and transaction correctness.

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

### Task 2 Response

Embedding offers inside the property document can cause the document to grow very large as popular listings accumulate many offers, potentially hitting MongoDB’s 16MB document limit. It also creates a hot document problem because every new offer rewrites the entire property document, increasing write contention under heavy traffic. A better approach is to store offers in a separate `offers` collection with a reference to `property_id` and appropriate indexes such as `(property_id)` and `(property_id, buyer_id)` unique. This allows offers to scale independently and improves write performance. The tradeoff is that retrieving property data with its offers now requires additional queries or aggregation, increasing application complexity compared to the embedded model.

## Task 3

**Format:** code + explanation

Review `get_comparable_sales` method in `app/services/valuation_service.py`. 
Leave comments on any issue you'd flag and order them by priority as we scale up.

---

### Task 3 Response

The highest priority issue in `get_comparable_sales` is the lack of a proper index on `(property_id, sale_price)`, which can cause collection scans and expensive in-memory sorting as the dataset grows. The method also executes two separate database queries (one for the top comps and one for the count), doubling the load under high traffic. Another concern is potential cache stampede when the Redis entry expires and many requests hit the database simultaneously. Additionally, the query retrieves full documents instead of projecting only required fields, increasing payload size and serialization cost. I would address indexing first, then reduce duplicate queries (e.g., via aggregation), and finally add cache protection mechanisms.

## Task 4

**Format:** explanation

An AI system routes user requests through an Orchestrator that manages a stateful workflow. Each downstream agent runs a multi-step LLM chain. Agents call external tools through a service layer. Some workflows pause mid-execution waiting for user input.

In production you observe p99 response times exceeding 50 seconds, occasional cascading failures when a downstream agent is slow, and paused workflows that are never cleaned up.

You have 1 week before a product demo.

1. What reliability problems would you expect in a system like this?
2. How would you prioritize fixing them, and what does your prioritization give up?
3. Given all of the knowledge you know, provide a 1-week timeline of your implementation details and how it will impact the users.
4. What makes the tool service layer harder to make resilient than a typical stateless API?
