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
)

logger = logging.getLogger(__name__)

FALLBACK_ANSWER = (
    "I am unable to process your question at this moment. Please try again shortly."
)

GREETINGS = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "bonjour", "salut"}


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
    # Step 1 — Handle greetings instantly
    if question.strip().lower().rstrip("!.,?") in GREETINGS:
        return {
            "answer": "Hello! I'm UrbanFlow AI, your traffic assistant for Yaoundé. Ask me about traffic, incidents, or road conditions anywhere in the city!",
            "location_detected": None,
            "context_used": {"incidents": [], "prediction": None},
        }

    # Step 2 — Extract context clues from question
    location: Optional[str] = await extract_location_with_llm(question)
    hour: int = extract_hour(question)
    day: str  = extract_day(question)

    # Step 3 — Always fetch nearby incidents by coordinates
    incidents = await get_nearby_incidents(latitude, longitude, token)

    # Step 4 — Fetch traffic prediction only if location detected
    prediction: Optional[str] = None
    if location:
        prediction = await get_traffic_prediction(location, hour, day, token)

    # Step 5 — Format incidents into readable text
    formatted_incidents = format_incidents(incidents)

    # Step 6 — Build prompt
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

    # Step 7 — Call Z.ai API
    answer = FALLBACK_ANSWER
    try:
        client = OpenAI(
            api_key=os.getenv("ZAI_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4",
        )
        response = client.chat.completions.create(
            model="glm-4.7-flashx",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
        )
        logger.info("Z.ai raw response: %s", response)
        message = response.choices[0].message
        answer = message.content or getattr(message, "reasoning_content", None) or FALLBACK_ANSWER
    except Exception as exc:
        logger.error("Z.ai API call failed: %s", exc)
        traceback.print_exc()

    # Step 8 — Return result
    return {
        "answer": answer,
        "location_detected": location,
        "context_used": {
            "incidents": incidents,
            "prediction": prediction,
        },
    }