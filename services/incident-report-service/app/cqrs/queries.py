from repository import incident_repository

"""
CQRS — QUERY SIDE
════════════════════════════════════════════════════════════════════
Every function here READS data only.
These functions NEVER write to MongoDB.
These functions NEVER touch Redis. Not once.
This file is the proof of the Query side of the CQRS pattern.
════════════════════════════════════════════════════════════════════
"""


async def qry_get_incidents_near(lat: float, lng: float, radius: float) -> list:
    """
    QUERY: Return all active incidents within `radius` metres.
    Uses MongoDB $near with the 2dsphere geospatial index.
    """
    return await incident_repository.find_near(lat, lng, radius)


async def qry_get_incidents_by_area(area: str) -> list:
    """
    QUERY: Return active incidents for a named area.
    """
    return await incident_repository.find_by_area(area)


async def qry_get_incident_by_id(incident_id: str) -> dict | None:
    """
    QUERY: Return full details of a single incident.
    """
    return await incident_repository.find_by_id(incident_id)


async def qry_get_incidents_by_user(user_id: str) -> list:
    """
    QUERY: Return all incidents reported by a specific user.
    """
    return await incident_repository.find_by_user(user_id)

async def qry_check_route_for_incidents(route_points: list[list[float]]) -> dict | None:
    """
    QUERY: Check a route for incidents within 300m of any point.
    Read only. Never touches Redis.
    """
    return await incident_repository.find_incident_along_route(route_points)

