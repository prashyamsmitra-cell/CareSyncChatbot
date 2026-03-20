# rules.py — CareSync AI Rule Engine
# Comprehensive symptom mapping with clinical advice and vague language support

import re
import random
from dataclasses import dataclass, field
from typing import Optional, List

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
    redirect: Optional[str] = None


# ══════════════════════════════════════════════════════════════
# SYMPTOM RULES — comprehensive vague + specific mapping
# Each rule has: keywords (any match counts), reply, doctor, urgency
# ══════════════════════════════════════════════════════════════
SYMPTOM_RULES = [

    # ── ABDOMINAL / STOMACH ───────────────────────────────────
    {
        "keywords": [
            "stomach pain", "stomach ache", "tummy ache", "tummy pain", "belly pain", "belly ache",
            "abdominal pain", "abdominal cramp", "stomach cramp", "gut pain", "i feel sick",
            "my stomach hurts", "stomach is hurting", "pain in stomach", "pain in my stomach",
            "pain in belly", "stomach is killing me", "stomach issues", "stomach problem",
            "gastric pain", "gastric issue", "indigestion", "bloating", "feel bloated",
            "my tummy", "tummy problem", "upset stomach", "stomach discomfort",
            "nausea", "feel nauseous", "feeling nauseous", "want to vomit", "feel like vomiting",
            "vomiting", "throwing up", "threw up", "diarrhoea", "diarrhea", "loose motions",
            "loose stool", "food poisoning", "food intoxication", "acidity", "acid reflux",
            "heartburn", "burping", "flatulence", "gas problem",
        ],
        "reply": (
            "Stomach and abdominal pain can have many causes ranging from mild indigestion to more serious conditions.\n\n"
            "🟡 **If the pain is mild or occasional:** It may be due to gas, acidity, or indigestion. "
            "Try staying hydrated, avoiding spicy or oily food, and taking an antacid. "
            "If you feel nauseous or have vomiting, rest and sip water slowly.\n\n"
            "🔴 **If the pain is persistent, severe, or comes with fever:** Please visit a "
            "**General Physician** or a nearby multispeciality clinic as soon as possible. "
            "Persistent stomach pain should not be ignored as it may indicate infections, gastritis, or appendicitis.\n\n"
            "🚨 **Go to emergency immediately if:** The pain is sudden and severe, you have blood in stool or vomit, "
            "or the pain is concentrated on the lower right side of your abdomen."
        ),
        "doctor": DOCTORS["general"],
        "urgency": "moderate",
    },

    # ── CHEST / HEART ─────────────────────────────────────────
    {
        "keywords": [
            "chest pain", "chest ache", "chest tightness", "chest pressure", "chest discomfort",
            "my chest hurts", "pain in chest", "pain in my chest", "chest is hurting",
            "heart pain", "heart ache", "heart hurts", "my heart hurts", "heart racing",
            "palpitation", "heart pounding", "heart fluttering", "irregular heartbeat",
            "heart skipping", "angina", "shortness of breath heart", "left arm pain",
            "pain radiating to arm", "jaw pain with chest", "sweating chest pain",
        ],
        "reply": (
            "Chest pain and heart-related symptoms are always taken seriously in medicine.\n\n"
            "🚨 **Seek emergency care immediately if:** The pain is severe, crushing, or spreads to your left arm, "
            "jaw, or neck — especially with sweating, nausea, or breathlessness. Call **108** right away. "
            "These could be signs of a heart attack.\n\n"
            "🟡 **If the pain is mild, occasional, or related to stress:** It may be due to muscle strain, "
            "acid reflux, or anxiety. However, chest pain should never be self-diagnosed.\n\n"
            "Please visit a **Cardiologist** for a proper evaluation including an ECG. "
            "Do not delay — early assessment can be life-saving."
        ),
        "doctor": DOCTORS["cardiologist"],
        "urgency": "high",
    },

    # ── HEAD / BRAIN ──────────────────────────────────────────
    {
        "keywords": [
            "headache", "head pain", "head ache", "head hurts", "my head hurts", "head is pounding",
            "head is throbbing", "migraine", "severe headache", "worst headache", "constant headache",
            "headache every day", "headache for days", "headache won't go away",
            "dizziness", "dizzy", "feel dizzy", "feeling dizzy", "spinning", "room spinning",
            "vertigo", "lightheaded", "light headed", "fainting", "fainted", "blacked out",
            "seizure", "convulsion", "fits", "epilepsy", "numbness", "tingling sensation",
            "memory loss", "forgetful", "confusion", "cannot concentrate", "brain fog",
            "vision blurred", "blurred vision", "seeing double", "sudden vision loss",
            "slurred speech", "difficulty speaking", "facial drooping",
        ],
        "reply": (
            "Head pain and neurological symptoms can range from tension headaches to more serious conditions.\n\n"
            "🟢 **For mild headaches:** Rest in a quiet, dark room, stay hydrated, and take paracetamol if needed. "
            "Stress and dehydration are the most common causes.\n\n"
            "🟡 **If headaches are frequent, severe, or recurring:** Please visit a **Neurologist** "
            "or a nearby multispeciality clinic. Recurring headaches need proper diagnosis.\n\n"
            "🚨 **Go to emergency immediately if:** The headache is sudden and the worst of your life, "
            "accompanied by vision changes, slurred speech, facial drooping, numbness, or confusion. "
            "These may be signs of a stroke — call **108** immediately."
        ),
        "doctor": DOCTORS["neurologist"],
        "urgency": "moderate",
    },

    # ── BREATHING / LUNGS ─────────────────────────────────────
    {
        "keywords": [
            "breathing problem", "breathing difficulty", "difficulty breathing", "hard to breathe",
            "can't breathe", "cannot breathe", "shortness of breath", "short of breath",
            "out of breath", "breathless", "breathlessness", "feeling breathless",
            "chest congestion", "congested chest", "wheezing", "wheeze", "rattling breath",
            "cough", "dry cough", "wet cough", "coughing", "coughing a lot", "persistent cough",
            "cough won't stop", "phlegm", "mucus", "sputum", "coughing blood", "blood in cough",
            "asthma", "asthma attack", "inhaler", "lung pain", "lung problem",
            "pneumonia", "bronchitis", "respiratory", "choking",
        ],
        "reply": (
            "Breathing difficulties and respiratory symptoms should be taken seriously.\n\n"
            "🟢 **For mild cough or congestion:** Stay hydrated, use steam inhalation, and rest. "
            "A dry cough may be due to allergies or a viral infection and usually resolves in 1–2 weeks.\n\n"
            "🟡 **If you have persistent cough, wheezing, or mild breathlessness:** "
            "Please visit a **Pulmonologist** (lung specialist) or a nearby multispeciality clinic. "
            "These may indicate asthma, bronchitis, or an infection that needs treatment.\n\n"
            "🚨 **Seek emergency care immediately if:** You are severely breathless at rest, "
            "coughing blood, or your lips or fingertips are turning blue. Call **108** right away."
        ),
        "doctor": DOCTORS["pulmonologist"],
        "urgency": "moderate",
    },

    # ── JOINTS / BONES / MUSCLES ──────────────────────────────
    {
        "keywords": [
            "joint pain", "joints hurt", "my joints hurt", "painful joints", "joint swelling",
            "swollen joint", "stiff joints", "joint stiffness", "knee pain", "knee hurts",
            "my knee hurts", "knee swelling", "knee is swollen", "back pain", "backache",
            "lower back pain", "upper back pain", "back hurts", "my back is killing me",
            "spine pain", "spinal pain", "slip disc", "slipped disc", "disc problem",
            "shoulder pain", "shoulder hurts", "frozen shoulder", "neck pain", "neck stiffness",
            "stiff neck", "hip pain", "hip hurts", "ankle pain", "ankle swelling", "wrist pain",
            "bone pain", "fracture", "broken bone", "sprain", "muscle pain", "muscle ache",
            "body ache", "body pain", "all over pain", "pain everywhere", "arthritis",
            "rheumatoid", "gout", "sports injury", "workout injury", "gym injury",
        ],
        "reply": (
            "Joint, muscle, and bone pain can significantly affect your daily life.\n\n"
            "🟢 **For mild muscle soreness or minor sprains:** Rest the affected area, apply ice for 20 minutes, "
            "and take an anti-inflammatory like ibuprofen. Avoid strenuous activity for a few days.\n\n"
            "🟡 **If the pain is persistent, recurring, or affecting your movement:** "
            "Please visit an **Orthopaedic specialist** or a nearby multispeciality clinic. "
            "Conditions like arthritis, slip disc, or ligament injuries need proper imaging and diagnosis.\n\n"
            "🚨 **Go to emergency if:** You have severe pain after a fall or accident, "
            "a visible deformity, or cannot bear weight on a limb at all."
        ),
        "doctor": DOCTORS["orthopaedic"],
        "urgency": "moderate",
    },

    # ── DIABETES / ENDOCRINE ──────────────────────────────────
    {
        "keywords": [
            "diabetes", "diabetic", "blood sugar", "high blood sugar", "low blood sugar",
            "sugar level", "sugar is high", "sugar is low", "glucose", "insulin",
            "always thirsty", "excessive thirst", "drinking a lot of water", "urinating a lot",
            "frequent urination", "peeing a lot", "passing urine frequently",
            "thyroid", "thyroid problem", "thyroid issue", "hyperthyroid", "hypothyroid",
            "weight gain suddenly", "weight loss suddenly", "unexplained weight",
            "always tired", "extreme fatigue", "exhausted all the time", "no energy",
            "hormone problem", "hormonal imbalance", "hormonal issue", "pcos", "pcod",
            "adrenal", "metabolic", "tingling in feet", "tingling in hands", "slow healing wound",
        ],
        "reply": (
            "Your symptoms may be related to blood sugar, thyroid, or hormonal conditions — "
            "all of which are very manageable once properly diagnosed.\n\n"
            "🟢 **If you suspect diabetes:** Common signs include excessive thirst, frequent urination, "
            "unexplained fatigue, and slow-healing wounds. A simple fasting blood glucose test can confirm it.\n\n"
            "🟡 **Please visit an Endocrinologist** or a nearby multispeciality clinic for blood tests. "
            "Early diagnosis of diabetes and thyroid conditions leads to much better outcomes with the right medication and lifestyle changes.\n\n"
            "🚨 **If blood sugar is very low (hypoglycemia):** You may feel shaky, sweaty, or confused. "
            "Immediately consume sugar — a glucose tablet, juice, or sweet — and seek medical help."
        ),
        "doctor": DOCTORS["endocrinologist"],
        "urgency": "moderate",
    },

    # ── FEVER / GENERAL ILLNESS ───────────────────────────────
    {
        "keywords": [
            "fever", "high fever", "temperature", "high temperature", "running a fever",
            "feeling hot", "chills", "shivering", "cold and shivering", "cold and fever",
            "flu", "influenza", "cold", "common cold", "runny nose", "stuffy nose",
            "blocked nose", "nasal congestion", "sore throat", "throat pain", "throat hurts",
            "throat infection", "tonsils", "tonsillitis", "viral", "viral fever", "viral infection",
            "bacterial infection", "infection", "malaria", "dengue", "typhoid", "covid",
            "weakness", "feel weak", "body weakness", "not feeling well", "feeling unwell",
            "generally unwell", "under the weather", "feeling off", "don't feel good",
            "feel terrible", "feel awful", "feeling sick", "sick", "ill", "falling sick",
            "fell sick", "got sick", "loss of appetite", "not hungry", "can't eat",
        ],
        "reply": (
            "Fever and general illness are most commonly caused by viral or bacterial infections.\n\n"
            "🟢 **For mild fever (below 38.5°C / 101°F):** Rest, stay well hydrated, and take paracetamol "
            "to bring the fever down. Avoid cold water baths. Monitor your temperature every few hours.\n\n"
            "🟡 **If fever persists beyond 3 days, is very high, or comes with severe symptoms:** "
            "Please visit a **General Physician** or a nearby multispeciality clinic immediately. "
            "Infections like dengue, malaria, and typhoid require blood tests for diagnosis and specific treatment.\n\n"
            "🚨 **Go to emergency if:** Fever is above 40°C (104°F), you have difficulty breathing, "
            "a severe rash, or you are unable to stay awake."
        ),
        "doctor": DOCTORS["general"],
        "urgency": "moderate",
    },

    # ── SKIN ──────────────────────────────────────────────────
    {
        "keywords": [
            "skin rash", "rash", "itching", "itchy skin", "skin itch", "skin problem",
            "skin issue", "allergic reaction", "allergy", "hives", "eczema", "psoriasis",
            "acne", "pimples", "boil", "wound", "cut", "bruise", "skin infection",
            "redness on skin", "dry skin", "flaky skin", "skin peeling",
        ],
        "reply": (
            "Skin conditions can range from mild allergies to infections that need treatment.\n\n"
            "🟢 **For mild rashes or itching:** It may be due to an allergic reaction, heat, or dry skin. "
            "An antihistamine like cetirizine can help with itching. Avoid scratching.\n\n"
            "🟡 **If the rash is spreading, has blisters, or is accompanied by fever:** "
            "Please visit a **General Physician** or a nearby multispeciality clinic. "
            "Skin infections and severe allergic reactions need proper treatment.\n\n"
            "🚨 **Go to emergency if:** You have a sudden widespread rash with difficulty breathing — "
            "this may be anaphylaxis, a life-threatening allergic reaction."
        ),
        "doctor": DOCTORS["general"],
        "urgency": "moderate",
    },

    # ── EYES ──────────────────────────────────────────────────
    {
        "keywords": [
            "eye pain", "eye ache", "eyes hurt", "my eyes hurt", "eye problem", "eye issue",
            "red eye", "pink eye", "eye infection", "conjunctivitis", "eye discharge",
            "blurry vision", "vision problem", "can't see clearly", "vision loss",
            "eye strain", "watery eyes", "dry eyes", "itchy eyes",
        ],
        "reply": (
            "Eye symptoms should be evaluated promptly to prevent complications.\n\n"
            "🟢 **For mild eye strain or dryness:** Rest your eyes, avoid screens for a while, "
            "and use lubricating eye drops.\n\n"
            "🟡 **For red eyes, discharge, or infection:** Please visit a **General Physician** "
            "or an eye specialist at a nearby multispeciality clinic. Eye infections like conjunctivitis "
            "are contagious and need antibiotic eye drops.\n\n"
            "🚨 **Seek emergency care if:** You have sudden vision loss, severe eye pain, "
            "or an eye injury. These can threaten your sight."
        ),
        "doctor": DOCTORS["general"],
        "urgency": "moderate",
    },

    # ── MENTAL HEALTH ─────────────────────────────────────────
    {
        "keywords": [
            "anxiety", "anxious", "panic attack", "panic", "stressed", "stress",
            "depression", "depressed", "feeling low", "feeling sad", "feel hopeless",
            "hopeless", "worthless", "want to die", "suicidal", "self harm",
            "mental health", "mental issue", "mental problem", "overthinking",
            "cannot sleep", "insomnia", "sleep problem", "not sleeping", "sleeping too much",
            "mood swings", "irritable", "anger issues", "feeling empty", "no motivation",
        ],
        "reply": (
            "Mental health is just as important as physical health, and reaching out is a sign of strength. 💚\n\n"
            "🟢 **For stress and anxiety:** Try deep breathing, regular exercise, and limiting caffeine. "
            "Talk to someone you trust about how you're feeling.\n\n"
            "🟡 **If you've been feeling low, anxious, or unable to function for more than 2 weeks:** "
            "Please speak to a **General Physician** who can refer you to a mental health specialist. "
            "In India, you can also call **iCall at 9152987821** for free, confidential counselling.\n\n"
            "🚨 **If you are having thoughts of harming yourself:** Please call **iCall (9152987821)** "
            "or **Vandrevala Foundation (1860-2662-345)** immediately. You are not alone and help is available."
        ),
        "doctor": DOCTORS["general"],
        "urgency": "high",
    },

    # ── URINARY ───────────────────────────────────────────────
    {
        "keywords": [
            "uti", "urinary infection", "urinary tract", "burning urination", "burning while urinating",
            "pain while urinating", "painful urination", "blood in urine", "dark urine",
            "urine problem", "kidney pain", "kidney stone", "back pain with urination",
        ],
        "reply": (
            "Urinary symptoms like burning or pain during urination are usually signs of a urinary tract infection (UTI).\n\n"
            "🟢 **Immediate steps:** Drink plenty of water to flush out bacteria. Avoid holding urine in for long.\n\n"
            "🟡 **Please visit a General Physician** or a nearby multispeciality clinic promptly. "
            "UTIs need antibiotic treatment and will not resolve on their own. "
            "If left untreated, they can spread to the kidneys.\n\n"
            "🚨 **Go to emergency if:** You have severe back or flank pain, high fever with chills, "
            "or blood in your urine — these may indicate a kidney infection."
        ),
        "doctor": DOCTORS["general"],
        "urgency": "moderate",
    },

    # ── EMERGENCY CATCH-ALL ───────────────────────────────────
    {
        "keywords": [
            "emergency", "urgent", "help me", "serious", "very bad", "extremely painful",
            "unbearable pain", "can't take it", "ambulance", "not breathing", "stopped breathing",
            "unconscious", "fainted", "collapsed", "stroke", "heart attack",
            "heavy bleeding", "bleeding a lot", "accident", "injured badly",
        ],
        "reply": (
            "⚠️ This sounds like it could be a medical emergency.\n\n"
            "Please call **108** (national ambulance) or **112** (emergency services) immediately.\n\n"
            "Do not drive yourself — ask someone to take you to the nearest emergency room "
            "or wait for the ambulance. Stay calm and keep the person awake and still if possible."
        ),
        "doctor": None,
        "urgency": "emergency",
    },
]


# ── Navigation rules ───────────────────────────────────────────
NAV_RULES = [
    {
        "keywords": ["upload", "add file", "share file", "submit file", "upload medical",
                     "how do i upload", "where to upload", "upload report", "upload prescription"],
        "reply": "Sure! To upload your medical files, head over to the **Upload** tab on your dashboard. You can drag and drop files or click to browse — supports PDFs, images, and scans.",
        "redirect": "upload",
        "exclude": ["appointment", "doctor", "symptom", "pain", "fever"],
    },
    {
        "keywords": ["book", "appointment", "schedule", "see a doctor", "how do i book",
                     "make appointment", "how to book", "book slot", "book doctor", "visit doctor"],
        "reply": "Of course! To book an appointment, go to the **Appointments** tab on your dashboard. Click **Book Appointment**, choose your doctor, pick a date, and select an available time slot.",
        "redirect": "appointments",
        "exclude": ["cancel", "symptom", "pain", "fever", "hurt"],
    },
    {
        "keywords": ["cancel appointment", "cancel booking", "reschedule appointment"],
        "reply": "To cancel an appointment, go to the **Appointments** tab and click the cancel button next to the appointment. Only Pending or Confirmed appointments can be cancelled.",
        "redirect": "appointments",
        "exclude": [],
    },
    {
        "keywords": ["my files", "view files", "my reports", "my prescriptions",
                     "download file", "where are my files", "see files", "find files"],
        "reply": "Your uploaded files are all in the **Files** tab on your dashboard. You can view, download, or delete any file from there.",
        "redirect": "files",
        "exclude": [],
    },
    {
        "keywords": ["otp", "doctor access", "give doctor access", "doctor portal",
                     "share records", "pid", "patient id", "my pid"],
        "reply": "To give your doctor access to your records, share your **Patient ID (PID)** with them. Your doctor enters it in the Doctor Portal, an OTP is sent to your phone or appears in your Appointments tab, and you share it verbally with the doctor for 2-hour access.",
        "redirect": "appointments",
        "exclude": [],
    },
    {
        "keywords": ["overview", "home", "my profile", "my stats", "my bmi", "my weight", "my height", "my blood type"],
        "reply": "Your health overview including BMI, weight, height, blood type, vital signs, and appointment summary is all on the **Overview** tab of your dashboard.",
        "redirect": "overview",
        "exclude": [],
    },
]

# ── Conversational rules ───────────────────────────────────────
CONVERSATIONAL_RULES = [
    {
        "patterns": [r'\bhello\b', r'\bhi\b', r'\bhey\b', r'\bgood morning\b',
                     r'\bgood afternoon\b', r'\bgood evening\b', r'\bgreetings\b'],
        "replies": [
            "Hello! 👋 Welcome to CareSync. I'm your personal health assistant. Whether you have a symptom to check, need to find the right doctor, or just have a health question — I'm here to help. How are you feeling today?",
            "Hi there! 😊 I'm CareSync AI. Describe your symptoms and I'll help you understand what's going on and which specialist you should see. What can I do for you?",
            "Hey! Good to see you. I'm here to help with any health concerns. Tell me what's bothering you and I'll point you in the right direction. 🩺",
        ],
    },
    {
        "patterns": [r'\bhow are you\b', r'\bhow do you do\b', r'\bare you okay\b'],
        "replies": [
            "I'm doing great, thank you for asking! 😊 More importantly — how are *you* feeling today? Any symptoms or concerns I can help with?",
            "All good on my end! How about you? If something's been bothering you health-wise, I'm here to help.",
        ],
    },
    {
        "patterns": [r'\bthank\b', r'\bthanks\b', r'\bthank you\b', r'\bthx\b', r'\bgrateful\b'],
        "replies": [
            "You're very welcome! 😊 Take care of yourself and don't hesitate to reach out if you have more questions.",
            "Happy to help! That's what I'm here for. 🙏 Wishing you good health!",
            "Of course! Feel free to come back anytime. Stay well! 💚",
        ],
    },
    {
        "patterns": [r'\bsorry\b', r'\bapologi[sz]e\b', r'\bmy bad\b'],
        "replies": [
            "No worries at all! 😊 How can I help you today?",
            "Not a problem! Is there anything health-related I can assist you with?",
        ],
    },
    {
        "patterns": [r'\bbye\b', r'\bgoodbye\b', r'\bsee you\b', r'\btake care\b', r'\bgood night\b'],
        "replies": [
            "Take care! 💚 Remember, I'm always here whenever you have a health question. Stay well!",
            "Goodbye! Wishing you good health. 😊 Come back anytime you need help.",
        ],
    },
    {
        "patterns": [r'\bi hate\b', r'\bthis is stupid\b', r'\buseless\b', r'\bterrible\b', r'\bawful\b'],
        "replies": [
            "I'm sorry to hear that. 😔 I genuinely want to be helpful. If there's a health question I can answer more clearly, please let me know.",
            "I understand your frustration. I'll do my best to help — what health concern can I assist you with?",
        ],
    },
    {
        "patterns": [r'\bwho are you\b', r'\bwhat are you\b', r'\bwhat can you do\b', r'\byour name\b'],
        "replies": [
            "I'm CareSync AI — your personal clinical health assistant. 🏥\n\nHere's what I can help you with:\n• 🩺 Understand your symptoms and predict possible conditions\n• 👨‍⚕️ Suggest the right specialist for your concern\n• 📁 Guide you to upload and manage medical files\n• 📅 Help you book or manage appointments\n• 💊 Answer general health and medication questions\n\nWhat can I help you with today?",
        ],
    },
    {
        "patterns": [r'\bhelp\b', r'\bwhat can i ask\b', r'\bwhere to start\b'],
        "replies": [
            "Of course! Here's what I can help you with:\n\n🩺 **Symptoms** — Describe how you're feeling and I'll suggest the right doctor\n📅 **Appointments** — Ask how to book, cancel, or manage appointments\n📁 **Files** — Guide you to upload or view your medical records\n🔐 **Doctor Access** — Learn how to share records with your doctor\n💊 **Health Questions** — Ask about conditions, medications, or healthy living\n\nWhat's on your mind?",
        ],
    },
]

OFF_TOPIC_PATTERNS = [
    r'\bweather\b', r'\bsport[s]?\b', r'\bfootball\b', r'\bcricket\b', r'\bipl\b',
    r'\bnews\b', r'\bpolitics?\b', r'\bmovie[s]?\b', r'\bfilm[s]?\b',
    r'\bmusic\b', r'\bsong[s]?\b', r'\brecipe[s]?\b', r'\bcook(ing)?\b',
    r'\bmath\b', r'\bcalculate\b', r'\bcode\b', r'\bprogramming\b',
    r'\bjoke[s]?\b', r'\bfunny\b', r'\bpoem\b', r'\bstory\b',
    r'\binstagram\b', r'\bfacebook\b', r'\bwhatsapp\b', r'\btwitter\b',
    r'\bhoroscope\b', r'\bastrology\b', r'\bgame[s]?\b',
    r'\btravel\b', r'\bhotel\b', r'\bflight\b',
    r'\bcrypto\b', r'\bbitcoin\b', r'\bstock[s]?\b',
]

OFF_TOPIC_REPLIES = [
    "That's a bit outside my expertise! 😄 I'm a health assistant — topics like that are beyond what I can help with. But if you have any health concerns, symptoms, or need to book an appointment, I'm all yours! What medical assistance can I provide?",
    "Oops, that's off the beaten path for me! 🏥 I specialise in health and medical queries. Let's get back on track — do you have a symptom or health question I can help with?",
    "Ha, I wish I could help with that, but health is my one true calling! 😊 Tell me about any medical concerns you have and I'll do my best to assist.",
    "That's not quite my area — I'm built specifically for health and medical guidance. 🩺 Do you have any symptoms or health questions I can help you with?",
]

DISEASE_RULES = [
    {
        "name": "Common Cold",
        "keywords": ["runny nose", "stuffy nose", "sneezing", "sore throat", "mild fever", "nasal congestion"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing a **Common Cold**.\n\nIt is caused by a viral infection and usually resolves within 7–10 days.\n\n💊 **What helps:** Rest, fluids, steam inhalation, and paracetamol for fever. Avoid antibiotics — they don't work against viruses.\n\n⚠️ **See a doctor if:** Fever exceeds 39°C, symptoms worsen after 5 days, or breathing becomes difficult.",
        "doctor": DOCTORS["general"],
    },
    {
        "name": "Influenza",
        "keywords": ["high fever", "body ache", "chills", "sudden fever", "muscle pain", "extreme fatigue"],
        "required": 3,
        "reply": "Based on your symptoms, you may be experiencing **Influenza (Flu)**.\n\nThe flu comes on suddenly with high fever, body aches, and extreme fatigue — unlike a cold.\n\n💊 **What helps:** Rest, fluids, and paracetamol. Antivirals work best if taken early.\n\n⚠️ **See a doctor if:** Fever is very high, breathing is difficult, or symptoms don't improve after 5 days.",
        "doctor": DOCTORS["general"],
    },
    {
        "name": "Migraine",
        "keywords": ["throbbing headache", "one side head", "light sensitivity", "sound sensitivity", "nausea headache", "migraine"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing a **Migraine**.\n\nMigraines cause intense throbbing pain on one side of the head, often with nausea and sensitivity to light and sound.\n\n💊 **What helps:** Rest in a dark quiet room, hydration, ibuprofen or prescribed triptans.\n\n⚠️ **See a neurologist if:** Migraines are frequent, very severe, or come with numbness or slurred speech.",
        "doctor": DOCTORS["neurologist"],
    },
    {
        "name": "Asthma",
        "keywords": ["wheezing", "chest tightness", "cough night", "breathless walking", "inhaler", "asthma"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing **Asthma**.\n\nAsthma causes wheezing, breathlessness, and chest tightness — especially at night or during exercise.\n\n💊 **What helps:** Avoiding triggers (dust, smoke, pollen), reliever inhalers for attacks, preventer inhalers long-term.\n\n⚠️ **See a pulmonologist if:** Symptoms are frequent or your inhaler isn't helping.",
        "doctor": DOCTORS["pulmonologist"],
    },
    {
        "name": "Type 2 Diabetes",
        "keywords": ["excessive thirst", "frequent urination", "blurred vision", "slow healing", "tingling feet", "high sugar"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing signs of **Type 2 Diabetes**.\n\nKey signs include excessive thirst, frequent urination, fatigue, and slow-healing wounds.\n\n💊 **What helps:** Diet low in sugar, regular exercise, weight management, and prescribed medication.\n\n⚠️ **See an endocrinologist:** A fasting blood glucose test can confirm the diagnosis.",
        "doctor": DOCTORS["endocrinologist"],
    },
    {
        "name": "Gastroenteritis",
        "keywords": ["diarrhoea", "vomiting stomach", "stomach cramp", "nausea vomiting", "food poisoning", "loose stool"],
        "required": 2,
        "reply": "Based on your symptoms, you may be experiencing **Gastroenteritis** (Stomach Flu).\n\nIt causes nausea, vomiting, diarrhoea, and cramps from a viral or bacterial infection.\n\n💊 **What helps:** ORS (oral rehydration solution), rest, and bland food like rice and toast.\n\n⚠️ **See a doctor if:** Symptoms last more than 3 days, there is blood in stool, or you show signs of dehydration.",
        "doctor": DOCTORS["general"],
    },
]


def is_off_topic(message: str) -> bool:
    msg = message.lower()
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, msg):
            medical = ['pain', 'symptom', 'doctor', 'health', 'medicine', 'hospital',
                       'sick', 'disease', 'appointment', 'file', 'hurt', 'ache', 'fever']
            if not any(m in msg for m in medical):
                return True
    return False


def check_conversational(message: str) -> Optional[RuleResult]:
    msg = message.lower().strip()
    msg_clean = re.sub(r'[^\w\s\']', ' ', msg)
    for rule in CONVERSATIONAL_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, msg_clean):
                return RuleResult(reply=random.choice(rule["replies"]), doctor=None, confidence=1.0)
    return None


def check_navigation(message: str) -> Optional[RuleResult]:
    msg = message.lower().strip()
    best_match = None
    best_score = 0
    for rule in NAV_RULES:
        excludes = rule.get("exclude", [])
        if any(ex in msg for ex in excludes):
            continue
        score = sum(1 for kw in rule["keywords"] if kw in msg)
        if score > best_score:
            best_score = score
            best_match = rule
    if best_match and best_score >= 1:
        return RuleResult(reply=best_match["reply"], doctor=None, confidence=1.0, redirect=best_match.get("redirect"))
    return None


def predict_disease(message: str) -> Optional[RuleResult]:
    msg = re.sub(r'[^\w\s]', ' ', message.lower())
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


def match_symptom_rules(message: str) -> Optional[RuleResult]:
    msg = re.sub(r'[^\w\s]', ' ', message.lower())
    best_match = None
    best_score = 0
    for rule in SYMPTOM_RULES:
        score = sum(1 for kw in rule["keywords"] if kw in msg)
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


def match_rules(message: str) -> Optional[RuleResult]:
    # 1. Conversational
    conv = check_conversational(message)
    if conv:
        return conv

    # 2. Off-topic
    if is_off_topic(message):
        return RuleResult(reply=random.choice(OFF_TOPIC_REPLIES), doctor=None, confidence=1.0, off_topic=True)

    # 3. Navigation
    nav = check_navigation(message)
    if nav:
        return nav

    # 4. Disease prediction (multi-symptom)
    disease = predict_disease(message)
    if disease:
        return disease

    # 5. Symptom rules (vague + specific)
    symptom = match_symptom_rules(message)
    if symptom:
        return symptom

    return None