"""强化学习式重要性评分。

不是硬编码 importance=0.5，而是：
- 被反复查询的事件 → 更重要
- 关联到重要事件的事件 → 更重要
- 时间越近的事件 → 略重要
"""
import math
from collections import defaultdict
from datetime import datetime, timezone, timedelta


class ImportanceLearner:
    """基于交互的重要性学习器"""

    def __init__(self, decay_rate: float = 0.1):
        self.decay_rate = decay_rate
        self.scores: dict[int, float] = {}
        self.query_counts: dict[int, int] = defaultdict(int)
        self.link_graph: dict[int, set[int]] = defaultdict(set)

    def record_query(self, entity_id: int):
        """记录一次查询（该实体被用户关注）"""
        self.query_counts[entity_id] += 1

    def add_link(self, source_id: int, target_id: int):
        """记录实体之间的关联"""
        self.link_graph[source_id].add(target_id)

    def compute_importance(self, entity_id: int, created_at: datetime | None = None) -> float:
        """计算综合重要性得分"""
        # 查询频率得分 (0-0.4)
        query_score = math.log(self.query_counts.get(entity_id, 0) + 1) * 0.1
        query_score = min(query_score, 0.4)

        # 关联得分 (0-0.3)
        link_count = 0
        for source, targets in self.link_graph.items():
            if entity_id in targets:
                link_count += 1
        link_score = math.log(link_count + 1) * 0.1
        link_score = min(link_score, 0.3)

        # 时间衰减 (0-0.3)
        time_score = 0.3
        if created_at:
            days_ago = (datetime.now(timezone.utc) - created_at).days
            time_score = 0.3 * math.exp(-self.decay_rate * days_ago)

        return round(query_score + link_score + time_score, 3)

    def get_top_important(self, top_k: int = 10) -> list[int]:
        """返回最重要的实体 ID"""
        scored = [(eid, self.compute_importance(eid)) for eid in self.scores]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [eid for eid, _ in scored[:top_k]]
