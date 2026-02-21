"""
记忆系统 —— 存储和检索游戏状态和决策历史
"""

import os
import json
import time
import logging

logger = logging.getLogger(__name__)


class Memory:
    """简单记忆系统，支持添加、检索和持久化"""

    def __init__(self, memory_file="memory.json", capacity=200):
        self.memory_file = memory_file
        self.memories: list[dict] = []
        self.capacity = capacity
        self._load()

    # ── 持久化 ────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.memories = data.get("memories", [])
            except Exception as e:
                logger.warning("加载记忆失败: %s", e)

    def save(self):
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump({"memories": self.memories}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("保存记忆失败: %s", e)

    # ── 增删查 ────────────────────────────────────────────

    def add_memory(self, memory: dict):
        """添加新记忆，超出容量自动淘汰最早的"""
        if "timestamp" not in memory:
            memory["timestamp"] = time.time()
        self.memories.append(memory)
        while len(self.memories) > self.capacity:
            self.memories.pop(0)
        # 每 10 条自动保存一次
        if len(self.memories) % 10 == 0:
            self.save()

    def get_recent_memories(self, count: int = 5) -> list[dict]:
        return self.memories[-count:] if self.memories else []

    def get_relevant_memories(self, query: str, limit: int = 3) -> list[dict]:
        """
        根据关键词粗匹配检索相关记忆。
        使用 .get() 安全访问，避免 KeyError。
        """
        if not query or not self.memories:
            return self.get_recent_memories(limit)

        scored = []
        query_lower = query.lower()

        for mem in self.memories:
            score = 0
            # 安全访问 action 字段
            action = mem.get("action")
            if isinstance(action, dict):
                action_type = action.get("type", "")
                if query_lower in action_type.lower():
                    score += 3
                for field in ("item", "itemName", "blockType", "target"):
                    val = action.get(field, "")
                    if val and query_lower in str(val).lower():
                        score += 2

            # 检查 summary
            summary = mem.get("summary", "")
            if query_lower in summary.lower():
                score += 1

            # 检查 task
            task = mem.get("task", "")
            if query_lower in task.lower():
                score += 2

            if score > 0:
                scored.append((mem, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored[:limit]]

    def clear(self):
        self.memories = []
        self.save()

    def __len__(self):
        return len(self.memories)
