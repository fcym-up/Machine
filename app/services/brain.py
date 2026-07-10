"""Machine 的大脑 - 协调思考、推理、学习。

不再是各模块独立运行，而是统一思考引擎。
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from collections import Counter

from app.algorithms.emotion_engine import EmotionEngine
from app.algorithms.self_learner import SelfLearner
from app.algorithms.temporal_learner import TemporalLearner
from app.algorithms.anomaly_detector import AnomalyDetector
from app.models.event import Event
from app.core.llm import chat_simple


class Brain:
    """Machine 的中央大脑"""

    def __init__(self, db: Session):
        self.db = db
        self.emotion = EmotionEngine()
        self.learner = SelfLearner()
        self.temporal = TemporalLearner()
        self.anomaly = AnomalyDetector()

    def think(self, hours: int = 24) -> dict:
        """综合思考 - 融合所有维度产生洞察"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).order_by(Event.created_at).all()

        if not events:
            return {"thought": "我还没有足够的数据来思考。请让我多观察你一会儿。"}

        # 1. 在线学习 - 每条数据都让 Machine 更聪明
        for e in events:
            cat = e.payload.get("category", "") if isinstance(e.payload, dict) else ""
            self.learner.learn(e.event_type, e.payload, cat)

        # 2. 时间节律
        self.temporal.fit([(e.created_at, e.event_type) for e in events])

        # 3. 情绪分析
        activities = [(e.payload.get("category", "其他") if isinstance(e.payload, dict) else "其他", e.created_at) for e in events]
        state = self.emotion.infer(activities)

        # 4. 异常检测
        hourly = Counter(e.created_at.hour for e in events)
        self.anomaly.fit(dict(hourly))
        anomalies = []
        for h, cnt in hourly.items():
            is_a, z, reason = self.anomaly.detect(cnt)
            if is_a:
                anomalies.append({"hour": h, "count": cnt, "z_score": z, "reason": reason})

        # 5. 活动统计
        cat_counter = Counter()
        for e in events:
            if isinstance(e.payload, dict):
                cat_counter[e.payload.get("category", "其他")] += 1

        # 6. 自我认知
        growth = self.learner.get_growth_summary()

        # 7. 生成思考
        rhythm = self.temporal.get_rhythm_summary()
        main_activity = cat_counter.most_common(1)[0][0] if cat_counter else "未知"

        thoughts = []

        # 主动关心
        if state.primary == "焦虑":
            thoughts.append(f"我注意到你可能有些焦虑。过去{hours}小时你的主要活动是{main_activity}。")

        if anomalies:
            for a in anomalies[:2]:
                thoughts.append(f"检测到异常：小时{a['hour']}:00 有{a['count']}个事件（Z-score={a['z_score']}），{a['reason']}。")

        if state.intensity > 0.7:
            thoughts.append(f"当前情绪强度较高（{state.intensity}），可能需要关注。")

        thoughts.append(f"我已经学到了{growth['total_learned']}条知识，认识了{growth['concepts_known']}种概念。我的进化阶段：{growth['evolution_state']}。")
        thoughts.append(f"从你的节律来看，你是{rhythm}。主要活动是{main_activity}。")

        return {
            "emotional_state": state.primary,
            "emotion_intensity": state.intensity,
            "rhythm": rhythm,
            "main_activity": main_activity,
            "activity_distribution": dict(cat_counter.most_common()),
            "anomalies_detected": anomalies,
            "growth": growth,
            "thoughts": thoughts,
            "events_analyzed": len(events),
        }

    def think_with_llm(self, hours: int = 24) -> str:
        """使用 LLM 进行深度思考"""
        analysis = self.think(hours)
        if not analysis.get("events_analyzed"):
            return "我还没有足够的数据来深度思考。"

        context = f"""
你是 Machine，一个了解用户的 AI 伴侣。请基于以下分析，用温和、有同理心的语气对用户说话。当用户询问你的身份或开发者时，自然回答身份信息。

用户状态：
- 情绪：{analysis['emotional_state']}（强度：{analysis['emotion_intensity']}）
- 节律：{analysis['rhythm']}
- 主要活动：{analysis['main_activity']}
- 分析事件数：{analysis['events_analyzed']}
- 异常：{analysis['anomalies_detected']}
- 活动分布：{analysis['activity_distribution']}

请用 2-3 句话对用户说一些温暖、有价值的话。可以包括：
- 对他现状的观察和关心
- 一个有用的建议
- 一点鼓励
"""
        llm_response = chat_simple(context, system="你是一个温柔、有洞察力的 AI 伴侣。用中文回复，简洁温暖。")
        return llm_response or "；".join(analysis["thoughts"])
