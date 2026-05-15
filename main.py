# main.py — CareSync AI Chatbot Service (FastAPI)
# Hybrid rule-based + Gemini 1.5 Flash chatbot
# Deploy on Railway as a separate service from the Node.js backend

import os
import logging
from datetime import date, datetime, timedelta
from threading import Lock
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rules import match_rules
from gemini import GeminiRateLimitError, ask_gemini

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="CareSync AI Chatbot",
    description="Hybrid rule-based + Gemini 1.5 Flash health assistant",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restricted by API key in practice
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ── Auth ──────────────────────────────────────────────────────
CARESYNC_API_KEY = os.getenv("CARESYNC_API_KEY", "")
DAILY_CHAT_LIMIT = int(os.getenv("DAILY_CHAT_LIMIT", "200"))
PER_MINUTE_CHAT_LIMIT = int(os.getenv("PER_MINUTE_CHAT_LIMIT", "10"))
_usage_lock = Lock()
_daily_usage = {}
_minute_usage = {}
DAILY_LIMIT_REACHED_MESSAGE = "Daily chat limit reached. Please try again tomorrow."
MINUTE_LIMIT_REACHED_MESSAGE = "You're sending messages too quickly. Please wait a minute and try again."


def verify_key(x_api_key: Optional[str]):
    if CARESYNC_API_KEY and x_api_key != CARESYNC_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")


def check_and_record_limits(pid: str) -> str:
    today = date.today().isoformat()
    now = datetime.utcnow()
    minute_window_start = now - timedelta(minutes=1)

    with _usage_lock:
        minute_record = _minute_usage.get(pid)

        if not minute_record:
            _minute_usage[pid] = {"timestamps": [now]}
        else:
            timestamps = [
                timestamp
                for timestamp in minute_record["timestamps"]
                if timestamp > minute_window_start
            ]

            if len(timestamps) >= PER_MINUTE_CHAT_LIMIT:
                minute_record["timestamps"] = timestamps
                return "minute_limit"

            timestamps.append(now)
            minute_record["timestamps"] = timestamps

        daily_record = _daily_usage.get(pid)

        if not daily_record or daily_record["date"] != today:
            _daily_usage[pid] = {"date": today, "count": 1}
            return "ok"

        if daily_record["count"] >= DAILY_CHAT_LIMIT:
            return "daily_limit"

        daily_record["count"] += 1
        return "ok"


# ── Request / Response models ─────────────────────────────────
class HistoryMessage(BaseModel):
    role: str       # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    pid: str
    message: str
    history: List[HistoryMessage] = []


class ChatResponse(BaseModel):
    reply: str
    source: str         # "rule" or "gemini"
    doctor: Optional[dict] = None
    redirect: Optional[str] = None  # tab to navigate to: overview/files/upload/appointments


# ── Health check ──────────────────────────────────────────────
@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "CareSync AI Chatbot",
        "version": "1.0.0",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
    }

# ── Wake-up ping — responds instantly, no auth needed ─────────
@app.get("/wake")
def wake():
    return {"awake": True}


# ── Main chat endpoint ─────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    x_api_key: Optional[str] = Header(default=None)
):
    verify_key(x_api_key)

    pid = req.pid.strip()
    if not pid:
        raise HTTPException(status_code=400, detail="PID is required.")

    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    limit_status = check_and_record_limits(pid)
    if limit_status == "daily_limit":
        log.info(f"[{pid}] Daily chat limit reached")
        return ChatResponse(
            reply=DAILY_LIMIT_REACHED_MESSAGE,
            source="rule",
            doctor=None,
            redirect="appointments",
        )
    if limit_status == "minute_limit":
        log.info(f"[{pid}] Per-minute chat limit reached")
        return ChatResponse(
            reply=MINUTE_LIMIT_REACHED_MESSAGE,
            source="rule",
            doctor=None,
            redirect=None,
        )

    log.info(f"[{pid}] User: {message[:80]}")

    # ── Step 1: Try rule-based engine first ───────────────────
    rule_result = match_rules(message)

    if rule_result:
        log.info(f"[{pid}] Rule matched (confidence={rule_result.confidence:.1f}, off_topic={rule_result.off_topic})")
        if rule_result.off_topic or rule_result.confidence >= 0.4:
            return ChatResponse(
                reply=rule_result.reply,
                source="rule",
                doctor=rule_result.doctor,
                redirect=getattr(rule_result, 'redirect', None),
            )

    # ── Step 2: Fall back to Gemini ───────────────────────────
    if not os.getenv("GEMINI_API_KEY"):
        # Gemini not configured — use rule result if we have one, else generic reply
        if rule_result:
            return ChatResponse(
                reply=rule_result.reply,
                source="rule",
                doctor=rule_result.doctor,
                redirect=getattr(rule_result, "redirect", None),
            )
        return ChatResponse(
            reply=(
                "I'm not sure I fully understand your question. Could you describe your symptoms "
                "in more detail? For example, where is the pain, how long have you had it, and "
                "how severe is it? I'll do my best to help or suggest the right doctor."
            ),
            source="rule",
            doctor=None,
        )

    history = [{"role": m.role, "content": m.content} for m in req.history]

    try:
        gemini_reply = await ask_gemini(message, history)
        log.info(f"[{pid}] Gemini replied ({len(gemini_reply)} chars)")
        return ChatResponse(reply=gemini_reply, source="gemini", doctor=None)

    except GeminiRateLimitError as e:
        log.warning(f"[{pid}] Gemini rate limited: {e}")
        return ChatResponse(
            reply=DAILY_LIMIT_REACHED_MESSAGE,
            source="rule",
            doctor=None,
            redirect="appointments",
        )

    except Exception as e:
        log.error(f"[{pid}] Gemini error: {e}")
        if rule_result:
            return ChatResponse(
                reply=rule_result.reply,
                source="rule",
                doctor=rule_result.doctor,
                redirect=getattr(rule_result, "redirect", None),
            )
        return ChatResponse(
            reply=(
                "I can help you with health questions, symptom checking, and finding the right doctor. "
                "Could you describe your symptoms or health concern in more detail?"
            ),
            source="rule",
            doctor=None,
        )
