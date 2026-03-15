# rules.py — Rule-based chatbot engine for CareSync
import re
from dataclasses import dataclass
from typing import Optional

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
    confidence: float = 1.0
    off_topic: bool = False

# ── Off-topic keywords ─────────────────────────────────────────
OFF_TOPIC_PATTERNS = [
    r'\bweather\b', r'\bsport[s]?\b', r'\bfootball\b', r'\bcricket\b',
    r'\bnews\b', r'\bpolitics?\b', r'\bmovie[s]?\b', r'\bfilm[s]?\b',
    r'\bmusic\b', r'\bsong[s]?\b', r'\brecipe[s]?\b', r'\bcook(ing)?\b',
    r'\bmath\b', r'\bcalculate\b', r'\bcode\b', r'\bprogram(ming)?\b',
    r'\bjoke[s]?\b', r'\bfunny\b', r'\bstory\b', r'\bpoem\b',
    r'\binstagram\b', r'\bfacebook\b', r'\bwhatsapp\b', r'\btwitter\b',
    r'\bhoroscope\b', r'\bastrology\b', r'\blottery\b', r'\bgame[s]?\b',
    r'\btravel\b', r'\bhotel\b', r'\bflight\b', r'\btourist\b',
]

# ── Disease prediction rules ───────────────────────────────────
DISEASE_RULES = [
    {
        "name": "Common Cold",
        "keywords": ["runny nose", "stuffy nose", "sneezing", "sore throat", "mild fever", "congestion", "nasal"],
        "required": 2,
        "reply": (
            "Based on your symptoms, you may be experiencing a **Common Cold**.\n\n"
            "Common cold symptoms include runny nose, sneezing, sore throat, mild fever, and congestion. "
            "It is caused by a viral infection and usually resolves on its own within 7–10 days.\n\n"
            "💊 What helps: Rest, staying hydrated, steam inhalation, and paracetamol for fever. "
            "Avoid antibiotics as they do not work against viruses.\n\n"
            "⚠️ See a doctor if: Fever exceeds 39°C, symptoms worsen after day 5, or you develop difficulty breathing."
        ),
        "doctor": DOCTORS["general"],
    },
    {
        "name": "Influenza (Flu)",
        "keywords": ["high fever", "body ache", "chills", "fatigue", "headache", "flu", "influenza", "muscle pain", "sudden fever"],
        "required": 3,
        "reply": (
            "Based on your symptoms, you may be experiencing **Influenza (Flu)**.\n\n"
            "The flu typically comes on suddenly with high fever, body aches, chills, extreme fatigue, and headache — "
            "unlike a cold which develops gradually. It is caused by the influenza virus.\n\n"
            "💊 What helps: Rest, fluids, paracetamol or ibuprofen for fever. Antiviral medication can help if taken early.\n\n"
            "⚠️ See a doctor if: Fever is very high, breathing becomes difficult, or symptoms don't improve after 5 days."
        ),
        "doctor": DOCTORS["general"],
    },
    {
        "name": "Hypertension (High Blood Pressure)",
        "keywords": ["high blood pressure", "hypertension", "headache neck", "dizziness blood", "blurred vision", "chest pressure", "nosebleed"],
        "required": 1,
        "reply": (
            "Based on your symptoms, you may be experiencing signs of **Hypertension (High Blood Pressure)**.\n\n"
            "High blood pressure often has no obvious symptoms, but warning signs can include headaches at the back of the neck, "
            "dizziness, blurred vision, and nosebleeds. It is a serious condition that increases risk of heart attack and stroke.\n\n"
            "💊 What helps: Regular blood pressure monitoring, reducing salt intake, exercise, and prescribed medication.\n\n"
            "⚠️ See a doctor immediately if: Blood pressure reading is above 180/120, or you have chest pain or vision changes."
        ),
        "doctor": DOCTORS["cardiologist"],
    },
    {
        "name": "Migraine",
        "keywords": ["throbbing headache", "one side head", "light sensitivity", "sound sensitivity", "nausea headache", "vomiting headache", "aura", "migraine"],
        "required": 2,
        "reply": (
            "Based on your symptoms, you may be experiencing a **Migraine**.\n\n"
            "Migraines are intense, throbbing headaches usually on one side of the head, often accompanied by nausea, "
            "vomiting, and sensitivity to light and sound. Some migraines are preceded by visual disturbances called aura.\n\n"
            "💊 What helps: Resting in a dark quiet room, staying hydrated, pain relievers like ibuprofen or prescribed triptans.\n\n"
            "⚠️ See a doctor if: Migraines are frequent, very severe, or accompanied by neurological symptoms like numbness or slurred speech."
        ),
        "doctor": DOCTORS["neurologist"],
    },
    {
        "name": "Asthma",
        "keywords": ["wheezing", "shortness of breath exercise", "chest tightness", "cough night", "breathless walking", "inhaler", "asthma"],
        "required": 2,
        "reply": (
            "Based on your symptoms, you may be experiencing **Asthma**.\n\n"
            "Asthma causes episodes of wheezing, breathlessness, chest tightness, and coughing — especially at night or during exercise. "
            "It is a chronic condition where the airways become inflamed and narrowed.\n\n"
            "💊 What helps: Avoiding triggers like dust, smoke, and pollen. Reliever inhalers for attacks, preventer inhalers for long-term control.\n\n"
            "⚠️ See a doctor if: Symptoms are frequent, your inhaler isn't helping, or you have a severe attack."
        ),
        "doctor": DOCTORS["pulmonologist"],
    },
    {
        "name": "Type 2 Diabetes",
        "keywords": ["excessive thirst", "frequent urination", "blurred vision", "slow healing", "tingling feet", "increased hunger", "fatigue diabetes", "high sugar"],
        "required": 2,
        "reply": (
            "Based on your symptoms, you may be experiencing signs of **Type 2 Diabetes**.\n\n"
            "Common symptoms include excessive thirst, frequent urination, unexplained fatigue, blurred vision, "
            "slow-healing wounds, and tingling in the hands or feet. Type 2 diabetes develops when the body cannot use insulin effectively.\n\n"
            "💊 What helps: Healthy diet low in sugar and refined carbs, regular exercise, weight management, and prescribed medication.\n\n"
            "⚠️ See a doctor for: A blood glucose test to confirm diagnosis. Early detection is key to preventing complications."
        ),
        "doctor": DOCTORS["endocrinologist"],
    },
    {
        "name": "Hypothyroidism",
        "keywords": ["weight gain unexplained", "always cold", "fatigue tiredness", "dry skin", "hair loss", "constipation", "slow heartbeat", "thyroid"],
        "required": 2,
        "reply": (
            "Based on your symptoms, you may be experiencing **Hypothyroidism** (underactive thyroid).\n\n"
            "When the thyroid gland doesn't produce enough hormone, it causes fatigue, unexplained weight gain, feeling cold, "
            "dry skin, hair thinning, and constipation. It is diagnosed with a simple blood test.\n\n"
            "💊 What helps: Daily thyroid hormone replacement tablets (levothyroxine), which are very effective.\n\n"
            "⚠️ See a doctor for: A TSH blood test to confirm the diagnosis."
        ),
        "doctor": DOCTORS["endocrinologist"],
    },
    {
        "name": "Osteoarthritis",
        "keywords": ["joint stiffness morning", "joint pain walking", "knee swelling", "creaking joints", "difficulty climbing stairs", "joint pain elderly", "arthritis"],
        "required": 2,
        "reply": (
            "Based on your symptoms, you may be experiencing **Osteoarthritis**.\n\n"
            "Osteoarthritis is the most common form of arthritis, causing joint pain, stiffness (especially in the morning), "
            "swelling, and reduced range of motion. It commonly affects the knees, hips, and hands.\n\n"
            "💊 What helps: Low-impact exercise like swimming, weight management, physiotherapy, and pain relief medication.\n\n"
            "⚠️ See a doctor if: Pain is severe, joints are very swollen, or daily activities are significantly affected."
        ),
        "doctor": DOCTORS["orthopaedic"],
    },
    {
        "name": "Pneumonia",
        "keywords": ["cough phlegm", "high fever breathing", "chest pain breathing", "shortness of breath fever", "coughing blood", "rapid breathing", "pneumonia"],
        "required": 2,
        "reply": (
            "Based on your symptoms, you may be experiencing **Pneumonia**.\n\n"
            "Pneumonia is an infection of the lungs causing cough with phlegm, fever, chest pain when breathing, "
            "and shortness of breath. It can be caused by bacteria, viruses, or fungi.\n\n"
            "💊 What helps: Bacterial pneumonia is treated with antibiotics. Rest and fluids are important for recovery.\n\n"
            "⚠️ See a doctor immediately: Pneumonia can be serious, especially in elderly or immunocompromised patients. Do not delay."
        ),
        "doctor": DOCTORS["pulmonologist"],
    },
    {
        "name": "Gastroenteritis (Stomach Flu)",
        "keywords": ["diarrhoea", "vomiting stomach", "stomach cramp", "nausea vomiting", "food poisoning", "loose stool", "stomach bug"],
        "required": 2,
        "reply": (
            "Based on your symptoms, you may be experiencing **Gastroenteritis** (Stomach Flu or Food Poisoning).\n\n"
            "Gastroenteritis causes nausea, vomiting, diarrhoea, and stomach cramps. It is usually caused by a viral or bacterial infection "
            "from contaminated food or water and resolves within a few days.\n\n"
            "💊 What helps: Stay hydrated with ORS (oral rehydration solution), rest, and eat bland foods like rice and toast. "
            "Avoid dairy and spicy foods until recovered.\n\n"
            "⚠️ See a doctor if: Symptoms last more than 3 days, there is blood in stool, or you show signs of dehydration."
        ),
        "doctor": DOCTORS["general"],
    },
]

# ── Symptom rules (doctor suggestions without disease prediction) ──
SYMPTOM_RULES = [
    {
        "keywords": ["chest pain", "chest tightness", "heart pain", "palpitation", "heart racing",
                     "irregular heartbeat", "angina", "shortness of breath heart"],
        "reply": (
            "Chest pain or heart-related symptoms should always be taken seriously. "
            "If the pain is severe, spreading to your arm or jaw, or accompanied by sweating and nausea, "
            "please seek emergency care immediately. For non-emergency concerns, I recommend booking an "
            "appointment with our Cardiologist."
        ),
        "doctor": DOCTORS["cardiologist"],
    },
    {
        "keywords": ["headache", "migraine", "dizziness", "seizure", "numbness", "tingling",
                     "memory loss", "confusion", "fainting", "vertigo", "head pain", "fits"],
        "reply": (
            "Neurological symptoms like headaches, dizziness, or numbness can have various causes. "
            "If symptoms are severe, sudden, or recurring, a neurological evaluation is recommended."
        ),
        "doctor": DOCTORS["neurologist"],
    },
    {
        "keywords": ["cough", "shortness of breath", "breathing difficulty", "wheezing", "asthma",
                     "phlegm", "mucus", "breathless", "chest congestion", "lung"],
        "reply": (
            "Respiratory symptoms like coughing, wheezing, or difficulty breathing may indicate infections, "
            "allergies, or chronic conditions. Our Pulmonologist can evaluate your symptoms."
        ),
        "doctor": DOCTORS["pulmonologist"],
    },
    {
        "keywords": ["diabetes", "blood sugar", "insulin", "thyroid", "excessive thirst",
                     "frequent urination", "weight gain", "weight loss sudden", "hormonal", "glucose"],
        "reply": (
            "Symptoms related to blood sugar, thyroid function, or unexplained weight changes may indicate "
            "an endocrine condition. Our Endocrinologist can provide a proper evaluation."
        ),
        "doctor": DOCTORS["endocrinologist"],
    },
    {
        "keywords": ["joint pain", "back pain", "knee pain", "shoulder pain", "fracture", "bone pain",
                     "muscle pain", "sprain", "arthritis", "spine", "slip disc", "neck pain", "hip pain"],
        "reply": (
            "Joint, muscle, or bone pain can significantly affect quality of life. "
            "Our Orthopaedic specialist can assess the cause and recommend treatment."
        ),
        "doctor": DOCTORS["orthopaedic"],
    },
    {
        "keywords": ["fever", "cold", "flu", "infection", "sore throat", "body ache",
                     "fatigue", "diarrhoea", "vomiting", "nausea", "stomach ache", "food poisoning"],
        "reply": (
            "General symptoms like fever, cold, or nausea are commonly caused by infections. "
            "Our General Physician can provide a thorough evaluation and treatment."
        ),
        "doctor": DOCTORS["general"],
    },
    {
        "keywords": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "help"],
        "reply": (
            "Hello! I'm CareSync AI, your personal health assistant. I can help you understand symptoms, "
            "predict possible conditions, suggest the right doctor, and answer health questions. "
            "How can I help you today?"
        ),
        "doctor": None,
    },
    {
        "keywords": ["upload", "how to upload", "book appointment", "how to book", "cancel", "otp", "pid", "patient id"],
        "reply": (
            "Here's a quick guide to CareSync:\n\n"
            "📁 Upload Files: Go to the Upload tab. Drag and drop files or click to select.\n\n"
            "📅 Book Appointment: Go to Appointments tab → Book Appointment → select doctor, date, and time slot.\n\n"
            "🔐 Doctor Access: Share your PID with your doctor. They request an OTP which appears on your phone or in the Appointments tab."
        ),
        "doctor": None,
    },
    {
        "keywords": ["emergency", "urgent", "ambulance", "severe pain", "unconscious", "not breathing", "stroke", "bleeding heavily"],
        "reply": (
            "⚠️ This sounds like a medical emergency. Please call 108 (India ambulance) or 112 immediately. "
            "Do not wait for an online consultation."
        ),
        "doctor": None,
    },
    {
        "keywords": ["anxiety", "depression", "stress", "mental health", "panic attack", "insomnia", "sleep problem"],
        "reply": (
            "Mental health is just as important as physical health. If you are feeling overwhelmed or depressed, "
            "please know that help is available. In India, you can reach iCall at 9152987821 for free counselling."
        ),
        "doctor": DOCTORS["general"],
    },
]

OFF_TOPIC_REPLY = (
    "I'm CareSync AI, a clinical health assistant. I'm only able to help with health and medical related questions. 😊\n\n"
    "I can help you with:\n"
    "• Describing your symptoms to predict possible conditions\n"
    "• Suggesting the right doctor for your concern\n"
    "• Answering general health and medication questions\n"
    "• Guiding you on how to use CareSync\n\n"
    "Please tell me about any health concerns you have!"
)


def is_off_topic(message: str) -> bool:
    msg = message.lower()
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, msg):
            # Make sure it's not a medical context
            medical_context = ['pain', 'symptom', 'doctor', 'health', 'medicine', 'hospital', 'sick', 'disease']
            if not any(m in msg for m in medical_context):
                return True
    return False


def predict_disease(message: str) -> Optional[RuleResult]:
    """Check if enough symptoms match a disease prediction."""
    msg = message.lower()
    msg = re.sub(r'[^\w\s]', ' ', msg)

    best_match = None
    best_score = 0

    for disease in DISEASE_RULES:
        matched = sum(1 for kw in disease["keywords"] if kw in msg)
        if matched >= disease["required"] and matched > best_score:
            best_score = matched
            best_match = disease

    if best_match:
        return RuleResult(
            reply=best_match["reply"],
            doctor=best_match.get("doctor"),
            confidence=1.0,
        )
    return None


def match_rules(message: str) -> Optional[RuleResult]:
    """Main rule matching — checks off-topic, disease prediction, then symptom rules."""
    msg = message.lower().strip()

    # Check off-topic first
    if is_off_topic(msg):
        return RuleResult(reply=OFF_TOPIC_REPLY, doctor=None, confidence=1.0, off_topic=True)

    # Try disease prediction
    disease_result = predict_disease(msg)
    if disease_result:
        return disease_result

    # Fall back to symptom rules
    msg_clean = re.sub(r'[^\w\s]', ' ', msg)
    best_match = None
    best_score = 0

    for rule in SYMPTOM_RULES:
        score = sum(len(kw.split()) for kw in rule["keywords"] if kw in msg_clean)
        if score > best_score:
            best_score = score
            best_match = rule

    if best_match and best_score >= 1:
        return RuleResult(
            reply=best_match["reply"],
            doctor=best_match.get("doctor"),
            confidence=min(1.0, best_score / 3),
        )

    return None