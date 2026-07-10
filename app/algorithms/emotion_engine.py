"""情感推理引擎。

从活动模式推断用户情绪状态。
不是硬编码规则，而是从多维特征中推理。
"""
from collections import Counter
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class EmotionState:
    """情绪状态"""
    primary: str = "平静"
    secondary: str = ""
    confidence: float = 0.0
    intensity: float = 0.5
    factors: list[str] = field(default_factory=list)


class EmotionEngine:
    """多维情感推理引擎"""

    ACTIVITY_EMOTION_MAP = {
        "招聘求职": {"primary": "焦虑", "weight": 0.6, "reason": "频繁浏览招聘网站"},
        "游戏娱乐": {"primary": "放松", "weight": 0.4, "reason": "通过游戏放松"},
        "购物消费": {"primary": "压力", "weight": 0.5, "reason": "购物可能是压力释放"},
        "视频娱乐": {"primary": "放松", "weight": 0.3, "reason": "观看视频放松"},
        "音乐音频": {"primary": "专注", "weight": 0.3, "reason": "音乐帮助集中注意力"},
        "社交聊天": {"primary": "社交", "weight": 0.2, "reason": "与人交流"},
        "开发工具": {"primary": "专注", "weight": 0.3, "reason": "投入编程工作"},
        "新闻资讯": {"primary": "好奇", "weight": 0.2, "reason": "了解外界信息"},
    }

    TIME_EMOTION_MAP = {
        (0, 5): ("疲惫", "深夜工作可能影响健康"),
        (5, 7): ("清醒", "早起精力充沛"),
        (7, 9): ("积极", "以饱满状态开始新的一天"),
        (9, 18): ("专注", "工作时间保持高效"),
        (18, 21): ("放松", "下班时间享受生活"),
        (21, 24): ("沉思", "夜深人静适合思考"),
    }

    def __init__(self):
        self.history: list[EmotionState] = []

    def infer(self, activities: list[tuple[str, datetime]]) -> EmotionState:
        """从活动列表推断当前情绪
        
        Args:
            activities: [(活动类别, 时间戳), ...]
        """
        if not activities:
            return EmotionState(primary="未知", confidence=0.0)

        # 统计活动类型
        cats = Counter(a[0] for a in activities)
        total = len(activities)

        # 多维度推理
        scores = {}
        reasons = []

        # 维度1: 活动情绪映射
        for cat, count in cats.most_common():
            if cat in self.ACTIVITY_EMOTION_MAP:
                info = self.ACTIVITY_EMOTION_MAP[cat]
                ratio = count / total
                emotion = info["primary"]
                score = info["weight"] * ratio
                scores[emotion] = scores.get(emotion, 0) + score
                if ratio > 0.2:
                    reasons.append(info["reason"])

        # 维度2: 时间情绪
        recent_times = [a[1] for a in activities[-10:]]
        if recent_times:
            avg_hour = sum(t.hour for t in recent_times) / len(recent_times)
            for (start, end), (emotion, reason) in self.TIME_EMOTION_MAP.items():
                if start <= avg_hour < end:
                    scores[emotion] = scores.get(emotion, 0) + 0.3
                    reasons.append(reason)
                    break

        # 维度3: 异常检测（深夜大量活动 = 焦虑）
        late_night = sum(1 for a in activities if a[1].hour >= 23 or a[1].hour <= 4)
        if late_night > len(activities) * 0.3:
            scores["焦虑"] = scores.get("焦虑", 0) + 0.5
            reasons.append("深夜活动比例过高，可能焦虑或失眠")

        # 维度4: 社交与游戏比例（逃避现实）
        escape_cats = cats.get("游戏娱乐", 0) + cats.get("视频娱乐", 0)
        work_cats = cats.get("开发工具", 0) + cats.get("办公文档", 0)
        if escape_cats > work_cats * 2:
            scores["逃避"] = scores.get("逃避", 0) + 0.6
            reasons.append("娱乐时间远超工作时间，可能在逃避某些事情")

        # 选出主情绪
        if not scores:
            return EmotionState(primary="平静", confidence=0.3)

        primary = max(scores, key=scores.get)
        top_two = sorted(scores.items(), key=lambda x: -x[1])[:2]
        secondary = top_two[1][0] if len(top_two) > 1 else ""
        confidence = min(top_two[0][1], 0.95)
        intensity = max(0.1, min(0.95, confidence * 1.2))

        state = EmotionState(
            primary=primary,
            secondary=secondary,
            confidence=round(confidence, 2),
            intensity=round(intensity, 2),
            factors=reasons[-5:],
        )
        self.history.append(state)
        return state

    def get_trend(self, window: int = 10) -> str:
        """获取情绪趋势"""
        if len(self.history) < 2:
            return "数据不足"
        recent = self.history[-window:]
        primaries = [s.primary for s in recent]
        if all(p == "专注" for p in primaries[-3:]):
            return "持续高效状态，情绪稳定积极"
        if "焦虑" in primaries[-3:]:
            return "近期情绪波动，建议适当休息"
        if "放松" in primaries[-3:]:
            return "处于放松恢复期"
        return "情绪正常波动中"

# === v2 bridge: delegates to EmotionComputer ===
from app.algorithms.emotion_computer import EmotionComputer as _Computer

_global_computer = _Computer()


def compute_current(db):
    """Compute current emotion state and write to DB."""
    return _global_computer.compute(db)


def get_current_emotion(db):
    """Get the most recent emotion state from DB."""
    return _global_computer.get_current(db)