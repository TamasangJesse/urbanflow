import logging
import os
from typing import Optional

from google import genai
from google.genai import types

from app.retriever import (
    extract_day,
    extract_hour,
    extract_location,
    get_nearby_incidents,
    get_traffic_prediction,
)

logger = logging.getLogger(__name__)

FALLBACK_ANSWER = (
    "I am unable to process your question at this moment. Please try again shortly."
)


def format_incidents(incidents: list) -> str:
    if not incidents:
        return "No active incidents currently reported near this location."
    lines = []
    for inc in incidents[:5]:
        lines.append(
            f"- {inc.get('type', 'Unknown').upper()}: "
            f"{inc.get('description', 'No description')} | "
            f"Severity: {inc.get('severity', 'unknown')} | "
            f"Reported: {inc.get('created_at', 'unknown')}"
        )
    return "\n".join(lines)


async def generate_answer(
    question: str,
    latitude: float,
    longitude: float,
    token: str,
) -> dict:
    # Step 1 — Extract context clues from question
    location: Optional[str] = extract_location(question)
    hour: int = extract_hour(question)
    day: str = extract_day(question)

    # Step 2 — Always fetch nearby incidents by coordinates
    incidents = await get_nearby_incidents(latitude, longitude, token)

    # Step 3 — Fetch traffic prediction only if location detected
    prediction: Optional[str] = None
    if location:
        prediction = await get_traffic_prediction(location, hour, day, token)

    # Step 4 — Format incidents into readable text
    formatted_incidents = format_incidents(incidents)

    # Step 5 — Build Gemini prompt
    prompt = f"""
You are UrbanFlow AI, a traffic assistant for Yaoundé, Cameroon. You help drivers make smart decisions about their routes and travel timing.

Answer the user's question using ONLY the real-time data provided below. Do not invent information. If the data shows no incidents, say the area appears clear based on current reports. Be concise (maximum 3 sentences), specific to Yaoundé, and helpful.

CURRENT TRAFFIC DATA:
Nearby incidents ({latitude}, {longitude}):
{formatted_incidents}

Traffic prediction for {location or 'the requested area'}:
{prediction or 'Prediction unavailable for this location.'}

User question: {question}

Your answer:
"""

    # Step 6 — Call Gemini API
    answer = FALLBACK_ANSWER
    try:
        gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        answer = response.text
    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc)

    # Step 7 — Return result dict
    return {
        "answer": answer,
        "location_detected": location,
        "context_used": {
            "incidents": incidents,
            "prediction": prediction,
        },
    }