# rules.py — Rule-based chatbot engine for CareSync
# Handles common symptom queries with instant responses and doctor suggestions.
# If confidence is low, returns None so Gemini takes over.

import re
from dataclasses import dataclass
from typing import Optional

# ── Doctor list (matches your Supabase doctors table) ──────────
DOCTORS = {
    "cardiologist":    {"name": "Dr. Amara Singh",   "id": "DOC001", "spec": "Cardiologist"},
    "neurologist":     {"name": "Dr. Liam Chen",     "id": "DOC002", "spec": "Neurologist"},
    "pulmonologist":   {"name": "Dr. Sofia Reyes",   "id": "DOC003", "spec": "Pulmonologist"},
    "general":         {"name": "Dr. James Okafor",  "id": "DOC004", "spec": "General Physician"},
    "endocrinologist": {"name": "Dr. Priya Menon",   "id": "DOC005", "spec": "Endocrinologist"},
    "orthopaedic":     {"name": "Dr. Marcus Webb",   "id": "DOC006", "spec": "Orthopaedic"},
}

@dataclass
class RuleResult:
    reply: str
    doctor: Optional[dict] = None
    confidence: float = 1.0  # 1.0 = confident, 0.0 = not matched


# ── Symptom → response + doctor mapping ───────────────────────
RULES = [
    # Cardiac
    {
        "keywords": ["chest pain", "chest tightness", "heart pain", "palpitation", "heart racing",
                     "irregular heartbeat", "heart attack", "angina", "shortness of breath heart"],
        "reply": (
            "Chest pain or heart-related symptoms should always be taken seriously. "
            "If the pain is severe, spreading to your arm or jaw, or accompanied by sweating and nausea, "
            "please seek emergency care immediately. For non-emergency concerns, I recommend booking an "
            "appointment with our cardiologist."
        ),
        "doctor": DOCTORS["cardiologist"],
    },
    # Neurological
    {
        "keywords": ["headache", "migraine", "dizziness", "seizure", "numbness", "tingling",
                     "memory loss", "confusion", "fainting", "vertigo", "head pain", "fits"],
        "reply": (
            "Neurological symptoms like headaches, dizziness, or numbness can have various causes — "
            "from tension and dehydration to more complex conditions. If symptoms are severe, sudden, "
            "or recurring, a proper neurological evaluation is recommended. Our neurologist can help assess your condition."
        ),
        "doctor": DOCTORS["neurologist"],
    },
    # Respiratory
    {
        "keywords": ["cough", "shortness of breath", "breathing difficulty", "wheezing", "asthma",
                     "phlegm", "mucus", "breathless", "chest congestion", "respiratory", "lung"],
        "reply": (
            "Respiratory symptoms like coughing, wheezing, or difficulty breathing may indicate infections, "
            "allergies, or chronic conditions like asthma. If you are experiencing severe breathlessness, "
            "seek emergency care. Otherwise, our pulmonologist can evaluate your symptoms thoroughly."
        ),
        "doctor": DOCTORS["pulmonologist"],
    },
    # Diabetes / Endocrine
    {
        "keywords": ["diabetes", "blood sugar", "insulin", "thyroid", "fatigue weight", "excessive thirst",
                     "frequent urination", "weight gain", "weight loss sudden", "hormonal", "endocrine",
                     "hyperthyroid", "hypothyroid", "glucose"],
        "reply": (
            "Symptoms related to blood sugar, thyroid function, or unexplained weight changes may indicate "
            "an endocrine condition such as diabetes or a thyroid disorder. Early diagnosis is important for "
            "effective management. I recommend consulting our endocrinologist for a proper evaluation."
        ),
        "doctor": DOCTORS["endocrinologist"],
    },
    # Orthopaedic
    {
        "keywords": ["joint pain", "back pain", "knee pain", "shoulder pain", "fracture", "bone pain",
                     "muscle pain", "sprain", "arthritis", "spine", "slip disc", "neck pain",
                     "hip pain", "wrist pain", "ankle pain", "sports injury"],
        "reply": (
            "Joint, muscle, or bone pain can significantly affect your quality of life. Whether it's a "
            "sports injury, arthritis, or a spinal issue, our orthopaedic specialist can assess the cause "
            "and recommend treatment including physiotherapy, medication, or surgical options if needed."
        ),
        "doctor": DOCTORS["orthopaedic"],
    },
    # General / Fever / Infection
    {
        "keywords": ["fever", "cold", "flu", "infection", "viral", "bacterial", "sore throat",
                     "body ache", "fatigue", "weakness", "diarrhoea", "vomiting", "nausea",
                     "stomach ache", "stomach pain", "abdominal pain", "food poisoning", "allergy"],
        "reply": (
            "General symptoms like fever, cold, nausea, or body aches are most commonly caused by viral or "
            "bacterial infections and usually resolve with rest and proper hydration. However, if symptoms "
            "persist beyond 3–5 days or worsen significantly, a consultation is recommended. Our general "
            "physician can provide a thorough evaluation and appropriate treatment."
        ),
        "doctor": DOCTORS["general"],
    },
    # Greetings
    {
        "keywords": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "help"],
        "reply": (
            "Hello! I'm CareSync AI, your personal health assistant. I can help you understand symptoms, "
            "suggest the right doctor, answer general health questions, and guide you through using CareSync. "
            "How can I help you today?"
        ),
        "doctor": None,
    },
    # How to use CareSync
    {
        "keywords": ["upload file", "how to upload", "add file", "upload report", "upload prescription",
                     "how do i", "how to book", "book appointment", "how to cancel", "doctor access",
                     "otp", "pid", "patient id"],
        "reply": (
            "Here's a quick guide to CareSync:\n\n"
            "📁 Upload Files: Go to the Upload tab on your dashboard. Drag and drop files or click to select. "
            "Choose a file type (Prescription, Lab Report, Scan, Other) and click Upload.\n\n"
            "📅 Book Appointment: Go to the Appointments tab, click Book Appointment, select a doctor, "
            "pick a date, choose an available time slot, and confirm.\n\n"
            "🔐 Doctor Access: Share your Patient ID (PID) with your doctor. They will request an OTP "
            "which will arrive on your registered phone or appear in your Appointments tab. "
            "Share the code verbally with the doctor to grant them 2-hour access to your records."
        ),
        "doctor": None,
    },
    # Emergency
    {
        "keywords": ["emergency", "urgent", "ambulance", "severe pain", "unconscious", "not breathing",
                     "heart attack", "stroke", "bleeding heavily", "accident"],
        "reply": (
            "⚠️ This sounds like a medical emergency. Please call emergency services immediately — "
            "dial 108 (India national ambulance) or 112 (emergency). Do not wait for an online consultation. "
            "If someone is unconscious or not breathing, begin CPR if you are trained and call for help immediately."
        ),
        "doctor": None,
        "confidence": 1.0,
    },
    # Mental health
    {
        "keywords": ["anxiety", "depression", "stress", "mental health", "panic attack", "sad",
                     "hopeless", "sleep problem", "insomnia", "suicidal", "self harm"],
        "reply": (
            "Mental health is just as important as physical health. If you are feeling overwhelmed, anxious, "
            "or depressed, please know that help is available. Speaking to a mental health professional is a "
            "strong and positive step. In India, you can also reach iCall at 9152987821 for free counselling. "
            "Our general physician can also provide an initial evaluation and referral."
        ),
        "doctor": DOCTORS["general"],
    },
]


def match_rules(message: str) -> Optional[RuleResult]:
    """
    Checks the message against all rules.
    Returns a RuleResult if matched, or None if no rule applies.
    """
    msg = message.lower().strip()
    msg = re.sub(r'[^\w\s]', ' ', msg)  # remove punctuation

    best_match = None
    best_score = 0

    for rule in RULES:
        score = 0
        for kw in rule["keywords"]:
            if kw in msg:
                # longer keyword match = higher score
                score += len(kw.split())

        if score > best_score:
            best_score = score
            best_match = rule

    # Require at least a 1-word keyword match to use rule
    if best_match and best_score >= 1:
        return RuleResult(
            reply=best_match["reply"],
            doctor=best_match.get("doctor"),
            confidence=min(1.0, best_score / 3),  # normalise
        )

    return None  # No rule matched — let Gemini handle it