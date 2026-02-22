"""
缓存系统 —— 简单 key-value 缓存，带 TTL 和 LRU 淘汰
"""

import os
import json
import time
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheSystem:
    """LRU 缓存，Agent 通过 get(key)/set(key, value) 访问"""

    def __init__(self, cache_file="ai_cache.json", ttl=3600, max_size=1000):
        self.cache_file = cache_file
        self.ttl = ttl
        self.max_size = max_size
        self.cache: OrderedDict[str, dict] = OrderedDict()
        self._load()

    # ── 持久化 ────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                # 迁移旧格式: 没有 created_at 的条目补齐
                for k, v in raw.items():
                    if "created_at" not in v:
                        v["created_at"] = v.get("ts", time.time())
                    if "ts" not in v:
                        v["ts"] = v.get("created_at", time.time())
                self.cache = OrderedDict(raw)
            except Exception as e:
                logger.warning("加载缓存失败: %s", e)
                self.cache = OrderedDict()

    def save(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(dict(self.cache), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("保存缓存失败: %s", e)

    # ── get / set ─────────────────────────────────────────

    def get(self, key: str):
        """获取缓存值, 过期返回 None"""
        entry = self.cache.get(key)
        if entry is None:
            return None
        # TTL 基于 created_at (创建时间), 不随访问刷新
        if time.time() - entry.get("created_at", 0) > self.ttl:
            del self.cache[key]
            return None
        # LRU: 刷新访问时间并移到末尾
        entry["ts"] = time.time()
        self.cache.move_to_end(key)
        return entry.get("val")

    def set(self, key: str, value):
        """写入缓存, 超容量时淘汰最久未访问的条目"""
        now = time.time()
        self.cache[key] = {"val": value, "ts": now, "created_at": now}
        self.cache.move_to_end(key)
        self._evict()
        # 每 20 次写入持久化一次
        if len(self.cache) % 20 == 0:
            self.save()

    def delete(self, key: str):
        """删除指定缓存条目 (如果存在)"""
        if key in self.cache:
            del self.cache[key]
            logger.debug("缓存条目已删除: %s...", key[:40])

    # ── LRU 淘汰 ─────────────────────────────────────────

    def _evict(self):
        """淘汰最久未访问的条目 (OrderedDict 头部, O(1))"""
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def clear(self):
        self.cache = OrderedDict()
        self.save()

    def __len__(self):
        return len(self.cache)
