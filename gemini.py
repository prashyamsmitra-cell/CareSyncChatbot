# gemini.py - Google Gemini wrapper for CareSync AI
# Called only when the rule-based engine cannot confidently answer.

import asyncio
import os
from typing import Dict, List, Optional

import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
MAX_RETRIES = 3
BASE_RETRY_DELAY_SECONDS = 1.0

SYSTEM_PROMPT = """You are CareSync AI - a warm, empathetic, and knowledgeable clinical health assistant embedded in CareSync, a patient health record management platform.

Your role is to:
- Answer general health and medical questions clearly and accurately
- Predict possible conditions based on symptoms described by the patient
- Suggest which type of doctor a patient should consult based on their symptoms
- Provide helpful health tips and guidance
- Help patients understand medical terms in simple language

Your personality:
- Warm, friendly, and human - not robotic
- Respond to greetings, thanks, and emotions naturally before getting to business
- Use light humour occasionally where appropriate
- Be encouraging and reassuring, especially with anxious patients

IMPORTANT: If a user asks about anything unrelated to health or medicine (such as weather, sports,
movies, cooking, programming, jokes, etc.), gently redirect them with something like:
"That's a bit outside my expertise! I'm here for health questions - is there something medical I can help you with?"
Never answer non-medical questions. Always bring the conversation back to health.

The doctors available in CareSync are:
- Dr. Amara Singh - Cardiologist (heart, blood pressure, chest pain)
- Dr. Liam Chen - Neurologist (headaches, seizures, memory, numbness)
- Dr. Sofia Reyes - Pulmonologist (breathing, lungs, asthma, cough)
- Dr. James Okafor - General Physician (fever, infections, general illness)
- Dr. Priya Menon - Endocrinologist (diabetes, thyroid, hormones, weight)
- Dr. Marcus Webb - Orthopaedic (bones, joints, back pain, sports injuries)

Important rules:
- Always recommend seeking professional medical advice for serious symptoms
- For emergencies, always direct to call 108 (India) or 112 immediately
- Never diagnose a condition - only suggest possibilities and recommend consultation
- Keep responses concise, warm, and easy to understand
- Do not discuss topics unrelated to health and medicine
- If asked who you are, say you are CareSync AI
"""


class GeminiError(Exception):
    """Base error for Gemini API failures."""


class GeminiRateLimitError(GeminiError):
    """Raised when Gemini rejects a request due to rate limits or quota."""

    def __init__(self, status_code: int, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


def _parse_retry_after(response: httpx.Response) -> Optional[float]:
    header_value = response.headers.get("Retry-After")
    if not header_value:
        return None

    try:
        return max(float(header_value), 0.0)
    except ValueError:
        return None


def _extract_text_response(data: Dict) -> str:
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiError("Unexpected Gemini response format") from exc


async def ask_gemini(message: str, history: List[Dict]) -> str:
    """
    Sends message + history to Gemini and returns the reply.
    Retries briefly for transient rate-limit and server failures.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment variables.")

    contents = []

    # Keep the recent context small to reduce token pressure and quota usage.
    for msg in history[-6:]:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}],
        })

    contents.append({
        "role": "user",
        "parts": [{"text": message}],
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}],
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 384,
            "topP": 0.9,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ],
    }

    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.post(
                    f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
            except httpx.HTTPError as exc:
                if attempt == MAX_RETRIES:
                    raise GeminiError(f"Gemini request failed: {exc}") from exc
                await asyncio.sleep(BASE_RETRY_DELAY_SECONDS * attempt)
                continue

            if response.status_code == 200:
                return _extract_text_response(response.json())

            retry_after = _parse_retry_after(response)
            response_preview = response.text[:300]

            if response.status_code == 429:
                if attempt < MAX_RETRIES:
                    delay = retry_after if retry_after is not None else BASE_RETRY_DELAY_SECONDS * attempt
                    await asyncio.sleep(delay)
                    continue
                raise GeminiRateLimitError(
                    status_code=429,
                    message=f"Gemini API rate limit hit: {response_preview}",
                    retry_after=retry_after,
                )

            if 500 <= response.status_code < 600 and attempt < MAX_RETRIES:
                await asyncio.sleep(BASE_RETRY_DELAY_SECONDS * attempt)
                continue

            raise GeminiError(f"Gemini API error {response.status_code}: {response_preview}")

    raise GeminiError("Gemini request failed after retries")
