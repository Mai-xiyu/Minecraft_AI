"""
学习系统 —— 记录动作结果，提取策略
"""

import os
import json
import time
import hashlib
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class LearningSystem:
    """从经验中学习: 记录动作成功率、提取成功策略"""

    def __init__(self, learning_file="learning.json", capacity=500):
        self.learning_file = learning_file
        self.capacity = capacity
        self.action_outcomes: dict[str, list] = defaultdict(list)
        self.successful_strategies: list[dict] = []
        self.failed_strategies: list[dict] = []
        self._load()

    # ── 持久化 ────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.action_outcomes = defaultdict(list, data.get("action_outcomes", {}))
                    self.successful_strategies = data.get("successful_strategies", [])
                    self.failed_strategies = data.get("failed_strategies", [])
            except Exception as e:
                logger.warning("加载学习数据失败: %s", e)

    def save(self):
        try:
            # 淘汰旧记录
            for key in list(self.action_outcomes):
                if len(self.action_outcomes[key]) > 50:
                    self.action_outcomes[key] = self.action_outcomes[key][-50:]
            self.successful_strategies = self.successful_strategies[-100:]
            self.failed_strategies = self.failed_strategies[-50:]

            with open(self.learning_file, "w", encoding="utf-8") as f:
                json.dump({
                    "action_outcomes": dict(self.action_outcomes),
                    "successful_strategies": self.successful_strategies,
                    "failed_strategies": self.failed_strategies,
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("保存学习数据失败: %s", e)

    # ── Agent 调用接口 ────────────────────────────────────

    def record(self, state: dict, action: dict, result: dict):
        """
        Agent 统一调用的记录接口。
        state: 机器人状态
        action: 执行的动作
        result: {"success": bool, ...}
        """
        action_type = action.get("type", "unknown")
        success = result.get("success", False)

        # 简化上下文 key (用 hashlib 而非 hash)
        ctx_str = json.dumps({
            "blocks": sorted(set(b.get("name", "") for b in state.get("nearbyBlocks", [])[:5])),
            "health": int(state.get("health", 0)),
        }, sort_keys=True)
        ctx_hash = hashlib.md5(ctx_str.encode()).hexdigest()[:8]
        key = f"{action_type}_{ctx_hash}"

        self.action_outcomes[key].append({
            "success": success,
            "timestamp": time.time(),
        })

        # 记录策略
        entry = {
            "action": action,
            "result_success": success,
            "timestamp": time.time(),
        }
        if success:
            self.successful_strategies.append(entry)
        else:
            self.failed_strategies.append(entry)

        # 容量控制 & 自动保存
        total = sum(len(v) for v in self.action_outcomes.values())
        if total > self.capacity:
            self.save()

    # ── 查询 ──────────────────────────────────────────────

    def get_action_success_rate(self, action_type: str) -> float:
        """获取某类动作的平均成功率"""
        all_outcomes = []
        for key, outcomes in self.action_outcomes.items():
            if key.startswith(f"{action_type}_"):
                all_outcomes.extend(outcomes)
        if not all_outcomes:
            return 0.5
        success_count = sum(1 for o in all_outcomes if o.get("success"))
        return success_count / len(all_outcomes)

    def get_recent_successes(self, limit: int = 5) -> list[dict]:
        return self.successful_strategies[-limit:]
