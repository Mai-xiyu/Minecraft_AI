"""
模式识别 —— 基于历史状态-动作对预测动作 (v2: 衰减 + 冷却 + 有效性评分)
"""

import json
import math
import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class PatternRecognition:
    """
    状态-动作模式匹配，返回 {"action": dict, "confidence": float}。

    v2 改进:
    - 时间衰减: 旧模式自然失效 (半衰期 300s)
    - 冷却机制: 被标记冷却的动作在冷却期内不被推荐
    - 有效性评分: 区分「成功且有用」和「成功但无用」
    - 去重存储: 避免同一 state+action 大量重复记录
    """

    MAX_PAIRS = 300
    CONFIDENCE_THRESHOLD = 0.90  # 提高阈值，减少误匹配
    DECAY_HALF_LIFE = 300.0      # 5 分钟半衰期
    DEFAULT_COOLDOWN = 60.0      # 默认冷却 60 秒

    def __init__(self):
        # 每条记录: {encoded, action, action_sig, success, timestamp, effectiveness}
        self.state_action_pairs: list[dict] = []
        self.action_counts: dict[str, int] = defaultdict(int)
        # 冷却名单: {action_sig: cooldown_until_timestamp}
        self._cooldowns: dict[str, float] = {}
        # 解析缓存
        self._parsed_cache: dict[str, dict] = {}

    # ── Agent 调用接口 ────────────────────────────────────

    def record(self, state: dict, action: dict, result: dict):
        """记录一条观察 (自动去重)"""
        encoded = self._encode_state(state)
        success = result.get("success", False)
        now = time.time()
        action_sig = self._action_signature(action)

        # 去重: 如果已有高度相似的 state+action，更新而非新增
        for pair in reversed(self.state_action_pairs[-50:]):
            if (pair["action_sig"] == action_sig
                    and self._similarity(encoded, pair["encoded"]) > 0.95):
                pair["timestamp"] = now
                pair["success"] = success
                if not success:
                    pair["effectiveness"] *= 0.5
                return

        # 新增记录
        self.state_action_pairs.append({
            "encoded": encoded,
            "action": action,
            "action_sig": action_sig,
            "success": success,
            "timestamp": now,
            "effectiveness": 1.0 if success else 0.0,
        })

        # 预解析缓存
        if encoded not in self._parsed_cache:
            try:
                self._parsed_cache[encoded] = json.loads(encoded)
            except json.JSONDecodeError:
                pass

        self.action_counts[action.get("type", "unknown")] += 1

        # 容量控制
        if len(self.state_action_pairs) > self.MAX_PAIRS:
            self.state_action_pairs = self.state_action_pairs[-self.MAX_PAIRS:]
            kept_keys = set(p["encoded"] for p in self.state_action_pairs)
            self._parsed_cache = {k: v for k, v in self._parsed_cache.items() if k in kept_keys}

    def predict_action(self, current_state: dict) -> dict | None:
        """
        根据当前状态预测最佳动作。
        得分 = similarity * time_decay * effectiveness

        返回:
            {"action": dict, "confidence": float} 或 None
        """
        if len(self.state_action_pairs) < 5:
            return None

        encoded = self._encode_state(current_state)
        now = time.time()

        # 清理过期冷却
        self._cooldowns = {k: v for k, v in self._cooldowns.items() if v > now}

        best_score = 0.0
        best_action = None

        for pair in self.state_action_pairs:
            if not pair["success"]:
                continue
            if pair["effectiveness"] < 0.3:
                continue

            # 检查冷却
            if pair["action_sig"] in self._cooldowns:
                continue

            # 时间衰减: exp(-age / half_life * ln2)
            age = now - pair["timestamp"]
            decay = math.exp(-age / self.DECAY_HALF_LIFE * 0.693)

            sim = self._similarity(encoded, pair["encoded"])
            score = sim * decay * pair["effectiveness"]

            if score > best_score:
                best_score = score
                best_action = pair["action"]

        if best_action is None or best_score < 0.5:
            return None

        return {"action": best_action, "confidence": best_score}

    def update_effectiveness(self, action: dict, made_progress: bool):
        """
        根据动作是否产生实际进展来更新有效性。
        由 Agent 在执行动作后调用。
        """
        action_sig = self._action_signature(action)
        for pair in reversed(self.state_action_pairs):
            if pair["action_sig"] == action_sig:
                if made_progress:
                    pair["effectiveness"] = min(1.0, pair["effectiveness"] * 1.1 + 0.1)
                else:
                    pair["effectiveness"] *= 0.6
                break

    def add_cooldown(self, action_sig: str, duration: float = None):
        """将某个动作签名加入冷却名单"""
        if duration is None:
            duration = self.DEFAULT_COOLDOWN
        self._cooldowns[action_sig] = time.time() + duration
        logger.info("模式匹配: 动作 %s 冷却 %.0f 秒", action_sig, duration)

    def is_on_cooldown(self, action_sig: str) -> bool:
        """检查某动作是否在冷却中"""
        return time.time() < self._cooldowns.get(action_sig, 0)

    # ── 内部方法 ──────────────────────────────────────────

    @staticmethod
    def _action_signature(action: dict) -> str:
        """生成动作签名"""
        atype = action.get("type", "unknown")
        key_params = []
        for k in ("blockType", "itemName", "target", "playerName", "message"):
            if k in action:
                key_params.append(f"{k}={action[k]}")
        return f"{atype}({','.join(key_params)})" if key_params else atype

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
                b.get("name", "") for b in state.get("nearbyBlocks", [])[:10]
            )),
            "inv": sorted(set(
                i.get("name", "") for i in state.get("inventory", [])
            )),
        }
        return json.dumps(features, sort_keys=True)

    def _similarity(self, s1_json: str, s2_json: str) -> float:
        """计算两个编码状态的相似度 (0~1)"""
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
