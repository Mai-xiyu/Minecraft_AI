"""
Minecraft AI Agent —— 核心决策循环
单一执行流: 获取状态 → 构建 prompt → (缓存/模式匹配) → LLM 调用 → 解析动作 → 执行 → 记录
"""

import json
import time
import logging
import re
import threading
import requests

from ai.llm_client import LLMClient
from ai.prompts import SYSTEM_PROMPT, format_state_message
from ai.memory import Memory
from ai.learning import LearningSystem
from ai.cache_system import CacheSystem
from ai.pattern_recognition import PatternRecognition

logger = logging.getLogger(__name__)


class MinecraftAgent:
    """
    Minecraft AI 代理。
    每次调用 step() 执行一个决策循环, 由外部计时器驱动。
    """

    def __init__(self, config: dict, llm_client: LLMClient):
        """
        参数:
            config: 完整配置字典 (从 config.json 加载)
            llm_client: 已初始化的 LLMClient 实例
        """
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
        self.max_history = 20

        # 任务 & 状态
        self._lock = threading.Lock()
        self.current_task: str = ""
        self.step_count: int = 0
        self.consecutive_errors: int = 0
        self.max_consecutive_errors: int = 5
        self.last_state: dict | None = None
        self._stop_requested: bool = False

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
        """设置/更改当前任务 (线程安全)"""
        with self._lock:
            self.current_task = task
            self.conversation_history.clear()
            self.step_count = 0
            self.consecutive_errors = 0
        logger.info("任务设置为: %s", task)

    def request_stop(self):
        """请求停止 (可从任意线程调用)"""
        self._stop_requested = True
        logger.info("Agent 收到停止请求")

    def step(self) -> dict:
        """
        执行一个完整决策循环。

        返回:
            {
                "success": bool,
                "action": dict | None,
                "response": str,        # LLM 原始回复
                "bot_state": dict | None,
                "error": str | None,
            }
        """
        # 检查停止请求
        if self._stop_requested:
            return {"success": True, "stopped": True, "action": None,
                    "response": "", "bot_state": None, "error": None}

        with self._lock:
            self.step_count += 1
            task_snapshot = self.current_task
        result = {
            "success": False,
            "action": None,
            "response": "",
            "bot_state": None,
            "error": None,
        }

        # 连续错误保护
        if self.consecutive_errors >= self.max_consecutive_errors:
            result["error"] = (
                f"连续 {self.consecutive_errors} 次错误, 已自动暂停。"
                f"请检查 Bot 连接和 LLM 配置后重试。"
            )
            result["auto_paused"] = True
            logger.warning("连续错误达到阈值 (%d), 自动暂停", self.consecutive_errors)
            return result

        try:
            # 1. 获取机器人状态
            state = self._get_bot_status()
            if state is None:
                result["error"] = "无法获取机器人状态"
                self.consecutive_errors += 1
                return result
            result["bot_state"] = state
            self.last_state = state

            # 2. 构建消息
            messages = self._build_messages(state, task_snapshot)

            # 3. 尝试缓存
            cache_key = self._make_cache_key(state, task_snapshot)
            cached = self.cache.get(cache_key) if self.use_cache else None
            if cached:
                logger.debug("命中缓存")
                llm_reply = cached
            else:
                # 4. 尝试模式匹配
                pattern_result = self.pattern.predict_action(state) if self.use_prediction else None
                if pattern_result and pattern_result.get("confidence", 0) > 0.8:
                    action = pattern_result["action"]
                    logger.info("模式匹配命中 (confidence=%.2f)", pattern_result["confidence"])
                    exec_result = self._execute_action(action)
                    self._record(state, action, exec_result, task_snapshot)
                    result["success"] = exec_result.get("success", False)
                    result["action"] = action
                    result["response"] = f"[模式匹配] {json.dumps(action, ensure_ascii=False)}"
                    result["bot_state"] = exec_result.get("state", state)
                    self.consecutive_errors = 0
                    return result

                # 5. 调用 LLM
                llm_reply = self.llm.chat(messages)
                self.cache.set(cache_key, llm_reply)

            result["response"] = llm_reply

            # 6. 解析动作
            action = self._parse_action(llm_reply)
            if action is None:
                # LLM 可能只回复了文本, 不算错误
                result["success"] = True
                self._add_to_history("assistant", llm_reply)
                return result

            # 6.5 验证动作参数
            validation_error = self._validate_action_params(action)
            if validation_error:
                logger.warning("动作参数校验失败: %s", validation_error)
                result["error"] = validation_error
                self._add_to_history("assistant", llm_reply)
                # 将校验错误反馈给 LLM，使其下次能修正
                self._add_to_history(
                    "user",
                    f"⚠ 动作参数校验失败: {validation_error}\n请根据错误信息调整策略，尝试其他方案。",
                )
                self.consecutive_errors += 1
                return result

            result["action"] = action

            # 7. 执行动作
            exec_result = self._execute_action(action)
            result["success"] = exec_result.get("success", False)
            result["bot_state"] = exec_result.get("state", state)

            # 8. 记录
            self._record(state, action, exec_result, task_snapshot)
            self._add_to_history("assistant", llm_reply)

            # 8.5 将执行结果反馈给 LLM，让它知道上一步的结果
            action_type = action.get("type", "unknown")
            if result["success"]:
                feedback_msg = exec_result.get("message", "成功")
                self._add_to_history(
                    "user",
                    f"✅ 动作 `{action_type}` 执行成功: {feedback_msg}\n请根据当前状态决定下一步。",
                )
                self.consecutive_errors = 0
            else:
                error_msg = exec_result.get("error", "未知错误")
                self._add_to_history(
                    "user",
                    f"❌ 动作 `{action_type}` 执行失败: {error_msg}\n"
                    f"请分析失败原因，不要重复同样的动作，尝试其他方案或先完成前置步骤。",
                )
                self.consecutive_errors += 1

            return result

        except Exception as e:
            logger.error("step() 异常: %s", e, exc_info=True)
            result["error"] = str(e)
            self.consecutive_errors += 1
            return result

    def get_status(self) -> dict:
        """返回 agent 当前状态摘要"""
        with self._lock:
            return {
                "task": self.current_task,
                "step_count": self.step_count,
                "consecutive_errors": self.consecutive_errors,
                "memory_count": len(self.memory.memories) if hasattr(self.memory, "memories") else 0,
                "llm_stats": self.llm.get_stats(),
            }

    # ── 内部方法 ──────────────────────────────────────────

    def _get_bot_status(self) -> dict | None:
        """从 bot 端获取状态"""
        try:
            resp = requests.get(
                f"{self.bot_base_url}/bot/status", timeout=5
            )
            data = resp.json()
            if data.get("connected") and data.get("state"):
                return data["state"]
            logger.warning("机器人未连接: %s", data.get("message", ""))
            return None
        except Exception as e:
            logger.error("获取状态失败: %s", e)
            return None

    def _build_messages(self, state: dict, task: str = "") -> list[dict]:
        """构建发给 LLM 的消息列表"""
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

        # 注入学习系统反馈 (成功策略 + 动作成功率)
        try:
            recent_successes = self.learning.get_recent_successes(limit=3)
            if recent_successes:
                tips = []
                for s in recent_successes:
                    act = s.get("action", {})
                    tips.append(f"- {act.get('type', '?')} 成功")
                # 高失败率动作警告
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
            pass  # 学习系统反馈不影响主流程

        # 历史上下文
        messages.extend(self.conversation_history[-self.max_history:])

        # 当前状态 & 任务
        state_msg = format_state_message(state, task)
        messages.append({"role": "user", "content": state_msg})

        return messages

    def _make_cache_key(self, state: dict, task: str = "") -> str:
        """根据任务 + 位置 + 血量 + 近处方块生成缓存键"""
        pos = state.get("position") or {}
        return (
            f"{task}|"
            f"{round(pos.get('x', 0))},"
            f"{round(pos.get('y', 0))},"
            f"{round(pos.get('z', 0))}|"
            f"{int(state.get('health', 0))}|"
            f"{len(state.get('nearbyEntities', []))}"
        )

    def _parse_action(self, text: str) -> dict | None:
        """
        从 LLM 回复中提取 JSON 动作。
        支持 ```json ... ``` 包裹，也支持裸 JSON。
        """
        if not text:
            return None

        # 尝试提取 json 代码块
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

        # 尝试直接解析整段
        try:
            data = json.loads(text.strip())
            if isinstance(data, dict) and ("type" in data or "action" in data):
                return data
        except json.JSONDecodeError:
            pass

        return None

    def _validate_action_params(self, action: dict) -> str | None:
        """验证动作参数是否完整, 返回错误信息或 None"""
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
        return None

    def _execute_action(self, action: dict) -> dict:
        """将动作 POST 到 bot 端执行"""
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
        """记录到记忆 & 学习系统"""
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
        """添加到对话历史 (滑动窗口)"""
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history:]

    # ── 资源释放 ──────────────────────────────────────────

    def shutdown(self):
        """保存所有数据"""
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
