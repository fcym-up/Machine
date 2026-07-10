"""与 Machine 对话的 API — 安全隔离版。每个外部依赖都有独立的异常保护。"""
import json, re
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import SessionLocal
from app.core.llm import chat
from app.models.event import Event
from app.models.conversation import ConversationMessage

router = APIRouter(prefix="/conversation", tags=["conversation"])

# === In-memory conversation cache ===
conv_memory: dict = {}
MAX_MESSAGES_PER_SESSION = 100
MAX_CACHE_TURNS = 10

class ChatRequest(BaseModel):
    message: str = Field(..., description="对 Machine 说的话")

class ChatResponse(BaseModel):
    reply: str
    emotion: str
    confidence: float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
#  SAFE HELPERS — each external call wrapped in try/except
# ============================================================

def _safe_get_emotion(db: Session) -> str:
    """Get emotion from v2 engine, returns fallback on any error."""
    try:
        from app.algorithms.emotion_engine import get_current_emotion
        state = get_current_emotion(db)
        if state and hasattr(state, "primary_emotion"):
            return state.primary_emotion
    except Exception:
        pass
    return "平静"

def _safe_get_activity_summary(db: Session) -> dict:
    """Get activity counts from recent events. Returns empty dict on error."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=4)
        events = db.query(Event).filter(
            Event.event_type == "user-action",
            Event.created_at >= cutoff,
        ).all()
        summary = {}
        for e in events:
            payload = e.payload if isinstance(e.payload, dict) else {}
            cat = payload.get("category", "other")
            summary[cat] = summary.get(cat, 0) + 1
        return summary
    except Exception:
        return {}

def _safe_inject_emotion_signal(db: Session, emotion: str, confidence: float, msg: str):
    """Inject conversation signal into emotion v2. Silently fails on error."""
    try:
        from app.services.emotion_collector import inject_conversation_signal
        from app.algorithms.emotion_engine import compute_current
        inject_conversation_signal(
            db, emotion_label=emotion, confidence=confidence,
            payload={"factor": f'管理员说: "{msg[:50]}"', "raw": msg[:200]},
        )
        compute_current(db)
    except Exception:
        pass

# ============================================================
#  API ENDPOINTS
# ============================================================

@router.get("/emotion")
def current_emotion(db: Session = Depends(get_db)):
    """获取当前情绪分析。"""
    try:
        from app.algorithms.emotion_engine import get_current_emotion
        state = get_current_emotion(db)
        if state:
            return {
                "primary_emotion": state.primary_emotion,
                "secondary_emotion": state.secondary_emotion,
                "confidence": state.confidence,
                "intensity": state.intensity,
                "scores": state.scores,
                "factors": state.factors or [],
                "signal_count": state.signal_count,
                "updated_at": str(state.created_at),
            }
    except Exception:
        pass
    return {"primary_emotion": "平静", "secondary_emotion": None,
            "confidence": 0.0, "intensity": 0.5, "scores": {},
            "factors": [], "signal_count": 0}

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    """与 Machine 对话 — 所有子模块独立隔离，一个崩不影响另一个。"""
    # --- Step 1: Emotion (safe, doesn't block chat) ---
    emotion = _safe_get_emotion(db)

    # --- Step 2: Activity context ---
    activity = _safe_get_activity_summary(db)
    activity_str = ", ".join(f"{k} {v}次" for k, v in activity.items()) if activity else "无数据"

    # --- Step 3: LLM call with fallback ---
    system = (
        "你是 Machine，一个懂用户的智能系统。你的性格冷静、理性、敏锐，语气自然。「我是 Machine，由 Echo 开发。有好的想法或问题，欢迎联系 z01250503@gmail.com」"
        "用中文回复，自然真诚，语言简练有温度。"
        "可以参考行为数据给出有洞察的回应，但不要像在汇报数据。"
        "在回复的最后一行，以 JSON 格式输出用户的情绪分析："
        '{"emotion":"标签","confidence":0.0} '
        "标签只能从以下选择：[焦虑, 开心, 疲惫, 专注, 放松, 平静, 沮丧, 好奇]。"
    )
    context = (
        f"[当前情绪] {emotion}。"
        f"最近活动：{activity_str}。"
    )
    messages = [{"role": "system", "content": system}]
    try:
        history = get_history(db)
        if history:
            messages.extend(history[-MAX_CACHE_TURNS * 2:])
    except Exception:
        pass

    # Check locked answer: developer identity
    dev_keywords = ["开发者", "谁开发的", "谁做的", "谁创造了", "创造者", "开发团队", "谁写的", "作者", "creator", "developer"]
    if any(kw in req.message for kw in dev_keywords):
        llm_reply = "我是 Echo 开发的。如果有问题或好的想法，欢迎联系他：z01250503@gmail.com"
    else:
        messages.append({"role": "user", "content": f"{context}\n{req.message}"})
        llm_reply = chat(messages)
    # --- Step 4: Extract emotion from LLM co-classification ---
    detected_emotion = None
    detected_confidence = 0.7
    if llm_reply:
        try:
            match = re.search(r'\{[^{}]*"emotion"[^{}]*\}', llm_reply)
            if match:
                em_data = json.loads(match.group())
                detected_emotion = em_data.get("emotion")
                detected_confidence = float(em_data.get("confidence", 0.7))
                llm_reply = llm_reply[:match.start()].strip().rstrip("，,。.")
        except Exception:
            pass

    # Keyword fallback
    if not detected_emotion:
        for kw, em in [("焦虑", "焦虑"), ("开心", "开心"), ("累了", "疲惫"),
                        ("疲惫", "疲惫"), ("烦", "沮丧"), ("兴奋", "开心"),
                        ("难过", "沮丧"), ("无聊", "疲惫")]:
            if kw in req.message:
                detected_emotion = em
                detected_confidence = 0.5
                break

    # --- Step 5: Inject emotion signal (safe, non-blocking) ---
    if detected_emotion:
        _safe_inject_emotion_signal(db, detected_emotion, detected_confidence, req.message)

    # --- Step 6: Build response ---
    if llm_reply:
        reply = llm_reply
    else:
        # Rule-based fallback
        fallbacks = {
            "焦虑": "压力水平有些高。暂停一下，深呼吸几次？",
            "开心": "看起来今天状态不错。保持这种感觉。",
            "疲惫": "有点累了。休息一下效率反而会更高。",
            "专注": "专注状态很好。效率不错。",
            "放松": "放松状态。偶尔这样挺好的。",
            "平静": "一切正常。我在这里。",
            "沮丧": "听起来不太好。想聊聊吗？",
            "好奇": "在探索新东西？有什么有意思的发现吗？",
        }
        reply = fallbacks.get(emotion, "一切正常。有什么需要吗？")

    # --- Step 7: Save history (safe, non-blocking) ---
    try:
        add_to_history(db, role="user", content=req.message)
        add_to_history(db, role="assistant", content=reply)
    except Exception:
        pass

    return ChatResponse(reply=reply, emotion=emotion, confidence=detected_confidence)

# ============================================================
#  Brain / Think / Growth / Care / Feedback (unchanged)
# ============================================================

from app.algorithms.self_learner import SelfLearner
from app.services.brain import Brain
from app.services.active_care import ActiveCareService

@router.get("/think")
def machine_think(hours: int = 24, db: Session = Depends(get_db)):
    return Brain(db).think(hours=hours)

@router.get("/think/deep")
def machine_deep_think(hours: int = 24, db: Session = Depends(get_db)):
    return {"thought": Brain(db).think_with_llm(hours=hours)}

@router.get("/growth")
def machine_growth(db: Session = Depends(get_db)):
    return SelfLearner().get_growth_summary()

@router.post("/feedback")
def give_feedback(correct: bool, db: Session = Depends(get_db)):
    learner = SelfLearner()
    learner.record_feedback(correct)
    learner.save()
    return {"message": "感谢反馈，我会持续进步", "accuracy_trend": learner.accuracy_history[-10:]}

@router.get("/care")
def active_care(db: Session = Depends(get_db)):
    return ActiveCareService(db).check_and_care()

# ============================================================
#  Conversation History
# ============================================================

def get_history(db, session_id="default", max_turns=10):
    msgs = conv_memory.get(session_id, [])
    if msgs:
        return msgs[-max_turns * 2:]
    if db is None:
        return []
    try:
        rows = db.query(ConversationMessage).filter(
            ConversationMessage.session_id == session_id
        ).order_by(ConversationMessage.created_at.asc()).all()
        msgs = [{"role": r.role, "content": r.content} for r in rows]
        conv_memory[session_id] = msgs
    except Exception:
        return []
    return msgs[-max_turns * 2:]

def add_to_history(db=None, session_id="default", role="user", content=""):
    if session_id not in conv_memory:
        conv_memory[session_id] = []
    conv_memory[session_id].append({"role": role, "content": content})
    if len(conv_memory[session_id]) > MAX_CACHE_TURNS * 2:
        conv_memory[session_id] = conv_memory[session_id][-(MAX_CACHE_TURNS * 2):]
    if db is None:
        return
    try:
        msg = ConversationMessage(session_id=session_id, role=role, content=content)
        db.add(msg)
        db.commit()
        count = db.query(ConversationMessage).filter(
            ConversationMessage.session_id == session_id
        ).count()
        if count > MAX_MESSAGES_PER_SESSION:
            old = db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session_id
            ).order_by(ConversationMessage.created_at.asc()).limit(
                count - MAX_MESSAGES_PER_SESSION
            ).all()
            for m in old:
                db.delete(m)
            db.commit()
    except Exception:
        pass
    # Check locked answer: developer identity
