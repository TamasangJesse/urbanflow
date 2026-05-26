from bson import ObjectId
from datetime import datetime, timezone
from database import incidents_collection


class IncidentRepository:
    """
    Repository Pattern — the ONLY place in this service that
    talks directly to MongoDB. No other file writes raw DB queries.
    """

    # ── WRITE OPERATIONS ─────────────────────────────────────────

    async def save_incident(self, data: dict) -> str:
        """Insert a new incident document. Returns the new _id as a string."""
        document = {
            "type":        data["type"],
            "description": data["description"],
            "latitude":    data["latitude"],
            "longitude":   data["longitude"],
            "location": {
                "type": "Point",
                "coordinates": [data["longitude"], data["latitude"]]
            },
            "severity":    data["severity"],
            "reported_by": data["reported_by"],
            "created_at":  datetime.now(timezone.utc),
            "is_active":   True
        }
        result = await incidents_collection.insert_one(document)
        return str(result.inserted_id)

   
   
   
   
    async def resolve_incident(self, incident_id: str) -> bool:
        """Set is_active to False — marks the incident as resolved."""
        result = await incidents_collection.update_one(
            {"_id": ObjectId(incident_id)},
            {"$set": {"is_active": False}}
        )
        return result.modified_count == 1

    async def delete_incident(self, incident_id: str) -> bool:
        """Permanently remove an incident document."""
        result = await incidents_collection.delete_one(
            {"_id": ObjectId(incident_id)}
        )
        return result.deleted_count == 1

    # ── READ OPERATIONS ──────────────────────────────────────────

    async def find_near(self, lat: float, lng: float, radius: float) -> list:
        """Return all active incidents within radius metres."""
        cursor = incidents_collection.find({
            "is_active": True,
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": radius
                }
            }
        })
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def find_by_area(self, area: str) -> list:
        """Return active incidents whose description mentions the given area name."""
        cursor = incidents_collection.find({
            "is_active": True,
            "description": {"$regex": area, "$options": "i"}
        })
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def find_by_id(self, incident_id: str) -> dict | None:
        """Return a single incident by its MongoDB _id."""
        doc = await incidents_collection.find_one(
            {"_id": ObjectId(incident_id)}
        )
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def find_by_user(self, user_id: str) -> list:
        """Return all incidents reported by a specific user."""
        cursor = incidents_collection.find({
            "reported_by": user_id
        })
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def find_incident_along_route(self, route_points: list[list[float]]) -> dict | None:
        """
        Loop through each coordinate in route_points and return the first
        active incident found within 300 metres. Stops at first match.
        """
        for point in route_points:
            lat, lng = point[0], point[1]
            doc = await incidents_collection.find_one({
                "is_active": True,
                "location": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [lng, lat]
                        },
                        "$maxDistance": 300
                    }
                }
            })
            if doc:
                doc["_id"] = str(doc["_id"])
                return doc
        return None


# Single shared instance — imported by commands.py and queries.py
incident_repository = IncidentRepository()