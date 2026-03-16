"""
Property data access layer.

Provides read operations on the properties collection.
"""

from bson import ObjectId


class PropertyRepository:
    def __init__(self, db):
        self.db = db

    def list_properties(self, page: int = 1, per_page: int = 20) -> list:
        """Return a paginated list of properties."""
        skip = (page - 1) * per_page
        cursor = self.db.properties.find({}).skip(skip).limit(per_page)
        return [self._serialize(p) for p in cursor]

    def get_by_id(self, property_id: str) -> dict | None:
        """Fetch a single property by its string ID."""
        try:
            oid = ObjectId(property_id)
        except Exception:
            return None
        doc = self.db.properties.find_one({"_id": oid})
        return self._serialize(doc) if doc else None

    def get_properties_with_offer_counts(self) -> list:
        """
        Return all properties with their offer count and most recent offer.
        """
        properties = list(self.db.properties.find({}))
        for prop in properties:
            prop_id = str(prop["_id"])
            prop["offer_count"] = self.db.offers.count_documents(
                {"property_id": prop_id}
            )
            latest = self.db.offers.find_one(
                {"property_id": prop_id},
                sort=[("submitted_at", -1)],
            )
            prop["latest_offer_amount"] = latest["amount"] if latest else None
            prop["_id"] = prop_id

        return properties
        
    def _serialize(self, doc: dict) -> dict:
        if doc is None:
            return None
        doc["_id"] = str(doc["_id"])
        return doc
