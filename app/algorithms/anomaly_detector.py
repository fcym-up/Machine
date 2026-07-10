"""统计异常检测算法 - 替代阈值比较。

使用 Z-score 和 IQR 方法检测行为异常。
"""
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta


class AnomalyDetector:
    """基于统计的异常检测器"""

    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity
        self.baselines: dict[str, tuple[float, float]] = {}
        self.history: dict[str, list[float]] = defaultdict(list)

    def fit(self, hourly_counts: dict[int, int]):
        """从历史数据学习基线"""
        values = list(hourly_counts.values())
        if len(values) < 2:
            return
        self.history["hourly"].extend(values)
        arr = np.array(values)
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        self.baselines["hourly"] = (mean, std)

    def detect(self, current_value: float, key: str = "hourly") -> tuple[bool, float, str]:
        """检测当前值是否异常
        
        Returns:
            (is_anomaly, z_score, reason)
        """
        baseline = self.baselines.get(key)
        if not baseline:
            return (False, 0.0, "基线数据不足")
        mean, std = baseline
        if std == 0:
            return (False, 0.0, "数据无变化")
        z = (current_value - mean) / std
        if abs(z) > self.sensitivity:
            direction = "高于" if z > 0 else "低于"
            return (True, round(z, 2), f"Z-score={z:.1f}，显著{direction}平均值（{mean:.1f}±{std:.1f}）")
        return (False, round(z, 2), "")

    def detect_iqr(self, values: list[float]) -> list[int]:
        """IQR 异常检测 - 返回异常值的索引"""
        if len(values) < 4:
            return []
        arr = np.array(values)
        q1, q3 = np.percentile(arr, [25, 75])
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = [i for i, v in enumerate(arr) if v < lower or v > upper]
        return outliers
