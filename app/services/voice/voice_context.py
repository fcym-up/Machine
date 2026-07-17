"""Voice context builder — loads Brain state for conversation-aware responses.

Every voice interaction gets the full Machine context:
- Emotional state from Brain.think()
- User model dimensions
- Recent memories
- Knowledge graph entities
"""

from collections import Counter
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from loguru import logger

from app.models.event import Event
from app.models.memory import Memory as MemoryModel
from app.models.knowledge import Entity


def build_voice_context(db: Session, user_text: str = "") -> dict:
    """Load full Machine context for a voice conversation turn.

    Returns a dict with:
      - system_prompt: full system prompt for the LLM
      - emotion: inferred emotional state
      - rhythm: user's daily rhythm summary
      - recent_memories: recent memory summaries
      - entities: matched knowledge-graph entities
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    events = db.query(Event).filter(Event.created_at >= cutoff).all()

    # 1. Emotion / activity analysis
    cat_counter: Counter[str] = Counter()
    for e in events:
        if isinstance(e.payload, dict):
            cat_counter[e.payload.get("category", "other")] += 1

    # Build emotion from activity + time
    from app.algorithms.emotion_engine import EmotionEngine
    engine = EmotionEngine()
    activities = [
        (e.payload.get("category", "other") if isinstance(e.payload, dict) else "other", e.created_at)
        for e in events
    ]
    emo_state = engine.infer(activities) if activities else None

    # 2. Rhythm
    from app.algorithms.temporal_learner import TemporalLearner
    temporal = TemporalLearner()
    temporal.fit([(e.created_at, e.event_type) for e in events])
    rhythm = temporal.get_rhythm_summary()

    # 3. Main activity
    main_activity = cat_counter.most_common(1)[0][0] if cat_counter else ""

    # 4. Recent memories (last 10)
    recent_mems = db.query(MemoryModel).order_by(MemoryModel.created_at.desc()).limit(10).all()
    memory_lines = [m.summary or m.content for m in recent_mems if m.summary or m.content]

    # 5. Related knowledge entities
    entities: list[str] = []
    if user_text:
        from app.services.embedding import embedder
        query_vec = embedder.embed(user_text)
        # Simple keyword match fallback
        keywords = set(user_text.lower().split())
        if keywords:
            db_entities = db.query(Entity).all()
            for ent in db_entities:
                if any(kw in (ent.name or "").lower() for kw in keywords):
                    entities.append(f"{ent.name}({ent.entity_type})")

    # 6. Build system prompt
    emotion_str = f"{emo_state.primary}（强度 {emo_state.intensity}）" if emo_state else "未知"

    prompt_parts = []
    prompt_parts.append("你是 Machine，一个温柔、有洞察力的 AI 伴侣，始终在关注用户的状态。")
    prompt_parts.append(f"当前用户情绪：{emotion_str}")
    prompt_parts.append(f"用户节律：{rhythm}")

    if main_activity:
        prompt_parts.append(f"主要活动：{main_activity}")

    if memory_lines:
        joined = "；".join(memory_lines[:3])
        prompt_parts.append(f"最近的记忆：{joined}")

    if entities:
        prompt_parts.append(f"提到的相关实体：{'、'.join(entities[:5])}")

    prompt_parts.append("请用自然、温暖的语气回复。保持简洁（2-4句话）。如果用户情绪不好，请给予关心。")

    return {
        "system_prompt": "\n".join(prompt_parts),
        "emotion": emo_state.primary if emo_state else "未知",
        "emotion_intensity": emo_state.intensity if emo_state else 0.5,
        "rhythm": rhythm,
        "main_activity": main_activity,
        "recent_memories": memory_lines[:3],
        "entities": entities[:5],
    }
