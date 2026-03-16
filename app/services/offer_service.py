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

        # Ensure database-level deduplication
        # This prevents race conditions under concurrent offer submissions
        self.db.offers.create_index(
            [("property_id", 1), ("buyer_id", 1)],
            unique=True
        )

    def submit_offer(self, property_id: str, buyer_id: str, amount: float) -> dict:
        """
        Submit an offer from a buyer on a property.
        Raises ValueError if a duplicate offer exists.
        """

        offer_doc = {
            "property_id": property_id,
            "buyer_id": buyer_id,
            "amount": amount,
            "status": "pending",
            "submitted_at": datetime.now(timezone.utc),
        }

        try:
            result = self.db.offers.insert_one(offer_doc)

        except DuplicateKeyError:
            raise ValueError(
                "Duplicate offer: buyer has already submitted an offer on this property"
            )

        # Convert Mongo ObjectId to string
        offer_doc["_id"] = str(result.inserted_id)
        offer_doc["submitted_at"] = offer_doc["submitted_at"].isoformat()

        # Invalidate cache so seller dashboard sees fresh data
        cache_key = f"{self.OFFERS_CACHE_PREFIX}{property_id}"
        self.redis.delete(cache_key)

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

        # Fetch offers
        offers = list(self.db.offers.find({"property_id": property_id}))
        # Batch fetch buyers to avoid N+1 queries
        buyer_ids = [offer["buyer_id"] for offer in offers]

        buyers = {}
        if buyer_ids:
            buyer_docs = self.db.users.find({"_id": {"$in": buyer_ids}})
            buyers = {b["_id"]: b for b in buyer_docs}
        
        # Attach buyer info
        for offer in offers:
            offer["_id"] = str(offer["_id"])

            if offer.get("submitted_at"):
                offer["submitted_at"] = offer["submitted_at"].isoformat()

            buyer = buyers.get(offer["buyer_id"])
            if buyer:
                buyer["_id"] = str(buyer["_id"])
                offer["buyer"] = buyer


        self.redis.set(cache_key, json.dumps(offers))

        return offers
