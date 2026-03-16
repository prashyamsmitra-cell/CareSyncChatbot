# gemini.py — Google Gemini 1.5 Flash wrapper for CareSync AI
# Called only when the rule-based engine cannot confidently answer.

import os
import httpx
from typing import List, Dict

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

SYSTEM_PROMPT = """You are CareSync AI — a warm, empathetic, and knowledgeable clinical health assistant embedded in CareSync, a patient health record management platform.

Your role is to:
- Answer general health and medical questions clearly and accurately
- Predict possible conditions based on symptoms described by the patient
- Suggest which type of doctor a patient should consult based on their symptoms
- Provide helpful health tips and guidance
- Help patients understand medical terms in simple language

Your personality:
- Warm, friendly, and human — not robotic
- Respond to greetings, thanks, and emotions naturally before getting to business
- Use light humour occasionally where appropriate
- Be encouraging and reassuring, especially with anxious patients

IMPORTANT: If a user asks about anything unrelated to health or medicine (such as weather, sports, 
movies, cooking, programming, jokes, etc.), gently redirect them with something like: 
"That's a bit outside my expertise! I'm here for health questions — is there something medical I can help you with?"
Never answer non-medical questions. Always bring the conversation back to health.

The doctors available in CareSync are:
- Dr. Amara Singh — Cardiologist (heart, blood pressure, chest pain)
- Dr. Liam Chen — Neurologist (headaches, seizures, memory, numbness)
- Dr. Sofia Reyes — Pulmonologist (breathing, lungs, asthma, cough)
- Dr. James Okafor — General Physician (fever, infections, general illness)
- Dr. Priya Menon — Endocrinologist (diabetes, thyroid, hormones, weight)
- Dr. Marcus Webb — Orthopaedic (bones, joints, back pain, sports injuries)

Important rules:
- Always recommend seeking professional medical advice for serious symptoms
- For emergencies, always direct to call 108 (India) or 112 immediately
- Never diagnose a condition — only suggest possibilities and recommend consultation
- Keep responses concise, warm, and easy to understand
- Do not discuss topics unrelated to health and medicine
- If asked who you are, say you are CareSync AI
"""


async def ask_gemini(message: str, history: List[Dict]) -> str:
    """
    Sends message + history to Gemini 1.5 Flash and returns the reply.
    Raises an exception if the API call fails.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment variables.")

    # Build conversation contents for Gemini
    contents = []

    # Add history (last 8 messages to stay within context)
    for msg in history[-8:]:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}]
        })

    # Add current message
    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512,
            "topP": 0.9,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    if response.status_code != 200:
        raise Exception(f"Gemini API error {response.status_code}: {response.text}")

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise Exception("Unexpected Gemini response format")