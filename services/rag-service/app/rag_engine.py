import logging
import os
import traceback
from typing import Optional

from openai import OpenAI

from app.retriever import (
    extract_day,
    extract_hour,
    extract_location_with_llm,
    get_nearby_incidents,
    get_traffic_prediction,
     get_coordinates, #added just now
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
    location: Optional[str] = await extract_location_with_llm(question)
    hour: int = extract_hour(question)
    day: str  = extract_day(question)

    # Step 2 — Fetch incidents near detected location or user position
    if location:
        loc_lat, loc_lng = await get_coordinates(location)
    else:
        loc_lat, loc_lng = latitude, longitude

    incidents = await get_nearby_incidents(loc_lat, loc_lng, token)

    # Step 3 — Fetch traffic prediction only if location detected
    prediction: Optional[str] = None
    if location:
        prediction = await get_traffic_prediction(location, hour, day, token)

    # Step 4 — Format incidents
    formatted_incidents = format_incidents(incidents)

    # Step 5 — Call LLM with system + user message split
    answer = FALLBACK_ANSWER
    try:
        client = OpenAI(
            api_key=os.getenv("ZAI_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4",
        )
        response = client.chat.completions.create(
            model="glm-4.7-flashx",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are UrbanFlow AI, a friendly and helpful traffic assistant for Yaoundé, Cameroon. "
                        "You help drivers make smart decisions about routes and travel timing. "
                        "If the user greets you or makes small talk, respond warmly and naturally and invite them to ask about traffic. "
                        "If the user asks about traffic or incidents, use ONLY the real-time data provided — never invent information. "
                        "Be concise (maximum 3 sentences), friendly, and helpful. "
                        "You understand both English and French — respond in the same language the user wrote in."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"CURRENT TRAFFIC DATA:\n"
                        f"Nearby incidents:\n{formatted_incidents}\n\n"
                        f"Traffic prediction for {location or 'the requested area'}: "
                        f"{prediction or 'Prediction unavailable.'}\n\n"
                        f"User question: {question}"
                    )
                }
            ],
            max_tokens=1500,
        )
        message = response.choices[0].message
        answer = message.content or getattr(message, "reasoning_content", None) or FALLBACK_ANSWER
    except Exception as exc:
        logger.error("Z.ai API call failed: %s", exc)
        traceback.print_exc()

    return {
        "answer": answer,
        "location_detected": location,
        "context_used": {
            "incidents": incidents,
            "prediction": prediction,
        },
    }