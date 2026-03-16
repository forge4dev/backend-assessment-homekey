"""
Offer submission and retrieval service.

This module handles the core offer lifecycle: submission, deduplication,
retrieval, and caching. It is used by property_routes.py.
"""

import json
from datetime import datetime, timezone


class OfferService:
    OFFERS_CACHE_PREFIX = "offers:"

    def __init__(self, db, redis_client):
        self.db = db
        self.redis = redis_client

    def submit_offer(self, property_id: str, buyer_id: str, amount: float) -> dict:
        """
        Submit an offer from a buyer on a property.

        Raises ValueError if the buyer has already submitted an offer on
        this property.
        """
        existing = self.db.offers.find_one(
            {"property_id": property_id, "buyer_id": buyer_id}
        )
        if existing:
            raise ValueError("Duplicate offer: buyer has already submitted an offer on this property")

        offer_doc = {
            "property_id": property_id,
            "buyer_id": buyer_id,
            "amount": amount,
            "status": "pending",
            "submitted_at": datetime.now(timezone.utc),
        }
        result = self.db.offers.insert_one(offer_doc)
        offer_doc["_id"] = str(result.inserted_id)
        offer_doc["submitted_at"] = offer_doc["submitted_at"].isoformat()
        return offer_doc

    def get_offers(self, property_id: str) -> list:
        """
        Return all offers for a property, with buyer details joined in.
        Results are cached in Redis.
        """
        cache_key = f"{self.OFFERS_CACHE_PREFIX}{property_id}"

        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        offers = list(self.db.offers.find({"property_id": property_id}))
        for offer in offers:
            offer["buyer"] = self.db.users.find_one({"_id": offer["buyer_id"]})
            offer["_id"] = str(offer["_id"])
            if offer.get("submitted_at"):
                offer["submitted_at"] = offer["submitted_at"].isoformat()
            if offer.get("buyer") and offer["buyer"].get("_id"):
                offer["buyer"]["_id"] = str(offer["buyer"]["_id"])

        self.redis.set(cache_key, json.dumps(offers))

        return offers
