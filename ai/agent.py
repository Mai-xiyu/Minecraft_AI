"""
Minecraft AI Agent —— 核心决策循环
单一执行流: 获取状态 → 构建 prompt → (缓存/模式匹配) → LLM 调用 → 解析动作 → 执行 → 记录
"""

import json
import time
import logging
import re
import hashlib
import threading
import requests

from ai.llm_client import LLMClient
from ai.prompts import SYSTEM_PROMPT, format_state_message
from ai.memory import Memory
from ai.learning import LearningSystem
from ai.cache_system import CacheSystem
from ai.pattern_recognition import PatternRecognition

logger = logging.getLogger(__name__)

# 查询类动作: 不消耗游戏内操作，不计入重复检测，不被模式匹配记录
QUERY_ACTIONS = {"queryRecipe", "queryBlockInfo", "searchBlocks", "queryItemInfo"}


class MinecraftAgent:
    """
    Minecraft AI 代理。
    每次调用 step() 执行一个决策循环, 由外部计时器驱动。
    """

    def __init__(self, config: dict, llm_client: LLMClient):
        self.config = config
        self.llm = llm_client

        bot_url = config.get("server", {})
        self.bot_base_url = (
            f"http://{bot_url.get('host', 'localhost')}:{bot_url.get('port', 3002)}"
        )

        # 辅助系统
        self.memory = Memory()
        self.learning = LearningSystem()
        self.cache = CacheSystem()
        self.pattern = PatternRecognition()

        # 对话上下文 (滑动窗口)
        self.conversation_history: list[dict] = []
        self.max_history = 10  # 从 20 降到 10, 减少 token 消耗

        # 任务 & 状态
        self._lock = threading.Lock()
        self.current_task: str = ""
        self.step_count: int = 0
        self.last_state: dict | None = None
        self._stop_requested: bool = False

        # 分类错误计数器
        self.network_errors: int = 0
        self.action_errors: int = 0
        self.format_errors: int = 0
        self.max_network_errors: int = 10
        self.max_action_errors: int = 8
        self.max_format_errors: int = 5
        # 兼容旧接口
        self.consecutive_errors: int = 0
        self.max_consecutive_errors: int = 5

        # 重复动作检测
        self.recent_actions: list[str] = []
        self.max_same_action_repeat: int = 3
        self._last_failed_actions: set[str] = set()

        # 配置选项
        ai_cfg = config.get("ai", {})
        self.use_cache: bool = ai_cfg.get("use_cache", True)
        self.use_prediction: bool = ai_cfg.get("use_prediction", True)

        logger.info(
            "Agent 初始化完成 | model=%s | bot=%s",
            self.llm.model, self.bot_base_url,
        )

    # ── 公开接口 ──────────────────────────────────────────

    def set_task(self, task: str):
        with self._lock:
            self.current_task = task
            self.conversation_history.clear()
            self.step_count = 0
            self.network_errors = 0
            self.action_errors = 0
            self.format_errors = 0
            self.consecutive_errors = 0
            self.recent_actions.clear()
            self._last_failed_actions.clear()
        logger.info("任务设置为: %s", task)

    def request_stop(self):
        self._stop_requested = True
        logger.info("Agent 收到停止请求")

    def step(self) -> dict:
        if self._stop_requested:
            return {"success": True, "stopped": True, "action": None,
                    "response": "", "bot_state": None, "error": None}

        with self._lock:
            self.step_count += 1
            task_snapshot = self.current_task
        result = {
            "success": False, "action": None, "response": "",
            "bot_state": None, "error": None,
        }

        # 分类错误阈值检查
        auto_pause_reason = self._check_error_thresholds()
        if auto_pause_reason:
            result["error"] = auto_pause_reason
            result["auto_paused"] = True
            logger.warning("自动暂停: %s", auto_pause_reason)
            return result

        try:
            # 1. 获取机器人状态
            state = self._get_bot_status()
            if state is None:
                result["error"] = "无法获取机器人状态"
                self.network_errors += 1
                self.consecutive_errors += 1
                return result
            result["bot_state"] = state

            # 保存执行前的状态用于进展评估
            old_state = self.last_state
            self.last_state = state

            # 2. 检测重复动作
            repeat_warning = self._check_action_repetition()
            if repeat_warning:
                self._add_to_history("user", repeat_warning)

            # 3. 构建消息
            messages = self._build_messages(state, task_snapshot)

            # 4. 尝试缓存 (仅在无重复警告时使用)
            cache_key = self._make_cache_key(state, task_snapshot)
            use_cache_this_step = self.use_cache and not repeat_warning
            cached = self.cache.get(cache_key) if use_cache_this_step else None
            if cached:
                logger.debug("命中缓存")
                llm_reply = cached
            else:
                # 5. 尝试模式匹配 (检测到重复时也跳过)
                use_pattern_this_step = self.use_prediction and not repeat_warning
                pattern_result = self.pattern.predict_action(state) if use_pattern_this_step else None
                if pattern_result and pattern_result.get("confidence", 0) > self.pattern.CONFIDENCE_THRESHOLD:
                    action = pattern_result["action"]
                    action_sig = self._action_signature(action)
                    # 跳过冷却中或刚失败的动作
                    if action_sig in self._last_failed_actions:
                        logger.info("模式匹配命中但该动作刚失败, 跳过: %s", action_sig)
                    elif self.pattern.is_on_cooldown(action_sig):
                        logger.info("模式匹配命中但该动作冷却中, 跳过: %s", action_sig)
                    else:
                        logger.info("模式匹配命中 (confidence=%.2f)", pattern_result["confidence"])
                        exec_result = self._execute_action(action)
                        self._record(state, action, exec_result, task_snapshot)
                        result["success"] = exec_result.get("success", False)
                        result["action"] = action
                        result["response"] = f"[模式匹配] {json.dumps(action, ensure_ascii=False)}"
                        result["bot_state"] = exec_result.get("state", state)
                        self._track_action(action, result["success"])
                        # 评估进展并更新模式有效性
                        self._evaluate_and_update(old_state, exec_result.get("state", state), action, result["success"])
                        if result["success"]:
                            self._reset_action_errors()
                        else:
                            self.action_errors += 1
                            self.consecutive_errors += 1
                        return result

                # 6. 调用 LLM
                llm_reply = self.llm.chat(messages)
                self.cache.set(cache_key, llm_reply)

            result["response"] = llm_reply

            # 7. 解析动作
            action = self._parse_action(llm_reply)
            if action is None:
                # LLM 回复了纯文本而非 JSON 动作 - 标记为格式错误
                self.format_errors += 1
                self.consecutive_errors += 1
                result["success"] = False
                result["error"] = "LLM 未返回有效动作"
                self._add_to_history("assistant", llm_reply)
                self._add_to_history(
                    "user",
                    "⚠ 你必须以 JSON 格式回复一个游戏动作，例如: "
                    '{"type": "collect", "blockType": "oak_log", "count": 3}\n'
                    "不要回复纯文本分析或提问。请立即给出一个具体的游戏动作。",
                )
                return result

            # 7.5 验证动作参数
            validation_error = self._validate_action_params(action)
            if validation_error:
                logger.warning("动作参数校验失败: %s", validation_error)
                result["error"] = validation_error
                self._add_to_history("assistant", llm_reply)
                self._add_to_history(
                    "user",
                    f"⚠ 动作参数校验失败: {validation_error}\n请根据错误信息调整策略，尝试其他方案。",
                )
                self.format_errors += 1
                self.consecutive_errors += 1
                return result

            result["action"] = action
            action_type = action.get("type", "unknown")
            is_query = action_type in QUERY_ACTIONS

            # 8. 执行动作
            exec_result = self._execute_action(action)
            result["success"] = exec_result.get("success", False)
            result["bot_state"] = exec_result.get("state", state)

            # 9. 记录 (查询动作不记入模式匹配)
            if not is_query:
                self._record(state, action, exec_result, task_snapshot)
            self._add_to_history("assistant", llm_reply)

            # 10. 跟踪和反馈
            if not is_query:
                self._track_action(action, result["success"])
                # 评估进展
                self._evaluate_and_update(old_state, exec_result.get("state", state), action, result["success"])

            if result["success"]:
                feedback_msg = exec_result.get("message", "成功")
                if is_query:
                    # 查询结果直接注入，不加"不要重复"提示
                    self._add_to_history("user", f"📋 查询结果:\n{feedback_msg}")
                else:
                    self._add_to_history(
                        "user",
                        f"✅ 动作 `{action_type}` 执行成功: {feedback_msg}\n"
                        f"请根据当前状态决定下一步。",
                    )
                self._reset_action_errors()
            else:
                error_msg = exec_result.get("error", "未知错误")
                if self.use_cache:
                    self.cache.delete(cache_key)
                self._add_to_history(
                    "user",
                    f"❌ 动作 `{action_type}` 执行失败: {error_msg}\n"
                    f"请分析失败原因，尝试其他方案或先完成前置步骤。"
                    f"提示: 你可以使用 queryRecipe 查询合成配方，用 searchBlocks 搜索所需资源。",
                )
                self.action_errors += 1
                self.consecutive_errors += 1

            return result

        except requests.exceptions.ConnectionError:
            logger.error("网络连接错误: 无法连接到 Bot 服务器")
            result["error"] = "网络连接错误"
            self.network_errors += 1
            self.consecutive_errors += 1
            return result
        except requests.exceptions.Timeout:
            logger.error("请求超时")
            result["error"] = "请求超时"
            self.network_errors += 1
            self.consecutive_errors += 1
            return result
        except Exception as e:
            logger.error("step() 异常: %s", e, exc_info=True)
            result["error"] = str(e)
            self.consecutive_errors += 1
            return result

    def get_status(self) -> dict:
        with self._lock:
            return {
                "task": self.current_task,
                "step_count": self.step_count,
                "consecutive_errors": self.consecutive_errors,
                "network_errors": self.network_errors,
                "action_errors": self.action_errors,
                "format_errors": self.format_errors,
                "memory_count": len(self.memory.memories) if hasattr(self.memory, "memories") else 0,
                "llm_stats": self.llm.get_stats(),
            }

    # ── 内部方法 ──────────────────────────────────────────

    def _check_error_thresholds(self) -> str | None:
        """检查各类错误计数器是否达到阈值"""
        if self.network_errors >= self.max_network_errors:
            return f"网络错误达到阈值 ({self.network_errors} 次)。请检查 Bot 服务器连接。"
        if self.action_errors >= self.max_action_errors:
            return f"动作执行错误达到阈值 ({self.action_errors} 次)。请检查游戏环境。"
        if self.format_errors >= self.max_format_errors:
            return f"LLM 格式错误达到阈值 ({self.format_errors} 次)。请检查 LLM 配置或更换模型。"
        # 兼容旧逻辑
        if self.consecutive_errors >= self.max_consecutive_errors:
            return (
                f"连续 {self.consecutive_errors} 次错误, 已自动暂停。"
                f"请检查 Bot 连接和 LLM 配置后重试。"
            )
        return None

    def _reset_action_errors(self):
        """成功执行时重置相关错误计数器"""
        self.consecutive_errors = 0
        self.action_errors = max(0, self.action_errors - 1)  # 成功时逐步恢复
        self.format_errors = max(0, self.format_errors - 1)

    def _get_bot_status(self) -> dict | None:
        try:
            resp = requests.get(
                f"{self.bot_base_url}/bot/status", timeout=5
            )
            data = resp.json()
            if data.get("connected") and data.get("state"):
                self.network_errors = max(0, self.network_errors - 1)
                return data["state"]
            logger.warning("机器人未连接: %s", data.get("message", ""))
            return None
        except Exception as e:
            logger.error("获取状态失败: %s", e)
            return None

    def _build_messages(self, state: dict, task: str = "") -> list[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 添加相关记忆
        relevant = self.memory.get_relevant_memories(task, limit=3)
        if relevant:
            memory_text = "\n".join(
                f"- {m.get('summary', m.get('action', ''))}" for m in relevant
            )
            messages.append({
                "role": "system",
                "content": f"相关经验:\n{memory_text}",
            })

        # 注入学习系统反馈
        try:
            recent_successes = self.learning.get_recent_successes(limit=3)
            if recent_successes:
                tips = []
                for s in recent_successes:
                    act = s.get("action", {})
                    tips.append(f"- {act.get('type', '?')} 成功")
                for atype in ("moveTo", "collect", "craft", "placeBlock", "attack"):
                    rate = self.learning.get_action_success_rate(atype)
                    if rate < 0.3 and rate > 0:
                        tips.append(f"- ⚠ {atype} 成功率仅 {rate:.0%}, 考虑更换策略")
                if tips:
                    messages.append({
                        "role": "system",
                        "content": "学习反馈:\n" + "\n".join(tips),
                    })
        except Exception:
            pass

        # 历史上下文
        messages.extend(self.conversation_history[-self.max_history:])

        # 当前状态 & 任务
        state_msg = format_state_message(state, task)
        messages.append({"role": "user", "content": state_msg})

        return messages

    def _make_cache_key(self, state: dict, task: str = "") -> str:
        pos = state.get("position") or {}
        inv = state.get("inventory", [])
        inv_summary = "|".join(
            sorted(f"{i.get('name', '?')}:{i.get('count', 0)}" for i in inv[:20])
        )
        # 加入最近 2 条执行结果的上下文哈希
        context_parts = []
        for msg in self.conversation_history[-2:]:
            content = msg.get("content", "")[:50]
            context_parts.append(content)
        context_hash = hashlib.md5("|".join(context_parts).encode()).hexdigest()[:8]
        return (
            f"{task}|"
            f"{round(pos.get('x', 0))},"
            f"{round(pos.get('y', 0))},"
            f"{round(pos.get('z', 0))}|"
            f"{int(state.get('health', 0))}|"
            f"{int(state.get('food', 0))}|"
            f"{len(state.get('nearbyEntities', []))}|"
            f"{inv_summary}|"
            f"{context_hash}"
        )

    def _parse_action(self, text: str) -> dict | None:
        if not text:
            return None
        patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*"type"\s*:[^{}]*\})',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.DOTALL)
            if match:
                try:
                    action = json.loads(match.group(1))
                    if "type" in action or "action" in action:
                        return action
                except json.JSONDecodeError:
                    continue
        try:
            data = json.loads(text.strip())
            if isinstance(data, dict) and ("type" in data or "action" in data):
                return data
        except json.JSONDecodeError:
            pass
        return None

    def _validate_action_params(self, action: dict) -> str | None:
        atype = action.get("type") or action.get("action", "")
        coords_required = {"moveTo", "placeBlock", "dig", "lookAt"}
        if atype in coords_required:
            for p in ("x", "y", "z"):
                if p not in action:
                    return f"动作 {atype} 缺少参数: {p}"
        if atype == "collect" and "blockType" not in action:
            return "动作 collect 缺少参数: blockType"
        if atype in ("attack", "jumpAttack") and "target" not in action:
            return f"动作 {atype} 缺少参数: target"
        if atype == "chat" and "message" not in action:
            return "动作 chat 缺少参数: message"
        if atype == "placeBlock" and "itemName" not in action:
            return "动作 placeBlock 缺少参数: itemName"
        if atype == "dropItem" and "itemName" not in action:
            return "动作 dropItem 缺少参数: itemName"
        if atype == "smelt" and "itemName" not in action:
            return "动作 smelt 缺少参数: itemName"
        if atype in ("openChest", "depositItem", "withdrawItem"):
            for p in ("x", "y", "z"):
                if p not in action:
                    return f"动作 {atype} 缺少参数: {p}"
            if atype in ("depositItem", "withdrawItem") and "itemName" not in action:
                return f"动作 {atype} 缺少参数: itemName"
        if atype == "followPlayer" and "playerName" not in action:
            return "动作 followPlayer 缺少参数: playerName"
        # 查询类动作
        if atype in ("queryRecipe", "queryBlockInfo", "queryItemInfo") and "itemName" not in action and "blockName" not in action:
            return f"动作 {atype} 缺少参数: itemName 或 blockName"
        if atype == "searchBlocks" and "blockName" not in action:
            return "动作 searchBlocks 缺少参数: blockName"
        return None

    def _execute_action(self, action: dict) -> dict:
        try:
            resp = requests.post(
                f"{self.bot_base_url}/bot/action",
                json=action,
                timeout=35,
            )
            return resp.json()
        except requests.exceptions.Timeout:
            return {"success": False, "error": "动作执行超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _record(self, state: dict, action: dict, result: dict, task: str = ""):
        try:
            self.memory.add_memory({
                "task": task,
                "action": action,
                "result": result.get("success", False),
                "summary": f"{action.get('type', '?')} -> {'成功' if result.get('success') else '失败'}",
                "timestamp": time.time(),
            })
        except Exception as e:
            logger.debug("记录记忆失败: %s", e)
        try:
            self.learning.record(state, action, result)
        except Exception as e:
            logger.debug("学习记录失败: %s", e)
        try:
            self.pattern.record(state, action, result)
        except Exception as e:
            logger.debug("模式记录失败: %s", e)

    def _add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history:]

    # ── 进展评估 ──────────────────────────────────────────

    def _evaluate_and_update(self, old_state: dict | None, new_state: dict | None,
                             action: dict, success: bool):
        """
        评估动作是否产生了实际进展，更新模式匹配的有效性。
        比较执行前后的状态变化。
        """
        if not old_state or not new_state:
            return

        made_progress = False
        action_type = action.get("type", "")

        # 物品栏变化
        old_inv = {i.get("name", "?"): i.get("count", 0) for i in old_state.get("inventory", [])}
        new_inv = {i.get("name", "?"): i.get("count", 0) for i in new_state.get("inventory", [])}
        inv_changed = old_inv != new_inv

        # 位置变化
        old_pos = old_state.get("position", {})
        new_pos = new_state.get("position", {})
        pos_dist = sum(
            (old_pos.get(k, 0) - new_pos.get(k, 0)) ** 2 for k in ("x", "y", "z")
        ) ** 0.5
        pos_changed = pos_dist > 2.0

        # 生命/饥饿变化
        hp_changed = abs(old_state.get("health", 0) - new_state.get("health", 0)) > 0.5

        # 按动作类型判断进展
        if action_type in ("collect", "craft", "smelt", "eat", "dropItem",
                           "depositItem", "withdrawItem"):
            made_progress = inv_changed
        elif action_type in ("moveTo", "explore", "followPlayer"):
            made_progress = pos_changed
        elif action_type in ("attack", "jumpAttack"):
            made_progress = True  # 攻击总算有效
        elif action_type in ("dig", "placeBlock"):
            made_progress = True  # 改变了地形
        elif action_type == "equip":
            made_progress = inv_changed  # 装备变化
        elif action_type == "chat":
            made_progress = False  # chat 永远无进展
        elif action_type in QUERY_ACTIONS:
            return  # 查询动作不更新模式
        else:
            made_progress = success and (inv_changed or pos_changed or hp_changed)

        self.pattern.update_effectiveness(action, made_progress)

    # ── 重复动作检测 ──────────────────────────────────────

    @staticmethod
    def _action_signature(action: dict) -> str:
        atype = action.get("type", "unknown")
        key_params = []
        for k in ("blockType", "itemName", "target", "playerName", "message"):
            if k in action:
                key_params.append(f"{k}={action[k]}")
        return f"{atype}({','.join(key_params)})" if key_params else atype

    def _track_action(self, action: dict, success: bool):
        sig = self._action_signature(action)
        self.recent_actions.append(sig)
        if len(self.recent_actions) > 10:
            self.recent_actions = self.recent_actions[-10:]
        if success:
            self._last_failed_actions.discard(sig)
        else:
            self._last_failed_actions.add(sig)

    def _check_action_repetition(self) -> str | None:
        """
        检查最近动作是否过度重复。
        如果检测到重复，除了返回警告文本，还将该动作加入模式匹配冷却名单。
        """
        if len(self.recent_actions) < self.max_same_action_repeat:
            return None
        tail = self.recent_actions[-self.max_same_action_repeat:]
        if len(set(tail)) == 1:
            repeated = tail[0]
            logger.warning("检测到动作重复 %d 次: %s", self.max_same_action_repeat, repeated)
            # 关键: 将重复动作加入模式匹配冷却，防止下一步立即被模式匹配恢复
            self.pattern.add_cooldown(repeated, duration=90.0)
            return (
                f"⚠ 警告: 你已经连续执行了 {self.max_same_action_repeat} 次 `{repeated}` 动作。\n"
                f"请停止重复同一动作！分析当前状态，选择完全不同的策略。\n"
                f"提示: 可以使用 queryRecipe 查看合成所需材料，用 searchBlocks 搜索附近资源，"
                f"用 explore 探索新区域。"
            )
        return None

    # ── 资源释放 ──────────────────────────────────────────

    def shutdown(self):
        try:
            self.memory.save()
        except Exception:
            pass
        try:
            self.learning.save()
        except Exception:
            pass
        try:
            self.cache.save()
        except Exception:
            pass
        logger.info("Agent 已关闭")
