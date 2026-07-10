"""时间模式学习 - 学习你的日常节律。

从历史数据中学习：
- 你通常几点开始工作？
- 一周中哪几天效率最高？
- 你的工作/休息周期是多久？
"""
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta


class TemporalLearner:
    """时间节律学习器"""

    def __init__(self):
        self.hourly_profile: dict[int, float] = {}
        self.daily_profile: dict[int, float] = {}
        self.weekly_profile: dict[int, float] = {}

    def fit(self, events: list[tuple[datetime, str]]):
        """从事件列表学习时间模式
        
        Args:
            events: [(时间戳, 事件类型), ...]
        """
        hourly = defaultdict(float)
        daily = defaultdict(float)
        weekly = defaultdict(float)

        for ts, _ in events:
            hourly[ts.hour] += 1
            daily[ts.weekday()] += 1
            weekly[ts.isoweekday()] += 1

        total = len(events)
        if total > 0:
            self.hourly_profile = {h: round(c / total, 3) for h, c in hourly.items()}
            self.daily_profile = {d: round(c / total, 3) for d, c in daily.items()}
            self.weekly_profile = {w: round(c / total, 3) for w, c in weekly.items()}

    def get_peak_hour(self) -> int:
        """返回最活跃的小时"""
        if not self.hourly_profile:
            return -1
        return max(self.hourly_profile, key=self.hourly_profile.get)

    def get_most_active_day(self) -> str:
        """返回最活跃的星期几"""
        if not self.daily_profile:
            return "未知"
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        best = max(self.daily_profile, key=self.daily_profile.get)
        return days[best] if best < 7 else "未知"

    def predict_activity(self, hour: int) -> float:
        """预测某个小时的活跃度"""
        return self.hourly_profile.get(hour, 0.0)

    def get_rhythm_summary(self) -> str:
        """返回节律摘要"""
        peak = self.get_peak_hour()
        day = self.get_most_active_day()
        if peak < 0:
            return "数据不足"
        if 5 <= peak <= 9:
            rhythm = "早起型"
        elif 10 <= peak <= 17:
            rhythm = "白天型"
        elif 18 <= peak <= 23:
            rhythm = "晚间型"
        else:
            rhythm = "深夜型"
        return f"{rhythm}，最活跃在{peak}:00，最忙的一天是{day}"
