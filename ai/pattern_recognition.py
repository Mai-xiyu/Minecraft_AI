"""
模式识别 —— 基于历史状态-动作对预测动作 (不依赖 numpy)
"""

import json
import math
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class PatternRecognition:
    """简单的状态-动作模式匹配，返回 {"action": dict, "confidence": float}"""

    MAX_PAIRS = 500

    def __init__(self):
        self.state_action_pairs: list[tuple[str, dict, bool]] = []
        self.action_counts: dict[str, int] = defaultdict(int)
        # 缓存: encoded_str -> parsed_dict, 避免每次 similarity 都 json.loads
        self._parsed_cache: dict[str, dict] = {}

    # ── Agent 调用接口 ────────────────────────────────────

    def record(self, state: dict, action: dict, result: dict):
        """记录一条观察"""
        encoded = self._encode_state(state)
        success = result.get("success", False)
        self.state_action_pairs.append((encoded, action, success))

        # 预解析缓存
        if encoded not in self._parsed_cache:
            try:
                self._parsed_cache[encoded] = json.loads(encoded)
            except json.JSONDecodeError:
                pass

        action_type = action.get("type", "unknown")
        self.action_counts[action_type] += 1

        # 容量控制
        if len(self.state_action_pairs) > self.MAX_PAIRS:
            # 清理过期的解析缓存
            kept_keys = set(e for e, _, _ in self.state_action_pairs[-self.MAX_PAIRS:])
            self._parsed_cache = {k: v for k, v in self._parsed_cache.items() if k in kept_keys}
            self.state_action_pairs = self.state_action_pairs[-self.MAX_PAIRS:]

    def predict_action(self, current_state: dict) -> dict | None:
        """
        根据当前状态预测最佳动作。

        返回:
            {"action": dict, "confidence": float} 或 None
        """
        if len(self.state_action_pairs) < 5:
            return None

        encoded = self._encode_state(current_state)

        best_score = 0.0
        best_action = None

        for prev_encoded, action, success in self.state_action_pairs:
            if not success:
                continue
            sim = self._similarity(encoded, prev_encoded)
            if sim > best_score:
                best_score = sim
                best_action = action

        if best_action is None or best_score < 0.5:
            return None

        return {"action": best_action, "confidence": best_score}

    # ── 内部方法 ──────────────────────────────────────────

    def _encode_state(self, state: dict) -> str:
        features = {
            "pos": [
                round(state.get("position", {}).get("x", 0)),
                round(state.get("position", {}).get("y", 0)),
                round(state.get("position", {}).get("z", 0)),
            ],
            "hp": int(state.get("health", 0)),
            "food": int(state.get("food", 0)),
            "blocks": sorted(set(
                b.get("name", "") for b in state.get("nearbyBlocks", [])[:5]
            )),
            "inv": sorted(set(
                i.get("name", "") for i in state.get("inventory", [])
            )),
        }
        return json.dumps(features, sort_keys=True)

    def _similarity(self, s1_json: str, s2_json: str) -> float:
        """计算两个编码状态的相似度 (0~1), 使用解析缓存"""
        try:
            s1 = self._parsed_cache.get(s1_json) or json.loads(s1_json)
            s2 = self._parsed_cache.get(s2_json) or json.loads(s2_json)
        except json.JSONDecodeError:
            return 0.0

        # 位置距离
        p1, p2 = s1.get("pos", [0, 0, 0]), s2.get("pos", [0, 0, 0])
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))
        pos_sim = 1.0 / (1.0 + dist)

        # 血量
        hp_sim = 1.0 - abs(s1.get("hp", 0) - s2.get("hp", 0)) / 20.0

        # 饥饿
        food_sim = 1.0 - abs(s1.get("food", 0) - s2.get("food", 0)) / 20.0

        # 方块 Jaccard
        b1, b2 = set(s1.get("blocks", [])), set(s2.get("blocks", []))
        block_sim = len(b1 & b2) / max(len(b1 | b2), 1)

        # 物品 Jaccard
        i1, i2 = set(s1.get("inv", [])), set(s2.get("inv", []))
        inv_sim = len(i1 & i2) / max(len(i1 | i2), 1)

        return 0.3 * pos_sim + 0.1 * hp_sim + 0.1 * food_sim + 0.2 * block_sim + 0.3 * inv_sim
