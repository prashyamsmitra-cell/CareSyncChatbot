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
    redirect: Optional[str] = None  # tab name to highlight in UI

# ── Navigation redirects ───────────────────────────────────────
NAV_RULES = [
    {
        "keywords": ["upload file", "upload report", "upload prescription", "upload scan",
                     "add file", "how to upload", "upload medical", "share file"],
        "reply": "Sure! To upload your medical files, head over to the **Upload** tab on your dashboard. You can drag and drop files or click to browse — supports PDFs, images, and scans. You can also add a note describing each file.",
        "redirect": "upload",
    },
    {
        "keywords": ["book appointment", "make appointment", "schedule appointment", "how to book",
                     "book a doctor", "see a doctor", "appointment booking", "how do i make an appointment",
                     "how to make appointment", "book slot", "schedule visit"],
        "reply": "Of course! To book an appointment, go to the **Appointments** tab on your dashboard. Click **Book Appointment**, choose your doctor, pick a date, and select an available time slot. You can also add a reason for your visit.",
        "redirect": "appointments",
    },
    {
        "keywords": ["cancel appointment", "reschedule", "cancel booking"],
        "reply": "To cancel an appointment, go to the **Appointments** tab and find the appointment you want to cancel. Click the cancel button next to it. Please note that only Pending or Confirmed appointments can be cancelled.",
        "redirect": "appointments",
    },
    {
        "keywords": ["my files", "view files", "see my files", "find my files", "my reports",
                     "my prescriptions", "file library", "download file", "view report"],
        "reply": "Your uploaded files are all in the **Files** tab on your dashboard. You can view, download, or delete any file from there. Each file shows its type, size, and upload date.",
        "redirect": "files",
    },
    {
        "keywords": ["otp", "doctor access", "give doctor access", "doctor portal", "share records with doctor",
                     "how does doctor access", "pid", "patient id", "my pid"],
        "reply": "To give your doctor access to your records, share your **Patient ID (PID)** with them — you can find it on your dashboard. Your doctor will enter your PID in the Doctor Portal and an OTP will be sent to your registered phone (or appear in your Appointments tab). Share the code verbally with your doctor and they'll get 2-hour access to your records.",
        "redirect": "appointments",
    },
    {
        "keywords": ["ai chat", "chat", "talk to ai", "health chat", "ask health question"],
        "reply": "You're already here! I'm CareSync AI and I'm ready to help. Go ahead and describe your symptoms or ask me any health question. 😊",
        "redirect": None,
    },
    {
        "keywords": ["overview", "dashboard", "home", "go back", "main page", "my profile", "my stats", "bmi"],
        "reply": "Your health overview including BMI, weight, height, blood type, and appointment summary is all on the **Overview** tab of your dashboard.",
        "redirect": "overview",
    },
]

# ── Conversational / emotional rules ──────────────────────────
CONVERSATIONAL_RULES = [
    {
        "patterns": [r'\bhello\b', r'\bhi\b', r'\bhey\b', r'\bgood morning\b', r'\bgood afternoon\b',
                     r'\bgood evening\b', r'\bgreetings\b', r'\bhowdy\b'],
        "replies": [
            "Hello! 👋 Welcome to CareSync. I'm your personal health assistant. Whether you have a symptom to check, need to find the right doctor, or just have a health question — I'm here to help. What can I do for you today?",
            "Hi there! 😊 Great to have you here. I'm CareSync AI, ready to assist with any health questions or help you navigate your records. How are you feeling today?",
            "Hey! Good to see you. I'm CareSync AI — your clinical companion. Tell me what's on your mind health-wise and I'll do my best to help!",
        ],
    },
    {
        "patterns": [r'\bhow are you\b', r'\bhow do you do\b', r'\bare you okay\b', r'\bhow\'s it going\b'],
        "replies": [
            "I'm doing great, thank you for asking! 😊 I'm always ready to help with your health questions. How are *you* feeling today? Any symptoms or concerns I can help with?",
            "All systems running smoothly on my end! More importantly — how are you feeling? If something's been bothering you health-wise, I'm here to help.",
        ],
    },
    {
        "patterns": [r'\bthank\b', r'\bthanks\b', r'\bthank you\b', r'\bthankyou\b', r'\bthx\b',
                     r'\bmuch appreciated\b', r'\bgrateful\b'],
        "replies": [
            "You're very welcome! 😊 I'm always here if you have more health questions or need help navigating CareSync. Take care of yourself!",
            "Happy to help! That's what I'm here for. 🙏 Don't hesitate to reach out if you have more questions or concerns.",
            "Of course! Wishing you good health. 💚 Feel free to come back anytime you need assistance.",
        ],
    },
    {
        "patterns": [r'\bsorry\b', r'\bapologi[sz]e\b', r'\bmy bad\b', r'\bmy mistake\b'],
        "replies": [
            "No worries at all! 😊 There's nothing to apologise for. How can I help you today?",
            "Not a problem! We're all good here. Now, is there anything health-related I can assist you with?",
        ],
    },
    {
        "patterns": [r'\bbye\b', r'\bgoodbye\b', r'\bsee you\b', r'\btake care\b', r'\bgood night\b',
                     r'\bgood day\b', r'\bsee ya\b', r'\bciao\b'],
        "replies": [
            "Take care! 💚 Remember, I'm always here whenever you have a health question. Stay well!",
            "Goodbye! Wishing you good health. 😊 Come back anytime you need help.",
            "See you! Don't hesitate to return if you need medical guidance. Stay healthy! 🌿",
        ],
    },
    {
        "patterns": [r'\bi hate\b', r'\bthis is stupid\b', r'\buseless\b', r'\bworthless\b',
                     r'\bterrible\b', r'\bawful\b', r'\bi don\'t like\b'],
        "replies": [
            "I'm sorry to hear that. 😔 I genuinely want to be helpful to you. If there's something I can do better or a health question I can answer more clearly, please let me know.",
            "I understand your frustration, and I'm sorry if I've not been helpful enough. I'll do my best to improve. Is there a health concern I can help you with right now?",
        ],
    },
    {
        "patterns": [r'\bgreat\b', r'\bawesome\b', r'\bamazing\b', r'\bwonderful\b', r'\bexcellent\b',
                     r'\bperfect\b', r'\blove it\b', r'\bfantastic\b'],
        "replies": [
            "Glad to hear that! 😊 Is there anything else health-related I can help you with?",
            "Wonderful! 🌟 Let me know if you have any more health questions or need help with anything.",
        ],
    },
    {
        "patterns": [r'\bwho are you\b', r'\bwhat are you\b', r'\btell me about yourself\b',
                     r'\bwhat can you do\b', r'\byour name\b', r'\bwhat is caresync\b'],
        "replies": [
            "I'm CareSync AI — your personal clinical health assistant embedded in the CareSync platform. 🏥\n\nHere's what I can help you with:\n• 🩺 Check your symptoms and predict possible conditions\n• 👨‍⚕️ Suggest the right specialist for your concern\n• 📁 Guide you to upload and manage your medical files\n• 📅 Help you book or manage appointments\n• 💊 Answer general health and medication questions\n\nI'm not a replacement for a real doctor, but I'm here to point you in the right direction. What can I help you with today?",
        ],
    },
    {
        "patterns": [r'\bhelp\b', r'\bwhat can i ask\b', r'\bwhat should i ask\b', r'\bi don\'t know\b',
                     r'\bnot sure\b', r'\bwhere to start\b'],
        "replies": [
            "Of course! Here's what I can help you with:\n\n🩺 **Symptoms** — Describe how you're feeling and I'll suggest possible conditions and the right doctor\n📅 **Appointments** — Ask me how to book, cancel, or manage appointments\n📁 **Files** — I can guide you to upload or view your medical records\n🔐 **Doctor Access** — Learn how to share your records with your doctor securely\n💊 **Health Questions** — Ask me anything about medications, conditions, or healthy living\n\nGo ahead — what's on your mind?",
        ],
    },
]

# ── Off-topic patterns ─────────────────────────────────────────
OFF_TOPIC_PATTERNS = [
    r'\bweather\b', r'\bsport[s]?\b', r'\bfootball\b', r'\bcricket\b', r'\bipl\b',
    r'\bnews\b', r'\bpolitics?\b', r'\bmovie[s]?\b', r'\bfilm[s]?\b', r'\bseries\b',
    r'\bmusic\b', r'\bsong[s]?\b', r'\brecipe[s]?\b', r'\bcook(ing)?\b', r'\bfood\b',
    r'\bmath\b', r'\bcalculate\b', r'\bcode\b', r'\bprogram(ming)?\b', r'\bpython\b',
    r'\bjoke[s]?\b', r'\bfunny\b', r'\bstory\b', r'\bpoem\b', r'\bwrite\b',
    r'\binstagram\b', r'\bfacebook\b', r'\bwhatsapp\b', r'\btwitter\b', r'\btiktok\b',
    r'\bhoroscope\b', r'\bastrology\b', r'\blottery\b', r'\bgame[s]?\b', r'\bchess\b',
    r'\btravel\b', r'\bhotel\b', r'\bflight\b', r'\btourist\b', r'\bvacation\b',
    r'\bcrypto\b', r'\bbitcoin\b', r'\bstock[s]?\b', r'\binvest\b',
]

OFF_TOPIC_REDIRECTS = [
    "That's a bit outside my expertise! 😄 I'm a health assistant, so topics like that are beyond what I can help with. But if you have any health concerns, symptoms to check, or need help booking an appointment — I'm all yours! What medical assistance can I provide?",
    "Oops, that's a little off the beaten path for me! 🏥 I specialise in health and medical queries. Let's get back to where we were — is there a symptom, health question, or appointment I can help you with?",
    "Ha, I wish I could help with that, but health is my one true calling! 😊 Tell me about any medical concerns you have and I'll do my best to assist. What can I help you with health-wise?",
    "That's not quite my area — I'm built specifically for health and medical guidance. 🩺 Let's get back on track — do you have any symptoms to discuss or questions about your health records?",
]

# ── Disease prediction rules ───────────────────────────────────
DISEASE_RULES = [
    {
        "name": "Common Cold",
        "keywords": ["runny nose", "stuffy nose", "sneezing", "sore throat", "mild fever", "congestion", "nasal"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing a **Common Cold**.\n\nCommon cold symptoms include runny nose, sneezing, sore throat, mild fever, and congestion. It is caused by a viral infection and usually resolves on its own within 7–10 days.\n\n💊 **What helps:** Rest, staying hydrated, steam inhalation, and paracetamol for fever. Avoid antibiotics as they do not work against viruses.\n\n⚠️ **See a doctor if:** Fever exceeds 39°C, symptoms worsen after day 5, or you develop difficulty breathing.",
        "doctor": DOCTORS["general"],
    },
    {
        "name": "Influenza (Flu)",
        "keywords": ["high fever", "body ache", "chills", "fatigue", "headache", "flu", "influenza", "muscle pain", "sudden fever"],
        "required": 3,
        "reply": "Based on your symptoms, you may be experiencing **Influenza (Flu)**.\n\nThe flu typically comes on suddenly with high fever, body aches, chills, extreme fatigue, and headache — unlike a cold which develops gradually.\n\n💊 **What helps:** Rest, fluids, paracetamol or ibuprofen for fever. Antiviral medication can help if taken early.\n\n⚠️ **See a doctor if:** Fever is very high, breathing becomes difficult, or symptoms don't improve after 5 days.",
        "doctor": DOCTORS["general"],
    },
    {
        "name": "Hypertension",
        "keywords": ["high blood pressure", "hypertension", "headache neck", "dizziness blood", "blurred vision", "chest pressure", "nosebleed"],
        "required": 1,
        "reply": "Based on your symptoms, you may be experiencing signs of **Hypertension (High Blood Pressure)**.\n\nWarning signs can include headaches at the back of the neck, dizziness, blurred vision, and nosebleeds. It is a serious condition that increases risk of heart attack and stroke.\n\n💊 **What helps:** Regular blood pressure monitoring, reducing salt intake, exercise, and prescribed medication.\n\n⚠️ **See a doctor immediately if:** Blood pressure is above 180/120, or you have chest pain or vision changes.",
        "doctor": DOCTORS["cardiologist"],
    },
    {
        "name": "Migraine",
        "keywords": ["throbbing headache", "one side head", "light sensitivity", "sound sensitivity", "nausea headache", "vomiting headache", "aura", "migraine"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing a **Migraine**.\n\nMigraines are intense, throbbing headaches usually on one side of the head, often accompanied by nausea, vomiting, and sensitivity to light and sound.\n\n💊 **What helps:** Rest in a dark quiet room, staying hydrated, pain relievers like ibuprofen or prescribed triptans.\n\n⚠️ **See a doctor if:** Migraines are frequent, very severe, or accompanied by numbness or slurred speech.",
        "doctor": DOCTORS["neurologist"],
    },
    {
        "name": "Asthma",
        "keywords": ["wheezing", "shortness of breath exercise", "chest tightness", "cough night", "breathless walking", "inhaler", "asthma"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing **Asthma**.\n\nAsthma causes episodes of wheezing, breathlessness, chest tightness, and coughing — especially at night or during exercise.\n\n💊 **What helps:** Avoiding triggers like dust, smoke, and pollen. Reliever inhalers for attacks, preventer inhalers for long-term control.\n\n⚠️ **See a doctor if:** Symptoms are frequent, your inhaler isn't helping, or you have a severe attack.",
        "doctor": DOCTORS["pulmonologist"],
    },
    {
        "name": "Type 2 Diabetes",
        "keywords": ["excessive thirst", "frequent urination", "blurred vision", "slow healing", "tingling feet", "increased hunger", "fatigue diabetes", "high sugar"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing signs of **Type 2 Diabetes**.\n\nCommon symptoms include excessive thirst, frequent urination, unexplained fatigue, blurred vision, and tingling in the hands or feet.\n\n💊 **What helps:** Healthy diet low in sugar, regular exercise, weight management, and prescribed medication.\n\n⚠️ **See a doctor for:** A blood glucose test to confirm diagnosis. Early detection is key.",
        "doctor": DOCTORS["endocrinologist"],
    },
    {
        "name": "Hypothyroidism",
        "keywords": ["weight gain unexplained", "always cold", "fatigue tiredness", "dry skin", "hair loss", "constipation", "slow heartbeat", "thyroid"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing **Hypothyroidism** (underactive thyroid).\n\nSymptoms include fatigue, unexplained weight gain, feeling cold, dry skin, hair thinning, and constipation. It is diagnosed with a simple blood test.\n\n💊 **What helps:** Daily thyroid hormone replacement tablets (levothyroxine), which are very effective.\n\n⚠️ **See a doctor for:** A TSH blood test to confirm diagnosis.",
        "doctor": DOCTORS["endocrinologist"],
    },
    {
        "name": "Osteoarthritis",
        "keywords": ["joint stiffness morning", "joint pain walking", "knee swelling", "creaking joints", "difficulty climbing stairs", "arthritis"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing **Osteoarthritis**.\n\nOsteoarthritis causes joint pain, stiffness (especially in the morning), swelling, and reduced range of motion. It commonly affects the knees, hips, and hands.\n\n💊 **What helps:** Low-impact exercise, weight management, physiotherapy, and pain relief medication.\n\n⚠️ **See a doctor if:** Pain is severe, joints are very swollen, or daily activities are significantly affected.",
        "doctor": DOCTORS["orthopaedic"],
    },
    {
        "name": "Pneumonia",
        "keywords": ["cough phlegm", "high fever breathing", "chest pain breathing", "shortness of breath fever", "coughing blood", "rapid breathing", "pneumonia"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing **Pneumonia**.\n\nPneumonia is an infection of the lungs causing cough with phlegm, fever, chest pain when breathing, and shortness of breath.\n\n💊 **What helps:** Bacterial pneumonia is treated with antibiotics. Rest and fluids are important.\n\n⚠️ **See a doctor immediately:** Pneumonia can be serious. Do not delay seeking medical attention.",
        "doctor": DOCTORS["pulmonologist"],
    },
    {
        "name": "Gastroenteritis",
        "keywords": ["diarrhoea", "vomiting stomach", "stomach cramp", "nausea vomiting", "food poisoning", "loose stool", "stomach bug"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing **Gastroenteritis** (Stomach Flu).\n\nIt causes nausea, vomiting, diarrhoea, and stomach cramps. Usually caused by a viral or bacterial infection from contaminated food or water.\n\n💊 **What helps:** Stay hydrated with ORS, rest, and eat bland foods. Avoid dairy and spicy foods until recovered.\n\n⚠️ **See a doctor if:** Symptoms last more than 3 days, there is blood in stool, or you show signs of dehydration.",
        "doctor": DOCTORS["general"],
    },
]

# ── Symptom rules ──────────────────────────────────────────────
SYMPTOM_RULES = [
    {
        "keywords": ["chest pain", "chest tightness", "heart pain", "palpitation", "heart racing", "irregular heartbeat", "angina"],
        "reply": "Chest pain or heart-related symptoms should always be taken seriously. If the pain is severe or spreading to your arm or jaw, please seek emergency care immediately. For non-emergency concerns, our Cardiologist can help.",
        "doctor": DOCTORS["cardiologist"],
    },
    {
        "keywords": ["headache", "migraine", "dizziness", "seizure", "numbness", "tingling", "memory loss", "confusion", "fainting", "vertigo"],
        "reply": "Neurological symptoms like headaches, dizziness, or numbness can have various causes. If symptoms are severe or recurring, a neurological evaluation is recommended.",
        "doctor": DOCTORS["neurologist"],
    },
    {
        "keywords": ["cough", "shortness of breath", "breathing difficulty", "wheezing", "phlegm", "mucus", "breathless", "chest congestion", "lung"],
        "reply": "Respiratory symptoms like coughing, wheezing, or difficulty breathing may indicate infections, allergies, or chronic conditions. Our Pulmonologist can evaluate your symptoms.",
        "doctor": DOCTORS["pulmonologist"],
    },
    {
        "keywords": ["diabetes", "blood sugar", "insulin", "thyroid", "excessive thirst", "frequent urination", "weight gain sudden", "hormonal", "glucose"],
        "reply": "Symptoms related to blood sugar, thyroid function, or unexplained weight changes may indicate an endocrine condition. Our Endocrinologist can provide a proper evaluation.",
        "doctor": DOCTORS["endocrinologist"],
    },
    {
        "keywords": ["joint pain", "back pain", "knee pain", "shoulder pain", "fracture", "bone pain", "muscle pain", "sprain", "arthritis", "spine", "slip disc"],
        "reply": "Joint, muscle, or bone pain can significantly affect quality of life. Our Orthopaedic specialist can assess the cause and recommend treatment.",
        "doctor": DOCTORS["orthopaedic"],
    },
    {
        "keywords": ["fever", "cold", "flu", "infection", "sore throat", "body ache", "fatigue", "diarrhoea", "vomiting", "nausea", "stomach ache", "food poisoning"],
        "reply": "General symptoms like fever, cold, or nausea are commonly caused by infections. Our General Physician can provide a thorough evaluation and treatment.",
        "doctor": DOCTORS["general"],
    },
    {
        "keywords": ["emergency", "urgent", "ambulance", "not breathing", "stroke", "bleeding heavily", "unconscious"],
        "reply": "⚠️ This sounds like a medical emergency. Please call **108** (India ambulance) or **112** immediately. Do not wait for an online consultation.",
        "doctor": None,
    },
    {
        "keywords": ["anxiety", "depression", "stress", "mental health", "panic attack", "insomnia", "sleep problem", "suicidal"],
        "reply": "Mental health is just as important as physical health. If you are feeling overwhelmed or depressed, please know that help is available. In India, you can reach iCall at **9152987821** for free counselling. Our General Physician can also provide an initial evaluation.",
        "doctor": DOCTORS["general"],
    },
]

import random

def is_off_topic(message: str) -> bool:
    msg = message.lower()
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, msg):
            medical_context = ['pain', 'symptom', 'doctor', 'health', 'medicine', 'hospital', 'sick', 'disease', 'appointment', 'file']
            if not any(m in msg for m in medical_context):
                return True
    return False


def check_conversational(message: str) -> Optional[RuleResult]:
    msg = message.lower().strip()
    msg = re.sub(r'[^\w\s\']', ' ', msg)
    for rule in CONVERSATIONAL_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, msg):
                reply = random.choice(rule["replies"])
                return RuleResult(reply=reply, doctor=None, confidence=1.0)
    return None


def check_navigation(message: str) -> Optional[RuleResult]:
    msg = message.lower().strip()
    best_match = None
    best_score = 0
    for rule in NAV_RULES:
        score = sum(1 for kw in rule["keywords"] if kw in msg)
        if score > best_score:
            best_score = score
            best_match = rule
    if best_match and best_score >= 1:
        return RuleResult(
            reply=best_match["reply"],
            doctor=None,
            confidence=1.0,
            redirect=best_match.get("redirect"),
        )
    return None


def predict_disease(message: str) -> Optional[RuleResult]:
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
        return RuleResult(reply=best_match["reply"], doctor=best_match.get("doctor"), confidence=1.0)
    return None


def match_rules(message: str) -> Optional[RuleResult]:
    msg = message.lower().strip()

    # 1. Conversational / emotional
    conv = check_conversational(msg)
    if conv:
        return conv

    # 2. Off-topic
    if is_off_topic(msg):
        reply = random.choice(OFF_TOPIC_REDIRECTS)
        return RuleResult(reply=reply, doctor=None, confidence=1.0, off_topic=True)

    # 3. Navigation / app usage
    nav = check_navigation(msg)
    if nav:
        return nav

    # 4. Disease prediction
    disease = predict_disease(msg)
    if disease:
        return disease

    # 5. Symptom rules
    msg_clean = re.sub(r'[^\w\s]', ' ', msg)
    best_match = None
    best_score = 0
    for rule in SYMPTOM_RULES:
        score = sum(len(kw.split()) for kw in rule["keywords"] if kw in msg_clean)
        if score > best_score:
            best_score = score
            best_match = rule
    if best_match and best_score >= 1:
        return RuleResult(reply=best_match["reply"], doctor=best_match.get("doctor"), confidence=min(1.0, best_score / 3))

    return None