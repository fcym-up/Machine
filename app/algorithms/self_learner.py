"""自我进化引擎 - 在线学习 + 模型持久化。

Machine 每收到一条新数据就更新自己的模型，
而不是每次启动从零开始。
"""
import pickle, os, json
from datetime import datetime, timezone
from collections import defaultdict, Counter
import numpy as np


class SelfLearner:
    """持续在线学习 + 自我进化"""

    def __init__(self, state_dir: str = "D:/workplace/data/brain"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
        self.knowledge: dict = {}
        self.accuracy_history: list[float] = []
        self.last_updated = datetime.now(timezone.utc)
        self.load()

    def learn(self, event_type: str, payload: dict, category: str = ""):
        """从单个事件中学习"""
        key = f"{event_type}:{category}" if category else event_type
        if key not in self.knowledge:
            self.knowledge[key] = {"count": 0, "first_seen": str(datetime.now(timezone.utc)), "examples": []}
        self.knowledge[key]["count"] += 1
        self.knowledge[key]["last_seen"] = str(datetime.now(timezone.utc))
        if len(self.knowledge[key]["examples"]) < 10:
            self.knowledge[key]["examples"].append(str(payload)[:200])
        self.last_updated = datetime.now(timezone.utc)
        # 每 100 次学习自动保存
        total = sum(k["count"] for k in self.knowledge.values())
        if total % 100 == 0:
            self.save()

    def get_surprise_factor(self, event_type: str, category: str = "") -> float:
        """计算新颖度 - 越罕见的事件越令人惊讶"""
        key = f"{event_type}:{category}" if category else event_type
        total = sum(k["count"] for k in self.knowledge.values())
        if total == 0:
            return 1.0
        count = self.knowledge.get(key, {}).get("count", 0)
        expected = total / max(len(self.knowledge), 1)
        return 1.0 / (1.0 + count / max(expected, 1))

    def get_growth_summary(self) -> dict:
        """获取进化摘要"""
        total_events = sum(k["count"] for k in self.knowledge.values())
        categories_known = len(self.knowledge)
        new_last_hour = 0
        return {
            "total_learned": total_events,
            "concepts_known": categories_known,
            "new_discoveries": new_last_hour,
            "accuracy_trend": self.accuracy_history[-10:] if self.accuracy_history else [],
            "evolution_state": "初生" if total_events < 100 else "成长" if total_events < 1000 else "成熟" if total_events < 10000 else "智慧",
        }

    def record_feedback(self, correct: bool):
        """记录反馈以追踪准确率"""
        self.accuracy_history.append(1.0 if correct else 0.0)

    def save(self):
        """持久化到磁盘"""
        with open(f"{self.state_dir}/knowledge.json", "w", encoding="utf-8") as f:
            json.dump(self.knowledge, f, ensure_ascii=False, default=str)
        with open(f"{self.state_dir}/accuracy.pkl", "wb") as f:
            pickle.dump(self.accuracy_history, f)

    def load(self):
        """Load from disk with graceful error handling."""
        try:
            kf = f"{self.state_dir}/knowledge.json"
            if os.path.exists(kf):
                with open(kf, "r", encoding="utf-8") as f:
                    self.knowledge = json.load(f)
            af = f"{self.state_dir}/accuracy.pkl"
            if os.path.exists(af):
                with open(af, "rb") as f:
                    self.accuracy_history = pickle.load(f)
        except Exception as e:
            from loguru import logger
            logger.warning(f"Failed to load brain state: {e}, starting fresh")
            self.accuracy_history = []
