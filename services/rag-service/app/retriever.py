import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

INCIDENT_SERVICE_URL = os.getenv("INCIDENT_SERVICE_URL", "http://incident-report-service:8004")
TRAFFIC_SERVICE_URL = os.getenv("TRAFFIC_SERVICE_URL", "http://traffic-intelligence-service:8002")

YAOUNDE_LOCATIONS = [
    "Bastos", "Mokolo", "Mvan", "Carrefour Warda", "Centre Ville",
    "Nlongkak", "Mvog-Ada", "Messasi", "Biyem-Assi", "Essos", "Omnisports",
    "Mimboman", "Ngousso", "Santa Barbara", "Nsam", "Mendong", "Odza",
    "Ahala", "Nkolfoulou", "Ekounou",
]

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def extract_location(question: str) -> Optional[str]:
    lower = question.lower()
    for loc in YAOUNDE_LOCATIONS:
        if loc.lower() in lower:
            return loc
    return None


def extract_hour(question: str) -> int:
    lower = question.lower()

    if "midnight" in lower:
        return 0
    if "noon" in lower:
        return 12

    # Match "5pm", "5 pm", "17h", "at 8am", "8 am"
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

    # Default: current WAT hour (UTC+1)
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
            logger.warning(
                "Incident service returned %s for nearby incidents", response.status_code
            )
            return []
    except Exception as exc:
        logger.warning("Failed to fetch nearby incidents: %s", exc)
        return []


async def get_traffic_prediction(location: str, hour: int, day: str, token: str) -> Optional[str]:
    url = f"{TRAFFIC_SERVICE_URL}/predict"
    params = {"location": location, "hour": hour, "day": day}
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("congestion_level")
            logger.warning(
                "Traffic service returned %s for prediction", response.status_code
            )
            return None
    except Exception as exc:
        logger.warning("Failed to fetch traffic prediction: %s", exc)
        return None