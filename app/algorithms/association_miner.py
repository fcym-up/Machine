"""关联规则挖掘 - 发现行为模式。

"Apriori 风格"的频繁模式挖掘：
"你改了 A 文件后，75% 的情况会改 B 文件"
"""
from collections import defaultdict
from itertools import combinations


class AssociationMiner:
    """行为关联规则挖掘器"""

    def __init__(self, min_support: float = 0.1, min_confidence: float = 0.5):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.rules: list[dict] = []

    def fit(self, transactions: list[list[str]]):
        """从事务列表中挖掘关联规则
        
        Args:
            transactions: 每行是一组同时出现的事件类型
                例如：[["coding","file-change"],["coding","git-commit"],...]
        """
        n = len(transactions)
        # 计算频繁 1-项集
        item_counts = defaultdict(int)
        for t in transactions:
            for item in set(t):
                item_counts[item] += 1
        frequent = {item for item, cnt in item_counts.items() if cnt / n >= self.min_support}

        # 计算频繁 2-项集并生成规则
        pair_counts = defaultdict(int)
        for t in transactions:
            items = [i for i in t if i in frequent]
            for a, b in combinations(items, 2):
                pair_counts[(a, b)] += 1
                pair_counts[(b, a)] += 1

        for (antecedent, consequent), pair_cnt in pair_counts.items():
            support = pair_cnt / n
            confidence = pair_cnt / item_counts[antecedent] if item_counts[antecedent] > 0 else 0
            if support >= self.min_support and confidence >= self.min_confidence:
                self.rules.append({
                    "antecedent": antecedent,
                    "consequent": consequent,
                    "confidence": round(confidence, 3),
                    "support": round(support, 3),
                })

        self.rules.sort(key=lambda r: r["confidence"], reverse=True)

    def get_rules(self, antecedent: str | None = None) -> list[dict]:
        """获取关联规则"""
        if antecedent:
            return [r for r in self.rules if r["antecedent"] == antecedent]
        return self.rules[:20]

    def predict_next(self, current_activity: str, top_k: int = 3) -> list[str]:
        """预测下一步行为"""
        rules = self.get_rules(current_activity)
        return [r["consequent"] for r in rules[:top_k]]
