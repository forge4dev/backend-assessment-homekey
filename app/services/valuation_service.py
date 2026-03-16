"""
Property valuation service.

Calls a (mocked) valuation model and caches the result.
"""

import json
import time
import random
from datetime import datetime, timezone

COMPS_CACHE_TTL = 60

class ValuationService:
    VALUATION_CACHE_PREFIX = "valuation:"

    def __init__(self, db, redis_client):
        self.db = db
        self.redis = redis_client

    def get_valuation(self, property_id: str) -> dict:
        """
        Return a valuation estimate for the property.
        """
        cache_key = f"{self.VALUATION_CACHE_PREFIX}{property_id}"

        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Simulate external model latency
        result = self._call_valuation_model(property_id)

        self.redis.set(cache_key, json.dumps(result))

        return result

    def get_comparable_sales(self, property_id: str) -> dict:
        """Return top comparable sales for the listing page sidebar."""
        cache_key = f"comps:{property_id}"
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        top_comps = list(
            self.db.comparable_sales
            .find({"property_id": property_id})
            .sort("sale_price", -1)
            .limit(3)
        )

        total = self.db.comparable_sales.count_documents({"property_id": property_id})

        result = {
            "top_comparable_sales": [
                {**c, "_id": str(c["_id"])} for c in top_comps
            ],
            "total_count": total,
        }
        self.redis.set(cache_key, json.dumps(result), ex=COMPS_CACHE_TTL)
        return result

    def invalidate(self, property_id: str) -> None:
        """Invalidate the cached valuation for a property."""
        cache_key = f"{self.VALUATION_CACHE_PREFIX}{property_id}"
        self.redis.delete(cache_key)

    def _call_valuation_model(self, property_id: str) -> dict:
        """Mock valuation call with latency."""
        time.sleep(1.5)  # 1500 ms mock latency

        base = 1_000_000 + random.randint(-200_000, 400_000)
        return {
            "property_id": property_id,
            "estimated_value": base,
            "comparable_sales": self._mock_comps(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": "mock-v1",
        }

    def _mock_comps(self) -> list:
        comps = []
        for i in range(3):
            comps.append({
                "address": f"{100 + i * 10} Nearby St",
                "sale_price": 950_000 + i * 75_000,
                "sold_at": "2025-11-01",
                "distance_km": round(0.3 + i * 0.2, 1),
            })
        return comps
