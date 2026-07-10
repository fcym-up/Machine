"""用户画像引擎 - 从事件中学习你的习惯和模式。"""
from collections import Counter
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.event import Event


class UserProfile:
    def __init__(self, db: Session):
        self.db = db

    def get_habits(self, days=7):
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        if not events:
            return {"message": "数据不足，请先让Machine运行几天", "total_events": 0}
        hours = [e.created_at.hour for e in events]
        peak = Counter(hours).most_common(1)[0][0] if hours else 0
        apps = Counter()
        for e in events:
            if e.source == "activity" and isinstance(e.payload, dict):
                apps[e.payload.get("category", "other")] += 1
        total = len(events)
        return {
            "peak_hour": f"{peak}:00",
            "morning_person": 6 <= peak <= 10,
            "night_owl": peak >= 22,
            "total_events": total,
            "activity_breakdown": dict(apps.most_common()),
            "summary": f"主要活动: {apps.most_common(1)[0][0] if apps else '未知'}"
        }

    def daily_digest(self):
        today = datetime.now(timezone.utc).date()
        events = self.db.query(Event).filter(
            Event.created_at >= datetime(today.year, today.month, today.day)
        ).all()
        if not events:
            return {"message": "今天还没有记录任何活动"}
        topics = Counter(
            e.payload.get("category", "other") for e in events
            if isinstance(e.payload, dict)
        )
        return {
            "date": str(today),
            "total_events": len(events),
            "focus_areas": dict(topics.most_common()),
            "summary": f"今天共记录{len(events)}个事件"
        }

    def get_insights(self, days=7):
        habits = self.get_habits(days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        insights = []
        if habits.get("night_owl"):
            insights.append("你经常深夜工作，注意休息。")
        git_commits = sum(1 for e in recent if e.event_type == "git-commit")
        if git_commits > 10:
            insights.append(f"过去{days}天提交了{git_commits}次代码，生产力很高！")
        return {"habits": habits, "insights": insights}

    def full_dimension_analysis(self, days=7):
        """全维度活动分析"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        if not events:
            return {"message": "数据不足"}
        # 按分类统计
        cats = Counter()
        time_spent = {}
        for e in events:
            cat = e.payload.get("category","其他") if isinstance(e.payload,dict) else "其他"
            cats[cat] += 1
        total = len(events)
        # 检测使用模式
        patterns = []
        if cats.get("游戏娱乐",0) > 0:
            patterns.append(f"过去{days}天有{cats['游戏娱乐']}次游戏活动")
        if cats.get("招聘求职",0) > 0:
            patterns.append(f"检测到{cats['招聘求职']}次招聘网站访问，是否在找工作？")
        if cats.get("社交聊天",0) > 0:
            patterns.append(f"社交聊天活跃：{cats['社交聊天']}次")
        if cats.get("视频娱乐",0) > 0:
            patterns.append(f"视频娱乐：{cats['视频娱乐']}次")
        if cats.get("开发工具",0) > cats.get("游戏娱乐",0) + cats.get("视频娱乐",0):
            patterns.append("工作/学习是主要活动，保持专注！")
        return {
            "total": total,
            "categories": dict(cats.most_common()),
            "patterns": patterns,
            "summary": f"过去{days}天主要活动：{cats.most_common(1)[0][0] if cats else '未知'}（{round(cats.most_common(1)[0][1]/max(total,1)*100,1)}%）"
        }
