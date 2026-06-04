import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

INCIDENT_SERVICE_URL = os.getenv("INCIDENT_SERVICE_URL", "http://incident-report-service:8004")
TRAFFIC_SERVICE_URL  = os.getenv("TRAFFIC_SERVICE_URL",  "http://traffic-intelligence-service:8002")

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


async def extract_location_with_llm(question: str) -> Optional[str]:
    """Use the LLM to extract the location name from the question."""
    try:
        client = OpenAI(
            api_key=os.getenv("ZAI_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4",
        )
        response = client.chat.completions.create(
            model="glm-4.7-flashx",
            messages=[{
                "role": "user",
                "content": (
                    "Extract only the location name from this question. "
                    "Return just the location name with no explanation, "
                    "punctuation, or extra words. "
                    "If there is no location, return the word NULL.\n\n"
                    f"Question: {question}"
                )
            }],
            max_tokens=20,
        )
        result = response.choices[0].message.content.strip()
        return None if result.upper() == "NULL" else result
    except Exception as exc:
        logger.warning("LLM location extraction failed: %s", exc)
        return None


def extract_hour(question: str) -> int:
    lower = question.lower()

    if "midnight" in lower:
        return 0
    if "noon" in lower:
        return 12

    pm_match = re.search(r"\b(\d{1,2})\s*pm\b", lower)
    if pm_match:
        h = int(pm_match.group(1))
        return h if h == 12 else h + 12

    am_match = re.search(r"\b(\d{1,2})\s*am\b", lower)
    if am_match:
        h = int(am_match.group(1))
        return 0 if h == 12 else h

    h_match = re.search(r"\b(\d{1,2})h\b", lower)
    if h_match:
        return int(h_match.group(1)) % 24

    now_utc = datetime.now(timezone.utc)
    return (now_utc.hour + 1) % 24


def extract_day(question: str) -> str:
    lower = question.lower()
    now = datetime.now(timezone.utc)

    for day in DAY_NAMES:
        if day.lower() in lower:
            return day

    if "tomorrow" in lower:
        return DAY_NAMES[(now.weekday() + 1) % 7]

    return DAY_NAMES[now.weekday()]


async def get_coordinates(location: str) -> tuple[float, float]:
    """Get coordinates for any location using free OpenStreetMap geocoding."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{location}, Yaoundé, Cameroon",
                    "format": "json",
                    "limit": 1,
                },
                headers={"User-Agent": "UrbanFlow/1.0"}
            )
            if response.status_code == 200:
                data = response.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as exc:
        logger.warning("Geocoding failed for %s: %s", location, exc)
    return (3.8667, 11.5167)


async def get_nearby_incidents(latitude: float, longitude: float, token: str) -> list:
    url = f"{INCIDENT_SERVICE_URL}/incidents/near"
    params = {"lat": latitude, "lng": longitude, "radius": 3000}
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                return data.get("incidents", [])
            logger.warning("Incident service returned %s for nearby incidents", response.status_code)
            return []
    except Exception as exc:
        logger.warning("Failed to fetch nearby incidents: %s", exc)
        return []


async def get_traffic_prediction(location: str, hour: int, day: str, token: str) -> Optional[str]:
    latitude, longitude = await get_coordinates(location)
    url = f"{TRAFFIC_SERVICE_URL}/predict"
    params = {
        "location_name": location,
        "latitude":      latitude,
        "longitude":     longitude,
        "day_of_week":   day,
        "hour":          hour,
    }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("congestion_level")
            logger.warning("Traffic service returned %s for prediction", response.status_code)
            return None
    except Exception as exc:
        logger.warning("Failed to fetch traffic prediction: %s", exc)
        return None
