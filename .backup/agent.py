import os
import json
import time
import requests
import logging
import sys
from datetime import datetime
import threading
import concurrent.futures
import gc
import torch
import re # Import re for regex parsing
from pathlib import Path # <<<确保导入 Path>>>
# Import i18n function for logging
from gui.i18n import _
try:
    from .deepseek_api import DeepSeekAPI
except ImportError:
    from .deepseek_api_alt import DeepSeekAPI
from .prompts import SYSTEM_PROMPT, TASKS, get_state_analysis_prompt
from .memory import Memory
from .learning import LearningSystem
from .local_llm import LocalLLM
from .cache_system import CacheSystem
from .pattern_recognition import PatternRecognition
from .vision_learning import VisionLearningSystem
from .vision_capture import MinecraftVisionCapture
from torchvision import transforms
from PIL import Image
import base64
from io import BytesIO
import math # <<<导入 math 以便检查 NaN/Infinity (如果需要)>>>

# 在文件开头添加任务定义
TASKS = {
    "1. 探索世界": "探索周围环境，记录发现的资源和地形",
    "2. 收集资源": "收集指定类型的资源方块",
    "3. 建造房屋": "使用收集的材料建造房屋",
    "4. 种植农作物": "种植和收获农作物",
    "5. 挖矿": "在地下寻找和开采矿物",
    "6. 制作物品": "使用收集的材料制作工具和物品",
    "7. 战斗": "与敌对生物战斗",
    "8. 自由行动": "根据环境自主决定行动"
}

# 添加全局异常处理装饰器
def safe_execution(func):
    """安全执行装饰器，防止递归错误"""
    recursion_detect = False  # 递归检测标志
    max_recursion_level = 3   # 最大递归级别
    recursion_level = 0       # 当前递归级别
    
    def wrapper(self, *args, **kwargs):
        nonlocal recursion_detect, recursion_level
        
        # 检查递归
        if recursion_detect:
            recursion_level += 1
            if recursion_level > max_recursion_level:
                self.log(f"检测到深度递归调用 ({recursion_level})，中止执行")
                recursion_level = 0
                return None
        else:
            recursion_detect = True
        
        try:
            # 使用简单异常捕获替代可能导致递归的装饰器
            return func(self, *args, **kwargs)
        except Exception as e:
            self.log(f"安全执行捕获异常: {e}")
            return None
        finally:
            if recursion_level > 0:
                recursion_level -= 1
            else:
                recursion_detect = False
                
    return wrapper

class MinecraftAgent:
    """Minecraft AI代理"""
    
    def __init__(self, api):
        self.api = api
        # Use a more specific logger name
        self.logger = logging.getLogger("MinecraftAI.Agent")
        # Ensure logger level is appropriate (e.g., INFO)
        self.logger.setLevel(logging.INFO)
        
        self.memory = Memory()
        self.current_task = None
        
        # 加载配置
        self.config = self.load_config()
        
        # 连接到Minecraft服务器
        self.mc_api = f"http://{self.config['server']['host']}:{self.config['server']['port']}"
        
        # 设置AI参数
        self.ai_config = self.config['ai']
        self.steps = self.ai_config.get('steps', 100)
        self.delay = self.ai_config.get('delay', 3)
        self.initial_task = self.ai_config.get('initial_task')
        
        if self.initial_task:
            self.set_task(self.initial_task)
        
        # 添加优化组件
        self.use_local_model = os.environ.get("USE_LOCAL_MODEL", "0") == "1"
        if self.use_local_model:
            try:
                self.local_model = LocalLLM()
                self.logger.info("Using local large language model") # Log in English or use key?
            except Exception as e:
                # Use translated log key if available, otherwise fallback
                self.logger.error(_("log_ai_error", error=f"Local model loading failed: {e}"))
                self.use_local_model = False
        
        self.cache = CacheSystem()
        self.pattern_recognition = PatternRecognition()
        self.prediction_threshold = 0.8  # 相似度阈值
        self.use_prediction = True
        
        # 绩效统计
        self.api_calls = 0
        self.cached_responses = 0
        self.predictions_used = 0
        self.prediction_successes = 0
        
        # 视觉系统
        self.use_vision = self.config.get('vision', {}).get('use_vision', True)
        self.vision_learning = None
        self.vision_system_degraded = False
        if self.use_vision:
            try:
            vision_config = self.config.get('vision', {})
                vision_model = vision_config.get('vision_model', 'MobileNet')
            self.vision_learning = VisionLearningSystem(model_name=vision_model)
                self.logger.info(f"Vision learning system initialized with model: {vision_model}")
        except Exception as e:
                 self.logger.warning(_("log_vision_system_init_failed", error=str(e)))
                 self.logger.warning(_("log_vision_system_init_warning"))
            self.vision_system_degraded = True
                 self.use_vision = False # Disable vision if init failed
    
    def set_task(self, task):
        """设置当前任务"""
        if task in TASKS:
            self.current_task = task
            self.logger.info(f"Task set: {task} - {TASKS[task]}") # Keep internal logs simpler
            return True
        else:
            self.logger.error(f"Unknown task: {task}")
            return False
    
    def step(self):
        """执行一个步骤，包含视觉信息处理"""
        try:
            # 获取机器人当前状态
            self.logger.info("Getting bot status...") # Internal log
            bot_status = self.get_bot_status()
            if not bot_status or not bot_status.get('connected'):
                # Use translated log for user
                self.logger.warning(_("log_get_bot_status_failed", error="Bot not connected or status unavailable"))
                return {"success": False, "error": "机器人未连接"}
            self.logger.info("Bot status retrieved successfully.") # Internal log
            current_state_data = bot_status.get('state', {})

            # 获取视觉帧 (Base64)
            image_base64 = None
            if self.use_vision and self.vision_learning:
                self.logger.info("Getting vision data...") # Internal log
                try:
                    vision_response = requests.get(f"{self.mc_api}/bot/vision", timeout=10)
                    if vision_response.status_code == 200:
                        vision_data = vision_response.json()
                        if vision_data.get('success') and vision_data.get('data'):
                            image_base64 = vision_data['data'].split('base64,')[-1]
                            if len(image_base64) * 3 / 4 > 5_000_000:
                                self.logger.warning("Vision image too large, skipping inclusion.") # Internal log
                                image_base64 = None
                            else:
                                self.logger.info("Vision data retrieved.") # Internal log
                        elif vision_data.get('error'):
                             self.logger.warning(_("log_vision_get_frame_failed", error=vision_data.get('error')))
                        else:
                             self.logger.info("Vision data retrieved, but no image data found.") # Internal log
                    else:
                         self.logger.warning(f"Vision API request failed: {vision_response.status_code}") # Internal log
                except requests.exceptions.RequestException as e:
                    self.logger.error(_("log_vision_get_frame_failed", error=f"RequestException: {e}"))
                except Exception as e:
                    self.logger.error(_("log_vision_get_frame_failed", error=f"Unknown error: {e}"))
            elif self.use_vision and not self.vision_learning:
                 self.logger.warning("Vision enabled but system not initialized.") # Internal log

            # 1. 模式识别预测 (Optional)
            # ...

            # 2. 生成文本提示部分
            self.logger.info("Generating text prompt...") # Internal log
            text_prompt = self.generate_text_prompt(current_state_data)
            self.logger.info("Text prompt generated.") # Internal log

            # 3. 构建发送给 LLM 的消息列表
            messages = []
            messages.append({"role": "system", "content": SYSTEM_PROMPT})
            user_content = [{"type": "text", "text": text_prompt}]
            if image_base64 and not self.use_local_model:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                })
                self.logger.info("Image data added to prompt.") # Internal log
            elif image_base64 and self.use_local_model:
                 user_content[0]["text"] += "\n\n[Note: Visual context is available.]"
                 self.logger.info("Image presence noted for local model.") # Internal log
            messages.append({"role": "user", "content": user_content})

            # 4. 缓存 (暂未实现多模态缓存)
            cached_response = None
            response = None

            # 5. 调用 LLM
            llm_type = 'Local' if self.use_local_model else 'API'
            self.logger.info(f"Calling {llm_type} LLM...") # Internal log
            start_time = time.time()
            try:
                if self.use_local_model and hasattr(self, 'local_model'):
                    response = self.local_model.chat(messages)
                elif not self.use_local_model and self.api:
                    self.api_calls += 1
                    response = self.api.chat(messages)
                else:
                     raise Exception(f"LLM client ({llm_type}) not available.")
            except Exception as llm_error:
                 self.logger.error(_("log_ai_error", error=f"LLM call failed: {llm_error}"))
                 # Fallback action
                 action = {"type": "chat", "message": "Error communicating with LLM."}
                 result = {"success": False, "error": f"LLM call failed: {llm_error}"}
                 response = None # Ensure response is None so we don't parse

            end_time = time.time()
            self.logger.info(f"LLM call finished in {end_time - start_time:.2f}s.") # Internal log
            
            # 处理响应
            action = None
            if response is not None:
                if not response.strip():
                    self.logger.warning("LLM returned empty response.") # Internal log
                    action = {"type": "chat", "message": "Thinking..."}
                    result = {"success": False, "error": "LLM returned empty response"}
                else:
                    self.logger.info("Cleaning and parsing LLM response...") # Internal log
                    try:
                        cleaned_response = self._clean_response(response)
                        action = self._parse_action(cleaned_response)
                        self.logger.info(f"Parsed action: {action}") # Internal log
                    except Exception as e:
                         self.logger.error(_("log_ai_error", error=f"Parsing LLM response failed: {e}\nRaw: {response[:200]}..."))
                         action = {"type": "chat", "message": f"Error parsing response."}
                         result = {"success": False, "error": f"Parsing response failed: {e}"}
            # If action wasn't set due to LLM error or parsing error, create a default
            if action is None:
                if 'result' not in locals(): # If result wasn't set by LLM error handler
                    action = {"type": "chat", "message": "Having trouble deciding..."}
                    result = {"success": False, "error": "Action could not be determined"}
                else: # Result already contains the error
                    action = {"type": "chat", "message": "Error encountered, pausing."}

            # 执行动作 (only if action was determined)
            if 'error' not in result: # If no error occurred before action execution stage
                try:
                    self.logger.info(f"Sending action to bot server: {action}") # Internal log
                    bot_response = requests.post(
                        f"{self.mc_api}/bot/action",
                        json=action,
                        timeout=30
                    )
                    self.logger.info(f"Bot server response code: {bot_response.status_code}") # Internal log

                    if bot_response.status_code == 200:
                    result = bot_response.json()
                        self.logger.info(f"Bot execution result: {result}") # Internal log
                    else:
                        error_msg = f"Bot server error: {bot_response.status_code} - {bot_response.text}"
                        result = {"success": False, "error": error_msg}
                        self.logger.error(_("log_send_action_failed", error=error_msg))

                except requests.exceptions.RequestException as e:
                    error_msg = f"Communication error with bot server: {e}"
                    result = {"success": False, "error": error_msg}
                    self.logger.error(_("log_send_action_failed", error=error_msg))
                    
                    # 记录动作和结果
                    self.memory.add_memory({
                        'action': action,
                        'result': result,
                        'timestamp': time.time()
                    })
                    
            # 统计
            total_steps = self.api_calls + self.cached_responses + self.predictions_used
            if total_steps > 0 and total_steps % 10 == 0:
                 # Use internal log for stats
                 self.logger.info(f"Stats - API: {self.api_calls}, Cache: {self.cached_responses}, Predict: {self.predictions_used}")
                    
                    return result
                
            except Exception as e:
             import traceback
             self.logger.critical(_("log_ai_error", error=f"CRITICAL STEP ERROR: {e}\n{traceback.format_exc()}"))
             return {"success": False, "error": f"Critical step error: {e}"}
    
    def _clean_response(self, response):
        """清理LLM返回的原始响应文本"""
        if not isinstance(response, str): # Handle non-string input safely
             self.logger.warning(f"Received non-string response to clean: {type(response)}. Converting to string.")
             response = str(response)
        # 移除可能的 Markdown 代码块标记
        response = re.sub(r"```json\\n?", "", response)
        response = re.sub(r"\\n?```", "", response)
        # 移除可能的前后空白字符
            response = response.strip()
        # 尝试替换掉可能存在的非标准引号或转义 (注意原始字符串中的反斜杠)
        response = response.replace("\\\\'", "'").replace('\\\\"', '"') # Handles escaped quotes like \\' or \\"
        # 特殊处理：如果包含换行符，通常只取第一行有效命令
        if '\\n' in response:
            self.logger.debug(f"LLM response contains newline, taking first line: {response}")
            response = response.split('\\n')[0].strip()
        return response

    def _parse_action(self, response):
        """
        解析清理后的LLM响应，按顺序尝试多种格式，并进行验证。
        失败则尝试下一种格式，最终回退到 chat。
        """
        cleaned_response = self._clean_response(response) # Clean first
        self.logger.info(f"Parsing cleaned response: {cleaned_response}")

        # 1. 尝试解析和验证 JSON 格式
        try:
            action_json = json.loads(cleaned_response)
            if isinstance(action_json, dict) and 'type' in action_json:
                self._validate_action_params(action_json) # Throws on validation error
                self.logger.info(f"Parsed and validated as JSON action: {action_json}")
                return action_json
            else:
                self.logger.warning(f"Parsed JSON is not a valid action object: {cleaned_response}")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            self.logger.debug(f"JSON parsing/validation failed: {e}. Trying next format.")
        except Exception as e:
             self.logger.error(f"Unexpected error during JSON processing: {e}. Response: {cleaned_response}")

        # 2. 尝试解析和验证函数格式: command(param=value)
        match_func = re.match(r"^(\\w+)\\s*\\((.*)\\)$", cleaned_response)
        if match_func:
            command = match_func.group(1).strip()
            params_str = match_func.group(2).strip()
            parsed_action = {"type": command}
            try:
                # Parameter parsing logic (improved robustness slightly)
                # Regex explanation:
                # (\b\w+\b)          # Capture word boundary, one or more word chars, word boundary (key)
                # \s*=\s*            # Match equals sign with optional surrounding whitespace
                # (                  # Start capturing group for value
                #  "[^"\\]*(?:\\.[^"\\]*)*"  # Match double-quoted string, handling escaped quotes
                #  |                 # OR
                #  '[^'\\]*(?:\\.[^'\\]*)*' # Match single-quoted string, handling escaped quotes
                #  |                 # OR
                #  [^,\s()]+         # Match any sequence not containing comma, whitespace, or parentheses (unquoted value)
                # )                  # End capturing group for value
                params = re.findall(r'(\b\w+\b)\s*=\s*("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\']*(?:\\.[^\']*)*\'|[^,\s()]+)',
                                    params_str)
                for key, value in params:
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes and unescape
                    if (value.startswith('"') and value.endswith('"')) or \
                            (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1].encode('utf-8').decode('unicode_escape')  # More robust unescaping

                    # Type conversion
                    try:
                        if value.lower() == 'true':
                            parsed_action[key] = True
                        elif value.lower() == 'false':
                            parsed_action[key] = False
                        elif '.' in value:
                            parsed_action[key] = float(value)
                else:
                            parsed_action[key] = int(value)
                    except ValueError:
                        parsed_action[key] = value  # Keep as string

                self._validate_action_params(parsed_action)  # Throws on validation error
                self.logger.info(f"Parsed and validated as function action: {parsed_action}")
                return parsed_action
            except (ValueError, TypeError) as e:
                self.logger.debug(
                    f"Function action parsing/validation failed: {e}. Action attempt: {parsed_action}. Trying next format.")
            except Exception as e:
                self.logger.error(f"Error parsing function parameters: {e}")
        # if match_func:
        #     command = match_func.group(1).strip()
        #     params_str = match_func.group(2).strip()
        #     parsed_action = {"type": command}
        #     try:
        #         # Parameter parsing logic (improved robustness slightly)
        #         # Regex explanation:
        #         # (\b\w+\b)          # Capture word boundary, one or more word chars, word boundary (key)
        #         # \s*=\s*            # Match equals sign with optional surrounding whitespace
        #         # (                  # Start capturing group for value
        #         #  "[^"\\]*(?:\\.[^"\\]*)*"  # Match double-quoted string, handling escaped quotes
        #         #  |                 # OR
        #         #  '[^'\]*(?:\.[^'\]*)*' # Match single-quoted string, handling escaped quotes
        #         #  |                 # OR
        #         #  [^,\s()]+         # Match any sequence not containing comma, whitespace, or parentheses (unquoted value)
        #         # )                  # End capturing group for value
        #         params = re.findall(r'(\\b\\w+\\b)\\s*=\\s*("[^"\\\\]*(?:\\\\.[^"\\\\]*)*"|'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'|[^,\\s()]+)', params_str)
        #         for key, value in params:
        #             key = key.strip()
        #             value = value.strip()
        #             # Remove quotes and unescape
        #             if (value.startswith('"') and value.endswith('"')) or \
        #                (value.startswith("'") and value.endswith("'")):
        #                 value = value[1:-1].encode('utf-8').decode('unicode_escape') # More robust unescaping
        #
        #             # Type conversion
        #             try:
        #                 if value.lower() == 'true': parsed_action[key] = True
        #                 elif value.lower() == 'false': parsed_action[key] = False
        #                 elif '.' in value: parsed_action[key] = float(value)
        #                 else: parsed_action[key] = int(value)
        #             except ValueError:
        #                 parsed_action[key] = value # Keep as string
        #
        #         self._validate_action_params(parsed_action) # Throws on validation error
        #         self.logger.info(f"Parsed and validated as function action: {parsed_action}")
        #         return parsed_action
        #     except (ValueError, TypeError) as e:
        #         self.logger.debug(f"Function action parsing/validation failed: {e}. Action attempt: {parsed_action}. Trying next format.")
        #     except Exception as e:
        #          self.logger.error(f"Error parsing function parameters: {e}")

        # 3. 尝试解析和验证简单格式: command target
        match_simple = re.match(r"^(\\w+)\\s+(.+)$", cleaned_response)
        if match_simple:
            command = match_simple.group(1).strip()
            target_str = match_simple.group(2).strip()
            parsed_action = {"type": command}
            try:
                if command == 'chat':
                    parsed_action['message'] = target_str
                    self.logger.info(f"Parsed simple action as chat: {parsed_action}")
                    # Basic validation for chat message presence
                    self._validate_action_params(parsed_action)
                    return parsed_action
                elif command in ['attack', 'jumpAttack', 'collect', 'equip', 'craft', 'placeBlock']: # Added placeBlock
                     # Assign target/blockType/itemName based on command
                     if command in ['attack', 'jumpAttack']: parsed_action['target'] = target_str
                     elif command == 'collect': parsed_action['blockType'] = target_str
                     # PlaceBlock needs coordinates too, this simple format is ambiguous for placeBlock
                     # elif command == 'placeBlock': parsed_action['itemName'] = target_str
                     elif command in ['equip', 'craft']: parsed_action['itemName'] = target_str

                     # Only proceed if the command makes sense in simple format
                     if command != 'placeBlock': # Exclude placeBlock from simple validation for now
                         self._validate_action_params(parsed_action) # Throws on validation error
                         self.logger.info(f"Parsed and validated as simple action: {parsed_action}")
                         return parsed_action
                     else:
                          self.logger.debug(f"Simple command '{command}' is ambiguous without coordinates.")
                else:
                    self.logger.debug(f"Simple command '{command}' not recognized for this format.")
            except (ValueError, TypeError) as e:
                self.logger.debug(f"Simple action parsing/validation failed: {e}. Action attempt: {parsed_action}. Falling back.")
        except Exception as e:
                 self.logger.error(f"Unexpected error processing simple action: {e}")

        # 4. 如果所有格式都失败，回退到 Chat
        self.logger.warning(f"Could not parse response into known valid action format: '{cleaned_response}'. Treating as chat.")
        fallback_action = {"type": "chat", "message": cleaned_response if isinstance(cleaned_response, str) else str(cleaned_response)}
        try:
            # Validate fallback chat action - primarily checks if message exists and is string
            self._validate_action_params(fallback_action)
        except (ValueError, TypeError) as e:
             self.logger.error(f"Fallback chat action failed validation? Error: {e}")
             # Force a minimal chat message if validation fails (e.g., empty response)
             fallback_action = {"type": "chat", "message": "[unparseable response]"}
        return fallback_action


    def _validate_action_params(self, action):
        """
        验证解析出的动作及其参数是否有效。(最终重写版本 - 健壮)
        如果验证失败，则抛出 ValueError 或 TypeError。
        """
        action_type = action.get('type')

        # 1. Validate 'type' field
        if not action_type:
            raise ValueError("Action missing 'type' field")
        if not isinstance(action_type, str):
            raise TypeError(f"Action 'type' field must be a string, got {type(action_type).__name__}")

        # 2. Define known action types and their required parameters
        known_actions = {
            "moveTo": {"x", "y", "z"},
            "collect": {"blockType"},
            "placeBlock": {"itemName", "x", "y", "z"},
            "dig": {"x", "y", "z"},
            "attack": {"target"},
            "jumpAttack": {"target"},
            "lookAt": {"x", "y", "z"},
            "equip": {"itemName"},
            "unequip": set(),
            "useHeldItem": set(),
            "craft": {"itemName"},
            "chat": {"message"},
            "setControlState": {"control", "state"},
            "clearControlStates": set(),
            "wait": set(),
        }

        # 3. Check if action type is known
        if action_type not in known_actions:
            raise ValueError(f"Unknown action type: '{action_type}'")

        required_params_set = known_actions[action_type]
        provided_params_set = set(action.keys()) - {'type'}

        # 4. Check for missing required parameters
        missing = required_params_set - provided_params_set
        if missing:
            raise ValueError(f"Action '{action_type}' missing required parameters: {', '.join(sorted(missing))}")

        # 5. Perform Simplified Type Checks
        try:
            # Coordinate Checks
            if action_type in ["moveTo", "placeBlock", "dig", "lookAt"]:
                for coord in ['x', 'y', 'z']:
                    val = action[coord]
                    if not isinstance(val, (int, float)):
                        raise TypeError(f"Parameter '{coord}' must be a number, got {type(val).__name__}")

            # String Checks
            if action_type in ["attack", "jumpAttack"]:
                val = action['target']
                if not isinstance(val, str) or not val:
                    raise TypeError("Parameter 'target' must be a non-empty string")
            elif action_type == "collect":
                val = action['blockType']
                if not isinstance(val, str) or not val:
                    raise TypeError("Parameter 'blockType' must be a non-empty string")
            elif action_type in ["placeBlock", "equip", "craft"]:
                val = action['itemName']
                if not isinstance(val, str) or not val:
                    raise TypeError("Parameter 'itemName' must be a non-empty string")
            elif action_type == "chat":
                val = action['message']
                if not isinstance(val, str):
                    raise TypeError("Parameter 'message' must be a string")
            elif action_type == "setControlState":
                val_control = action['control']
                if not isinstance(val_control, str) or not val_control:
                    raise TypeError("Parameter 'control' must be a non-empty string")

            # Boolean Check
            if action_type == "setControlState":
                val_state = action['state']
                if not isinstance(val_state, bool):
                    raise TypeError("Parameter 'state' must be a boolean")

            # Optional Param Checks
            if "ticks" in action:
                if action_type != "wait":
                    raise ValueError("Parameter 'ticks' only valid for 'wait' action")
                val_ticks = action['ticks']
                if not isinstance(val_ticks, int):
                    raise TypeError("'ticks' must be an integer")
                if val_ticks < 0:
                    raise ValueError("'ticks' cannot be negative")
            if "count" in action:
                if action_type not in ["collect", "craft"]:
                    raise ValueError(f"'count' not valid for '{action_type}' action")
                val_count = action['count']
                if not isinstance(val_count, int):
                    raise TypeError("'count' must be an integer")
                if val_count <= 0:
                    raise ValueError("'count' must be positive")
            if "radius" in action:
                if action_type != "collect":
                    raise ValueError("'radius' only valid for 'collect' action")
                val_radius = action['radius']
                if not isinstance(val_radius, (int, float)):
                    raise TypeError("'radius' must be a number")
                if val_radius <= 0:
                    raise ValueError("'radius' must be positive")
            if "destination" in action:
                if action_type not in ["equip", "unequip"]:
                    raise ValueError(f"'destination' only valid for '{action_type}' action")
                val_dest = action['destination']
                if not isinstance(val_dest, str) or not val_dest:
                    raise TypeError("'destination' must be a non-empty string")

            # Check for Unknown Parameters
            allowed_params_set = set(known_actions[action_type])
            if action_type == "wait" and "ticks" in action:
                allowed_params_set.add("ticks")
            if action_type == "collect":
                if "count" in action:
                    allowed_params_set.add("count")
                if "radius" in action:
                    allowed_params_set.add("radius")
            if action_type == "craft" and "count" in action:
                allowed_params_set.add("count")
            if action_type in ["equip", "unequip"] and "destination" in action:
                allowed_params_set.add("destination")

            unknown = provided_params_set - allowed_params_set
            if unknown:
                self.logger.warning(
                    f"Action '{action_type}' received parameters not strictly defined for it: {', '.join(sorted(unknown))}"
                )

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            raise
        else:
            self.logger.debug(f"Action validation passed for: {action}")


    # def _validate_action_params(self, action):
    #     """
    #     验证解析出的动作及其参数是否有效。(最终重写版本 - 极简)
    #     如果验证失败，则抛出 ValueError 或 TypeError。
    #     """
    #     action_type = action.get('type')
    #
    #     # 1. Validate 'type' field
    #     if not action_type:
    #         raise ValueError("Action missing 'type' field")
    #     if not isinstance(action_type, str):
    #         raise TypeError(f"Action 'type' field must be a string, got {type(action_type).__name__}")
    #
    #     # 2. Define known action types and their required parameters
    #     # We will check types and optional params individually later
    #     known_actions = {
    #         "moveTo": {"x", "y", "z"},
    #         "collect": {"blockType"},
    #         "placeBlock": {"itemName", "x", "y", "z"},
    #         "dig": {"x", "y", "z"},
    #         "attack": {"target"},
    #         "jumpAttack": {"target"},
    #         "lookAt": {"x", "y", "z"},
    #         "equip": {"itemName"},
    #         "unequip": set(), # No required params, but known type
    #         "useHeldItem": set(),
    #         "craft": {"itemName"},
    #         "chat": {"message"},
    #         "setControlState": {"control", "state"},
    #         "clearControlStates": set(),
    #         "wait": set(), # No required params, but known type
    #     }
    #
    #     # 3. Check if action type is known
    #     if action_type not in known_actions:
    #         raise ValueError(f"Unknown action type: '{action_type}'")
    #
    #     required_params_set = known_actions[action_type]
    #     provided_params_set = set(action.keys()) - {'type'}
    #
    #     # 4. Check for missing required parameters
    #     missing = required_params_set - provided_params_set
    #     if missing:
    #         raise ValueError(f"Action '{action_type}' missing required parameters: {', '.join(sorted(list(missing)))}")
    #
    #     # --- 5. Perform Simplified Type Checks (Individual Ifs) ---
    #     # This section avoids a complex try-except block that seemed to cause issues.
    #
    #     # --- Coordinate Checks ---
    #     if action_type in ["moveTo", "placeBlock", "dig", "lookAt"]:
    #         for coord in ['x', 'y', 'z']:
    #             val = action[coord]
    #             if not isinstance(val, (int, float)):
    #                 raise TypeError(f"Parameter '{coord}' must be a number, got {type(val).__name__}")
    #             # Basic value check (optional, simplified)
    #             # if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
    #             #    raise ValueError(f"Parameter '{coord}' cannot be NaN or Infinity")
    #
    #     # --- String Checks (Required) ---
    #     if action_type in ["attack", "jumpAttack"]:
    #         val = action['target']
    #         if not isinstance(val, str) or not val:
    #             raise TypeError("Parameter 'target' must be a non-empty string")
    #     elif action_type == "collect":
    #         val = action['blockType']
    #         if not isinstance(val, str) or not val:
    #             raise TypeError("Parameter 'blockType' must be a non-empty string")
    #     elif action_type in ["placeBlock", "equip", "craft"]:
    #         val = action['itemName']
    #         if not isinstance(val, str) or not val:
    #             raise TypeError("Parameter 'itemName' must be a non-empty string")
    #     elif action_type == "chat":
    #         val = action['message']
    #         if not isinstance(val, str): # Allowing empty string
    #             raise TypeError("Parameter 'message' must be a string")
    #     elif action_type == "setControlState":
    #         val_control = action['control']
    #         if not isinstance(val_control, str) or not val_control:
    #             raise TypeError("Parameter 'control' must be a non-empty string")
    #
    #     # --- Boolean Check ---
    #     if action_type == "setControlState":
    #         val_state = action['state']
    #         if not isinstance(val_state, bool):
    #             raise TypeError("Parameter 'state' must be a boolean")
    #
    #     # --- Optional Param Checks (Simplified) ---
    #     if "ticks" in action:
    #         if action_type != "wait": raise ValueError("Parameter 'ticks' only valid for 'wait' action")
    #         val_ticks = action['ticks']
    #         if not isinstance(val_ticks, int): raise TypeError("'ticks' must be an integer")
    #         if val_ticks < 0: raise ValueError("'ticks' cannot be negative")
    #     if "count" in action:
    #          if action_type not in ["collect", "craft"]: raise ValueError(f"'count' not valid for '{action_type}' action")
    #          val_count = action['count']
    #          if not isinstance(val_count, int): raise TypeError("'count' must be an integer")
    #          if val_count <= 0: raise ValueError("'count' must be positive")
    #     if "radius" in action:
    #          if action_type != "collect": raise ValueError("'radius' only valid for 'collect' action")
    #          val_radius = action['radius']
    #          if not isinstance(val_radius, (int, float)): raise TypeError("'radius' must be a number")
    #          if val_radius <= 0: raise ValueError("'radius' must be positive")
    #     if "destination" in action:
    #          if action_type not in ["equip", "unequip"]: raise ValueError(f"'destination' only valid for '{action_type}' action")
    #          val_dest = action['destination']
    #          if not isinstance(val_dest, str) or not val_dest: raise TypeError("'destination' must be a non-empty string")
    #
    #
    #     # --- Check for Unknown Parameters ---
    #     # Calculate all *potentially* allowed params based on type and optional checks
    #     allowed_params_set = set(known_actions[action_type]) # Start with required
    #     if action_type == "wait" and "ticks" in action: allowed_params_set.add("ticks")
    #     if action_type == "collect":
    #         if "count" in action: allowed_params_set.add("count")
    #         if "radius" in action: allowed_params_set.add("radius")
    #     if action_type == "craft" and "count" in action: allowed_params_set.add("count")
    #     if action_type in ["equip", "unequip"] and "destination" in action: allowed_params_set.add("destination")
    #
    #     unknown = provided_params_set - allowed_params_set
    #     if unknown:
    #         # Log warning instead of error for unknown params to be less strict?
    #         self.logger.warning(f"Action '{action_type}' received parameters not strictly defined for it: {', '.join(sorted(list(unknown)))}")
    #         # raise ValueError(f"Action '{action_type}' received unknown parameters: {', '.join(sorted(list(unknown)))}")
    #
    #
    #     # If we reached here without exceptions, the validation passed.
    #     self.logger.debug(f"Action validation passed for: {action}")
    #     # No explicit return True needed
    
    def get_status(self):
        """获取游戏状态"""
        try:
            response = requests.get(f"{self.mc_api}/status")
            return response.json()
        except Exception as e:
            self.logger.error(f"获取状态失败: {e}")
            return None
    
    def execute_action(self, action):
        """执行动作"""
        try:
            response = requests.post(f"{self.mc_api}/action", json=action)
            return response.json()
        except Exception as e:
            self.logger.error(f"执行动作失败: {e}")
            return None
    
    def load_config(self):
        """加载配置文件 with error handling"""
        # Use Path from pathlib
        config_path = Path("config.json")
        default_config = {
            "deepseek_api_key": "",
            "minecraft": {"host": "0.0.0.0", "port": 25565, "username": "AI", "version": "1.21.1"},
            "server": {"port": 3002, "host": "localhost"},
            "ai": {"steps": 100, "delay": 3, "api_key": ""}, # api_key likely needed here too
            "vision": {"use_vision": True, "vision_model": "MobileNet"},
            "gui": {"language": "zh"}
        }
        if not config_path.exists():
            # Check parent directory as well, relative path might be tricky
            alt_config_path = Path(__file__).parent.parent / "config.json" # Go up two levels from ai/
            if alt_config_path.exists():
                 config_path = alt_config_path
            else:
                self.logger.warning(f"config.json not found in standard location or project root, using default config.")
                # Save default config in project root for user
                try:
                     # Save to project root instead of potentially volatile current dir
                     save_path = Path(__file__).parent.parent / "config.json"
                     with open(save_path, "w", encoding='utf-8') as f:
                        json.dump(default_config, f, indent=2, ensure_ascii=False)
                     self.logger.info(f"Saved default configuration to {save_path}")
                except Exception as e:
                     self.logger.error(f"Failed to save default config: {e}")
                return default_config

        try:
                    with open(config_path, "r", encoding='utf-8') as f:
                loaded_config = json.load(f)
                # Deep merge (simple version for expected structure)
                merged_config = default_config.copy()
                for key, value in loaded_config.items():
                    if isinstance(value, dict) and key in merged_config and isinstance(merged_config[key], dict):
                        # Recursively merge dictionaries (level 1 depth)
                        merged_config[key] = {**merged_config[key], **value} # Python 3.5+ merge
                    else:
                        merged_config[key] = value
                return merged_config
        except json.JSONDecodeError as e:
            self.logger.error(_("log_config_load_failed", error=f"Invalid JSON in config.json ({config_path}): {e}"))
            return default_config
        except Exception as e:
            self.logger.error(_("log_config_load_failed", error=f"Error loading config ({config_path}): {e}"))
            return default_config
    
    def _init_conversation(self):
        """初始化与DeepSeek的对话"""
        self.deepseek.clear_history()
        self.deepseek.add_to_history("system", SYSTEM_PROMPT)
    
    def get_bot_status(self):
        """获取机器人状态 with error handling"""
        try:
            response = requests.get(f"{self.mc_api}/bot/status", timeout=15)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
        except requests.exceptions.Timeout:
            self.logger.warning("Timeout getting bot status.") # Internal log
                return None
        except requests.exceptions.ConnectionError:
            self.logger.warning("Connection error getting bot status.") # Internal log
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting bot status: {e}") # Internal log
            return None
        except json.JSONDecodeError:
             self.logger.error("Failed to decode JSON from bot status response.") # Internal log
            return None
    
    def send_action(self, action):
        """发送动作到机器人"""
        try:
            response = requests.post(
                f"{self.mc_api}/action",
                json=action,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"发送动作失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"发送动作请求异常: {e}")
            return None
    
    def decide_action(self, state):
        """决定下一步动作"""
        # 检查是否有新的聊天消息需要回应
        has_recent_chat = False
        if 'recentChats' in state.get('state', {}) and state['state']['recentChats']:
            # 获取最近的一条聊天，检查时间戳是否在30秒内
            last_chat = state['state']['recentChats'][0]
            if time.time() - last_chat.get('timestamp', 0)/1000 < 30:  # 时间戳是毫秒
                has_recent_chat = True
        
        # 生成提示
        prompt = self.generate_prompt(self.current_task)
        
        # 使用缓存系统
        if os.environ.get('USE_CACHE', '0') == '1' and not has_recent_chat:
            cache_key = self.cache.get_cache_key(prompt)
            cached_response = self.cache.get_cached_response(cache_key)
            
            if cached_response:
                self.cached_responses += 1
                return self.parse_ai_response(cached_response)
        
        # 使用模式识别
        if os.environ.get('USE_PREDICTION', '0') == '1' and not has_recent_chat:
            prediction = self.pattern_recognition.predict_action(state)
            if prediction and prediction.get('confidence', 0) > self.prediction_threshold:
                self.predictions_used += 1
                return prediction.get('action')
        
        # 调用AI模型获取决策
        if self.use_local_model:
            response = self.local_model.generate(prompt)
        else:
            response = self.api.chat_completion(prompt)
        
        # 更新API调用计数
        self.api_calls += 1
        
        # 如果使用缓存，则缓存结果
        if os.environ.get('USE_CACHE', '0') == '1' and not has_recent_chat:
            cache_key = self.cache.get_cache_key(prompt)
            self.cache.cache_response(cache_key, response)
        
        # 如果使用模式识别，则记录新模式
        if os.environ.get('USE_PREDICTION', '0') == '1':
            parsed_response = self.parse_ai_response(response)
            self.pattern_recognition.add_pattern(state, parsed_response)
        
        return self.parse_ai_response(response)
    
    def parse_ai_response(self, response_text):
        """解析AI响应，支持多动作返回"""
        try:
            # 尝试从文本中提取JSON
            response_text = response_text.strip()
            if response_text.startswith('```') and response_text.endswith('```'):
                response_text = response_text[3:-3].strip()
            
            # 支持单个JSON对象或JSON数组
            import json
            import re
            
            # 尝试解析完整的JSON
            try:
                # 直接尝试解析整个响应
                parsed = json.loads(response_text)
                
                # 检查是否是动作数组
                if isinstance(parsed, list):
                    return parsed  # 返回动作数组
                elif isinstance(parsed, dict):
                    # 检查是否包含actions字段
                    if 'actions' in parsed and isinstance(parsed['actions'], list):
                        return parsed['actions']  # 返回动作数组
                    # 检查是否包含action字段
                    elif 'action' in parsed and isinstance(parsed['action'], dict):
                        return [parsed['action']]  # 返回单动作数组
                    elif 'type' in parsed:
                        return [parsed]  # 这是单个动作
            
                # 未找到明确的动作格式
                raise ValueError("JSON格式正确但找不到动作数据")
            
            except json.JSONDecodeError:
                # 尝试在文本中提取JSON对象或数组
                json_pattern = r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])'
                matches = re.findall(json_pattern, response_text, re.DOTALL)
                
                if matches:
                    for match in matches:
                        try:
                            parsed = json.loads(match)
                            
                            # 与上面相同的检查
                            if isinstance(parsed, list):
                                return parsed
                            elif isinstance(parsed, dict):
                                if 'actions' in parsed and isinstance(parsed['actions'], list):
                                    return parsed['actions']
                                elif 'action' in parsed and isinstance(parsed['action'], dict):
                                    return [parsed['action']]
                                elif 'type' in parsed:
                                    return [parsed]
                        except:
                            continue
            
                # 没有找到有效的JSON
                raise ValueError("无法在响应中找到有效的JSON")
            
        except Exception as e:
            print(f"解析AI响应失败: {e}")
            # 返回一个默认动作
            return [{"type": "chat", "message": "我需要重新思考一下。"}]
    
    def run_step(self):
        """运行一个决策步骤"""
        # 获取当前状态
        state = self.get_bot_status()
        if not state:
            print("无法获取机器人状态，将重试...")
            # 重试一次
            time.sleep(2)
            state = self.get_bot_status()
            if not state:
                print("重试失败，跳过此步骤")
                return False
        
        # 初始化视觉帧
        current_frame = None
        if self.use_vision:
            try:
                # 直接从API获取
                current_frame = self.vision_learning.get_frame_from_bot(f"{self.mc_api}/bot/vision")
            except Exception as e:
                print(f"获取视觉帧失败: {e}")
        
        # 决定动作
        actions = self.decide_action(state)
        
        # 确保actions是列表格式
        if not isinstance(actions, list):
            actions = [actions]
        
        # 顺序执行多个动作
        overall_success = True
        result = None
        
        for action in actions:
            try:
                print(f"执行动作: {action}")
                
                # 执行动作
                response = requests.post(
                    f"{self.mc_api}/bot/action",
                    json=action,
                    timeout=30  # 增加超时时间到30秒
                )
                
                # 处理响应
                if response.status_code == 200:
                    result = response.json()
                    
                    # 记录到内存中
                    self.memory.add_memory(
                        action=action,
                        result=result.get("actionResult", "unknown"),
                        state=result
                    )
                    
                    # 检查动作结果
                    action_result = result.get("actionResult", "")
                    if "error" in action_result.lower() or "失败" in action_result:
                        print(f"动作执行失败: {action_result}")
                        overall_success = False
                        break
                    
                    # 如果是长时间动作，适当延迟
                    if action["type"] in ["move", "collect", "dig"]:
                        time.sleep(self.delay)  # 使用配置的延迟
                else:
                    print(f"API请求错误: {response.status_code}, {response.text}")
                    overall_success = False
                    break
                
            except requests.exceptions.Timeout:
                print(f"执行动作超时，可能任务仍在进行中")
                # 对于可能是长时间运行任务的，我们不视为失败
                if action["type"] in ["move", "collect", "dig"]:
                    time.sleep(self.delay * 2)  # 给予更长的等待时间
                    continue
                else:
                    overall_success = False
                    break
            except Exception as e:
                print(f"执行动作时出错: {e}")
                overall_success = False
                break
        
        # 如果使用视觉学习，处理当前帧
        if self.use_vision and current_frame is not None and result is not None:
            last_action = actions[-1] if actions else None
            self.vision_learning.learn_from_frame(current_frame, state.get('state', {}), last_action, result)
        
        return overall_success
    
    def run(self, steps=None, delay=None):
        """运行AI代理"""
        steps = steps or self.ai_config.get('steps', 100)
        delay = delay or self.ai_config.get('delay', 3)
        
        self.logger.info(f"Starting Minecraft AI Agent for {steps} steps with {delay}s delay...")
        self.logger.info(f"Learning System: {'Enabled' if self.ai_config.get('learning_enabled', True) else 'Disabled'}")
        
        try:
            for i in range(steps):
                self.logger.info(f"--- Step {i+1}/{steps} ---")
                step_result = self.step()

                if not step_result or not step_result.get("success"):
                    error_info = step_result.get('error', 'Unknown step failure') if step_result else 'Step returned None'
                    self.logger.warning(f"Step {i+1} failed or did not succeed: {error_info}. Attempting to continue...")
                    # Add a longer delay after a failure to allow recovery?
                    time.sleep(delay * 1.5)
                else:
                time.sleep(delay)
                
        except KeyboardInterrupt:
            self.logger.info("User interrupt detected, stopping AI agent.")
        except Exception as e:
            self.logger.critical(_("log_ai_error", error=f"CRITICAL RUNTIME ERROR: {e}"))
        finally:
            self.logger.info("Minecraft AI Agent stopped.")
            
    def set_task(self, task_key):
        """设置当前任务"""
        if task_key in TASKS:
            self.current_task = task_key
            print(f"设置当前任务: {task_key} - {TASKS[task_key]}")
            return True
        else:
            print(f"未知任务: {task_key}")
            return False

    def generate_prompt(self, task):
        """生成提示词"""
        if not task or task not in TASKS:
            task = "8. 自由行动"  # 默认任务
        
        try:
            # 获取机器人状态
            status = self.get_bot_status()
            if status and status.get('connected'):
                bot_state = status.get('state', {})
                state_info = f"""
当前状态:
- 位置: {bot_state.get('position', 'unknown')}
- 生命值: {bot_state.get('health', 'unknown')}
- 饥饿值: {bot_state.get('food', 'unknown')}
- 背包: {', '.join(str(item) for item in bot_state.get('inventory', []))}
- 附近实体: {', '.join(str(entity) for entity in bot_state.get('nearbyEntities', []))}
- 附近方块: {', '.join(str(block) for block in bot_state.get('nearbyBlocks', []))}
"""
            else:
                state_info = "无法获取机器人状态"
        except Exception as e:
            state_info = f"获取状态失败: {e}"
        
        # 获取最近的记忆
        recent_memories = self.memory.get_recent_memories(5)
        memory_text = ""
        if recent_memories:
            memory_text = "\n最近的行动:\n" + "\n".join([
                f"- 动作: {mem['action']}, 结果: {mem['result']}"
                for mem in recent_memories
            ])
        
        # 基础提示词
        base_prompt = f"""
你是一个Minecraft机器人AI助手。你需要完成以下任务：
{task} - {TASKS[task]}

{state_info}

{memory_text}

请根据当前状态和任务，生成下一步行动。必须返回一个JSON对象，包含以下字段：
- type: 动作类型（必需）
- 其他相关参数

可用的动作类型有：
1. move - 移动到指定坐标，需要 x, y, z 参数
2. collect - 收集指定方块，需要 blockType 和 count 参数
3. craft - 制作物品，需要 item 和 count 参数
4. place - 放置方块，需要 item 和 x, y, z 参数
5. dig - 挖掘方块，需要 x, y, z 参数
6. equip - 装备物品，需要 item 参数
7. attack - 攻击实体，需要 entityName 参数
8. chat - 发送消息，需要 message 参数
9. look - 看向位置，需要 x, y, z 参数

示例响应格式：
{{
    "type": "move",
    "x": 100,
    "y": 64,
    "z": 100
}}

请直接返回JSON对象，不要添加其他文本或格式。
"""
        return base_prompt

    def generate_system_prompt(self):
        """生成系统提示词，指导AI行为"""
        system_prompt = f"""# Minecraft AI助手

## 你的角色
你是一个在Minecraft世界中帮助玩家完成任务的AI助手。你可以观察环境、移动、收集资源、制作物品、建造结构，并与玩家交流。
你的目标是完成用户指定的任务，同时遵循Minecraft的游戏规则和物理限制。

## 当前任务
{self.current_task}

## 环境状态
你可以看到周围的方块、实体和物品。你还可以看到自己的位置、生命值和饥饿值。
你可以通过执行动作来与环境交互，如移动、挖掘、放置方块等。

## 聊天交互
玩家可能会通过聊天向你发送消息。你应该解读这些消息并做出适当回应。
当你需要回复玩家时，必须在JSON响应中包含"chat"字段，如：{{"action": "move", ..., "chat": "我正在向山洞移动。"}}

## 任务批处理
为了提高效率，你可以一次返回多个连续任务，而不是一次只执行一个简单动作。格式如下：
```json
{
  "tasks": [
    {"action": "move", "x": 100, "y": 64, "z": -200, "description": "移动到森林"},
    {"action": "collect", "blockType": "oak_log", "radius": 32, "description": "收集橡木"},
    {"action": "craft", "item": "crafting_table", "count": 1, "description": "制作工作台"}
  ],
  "plan": "我将先移动到森林，然后收集木头，最后制作工作台",
  "chat": "我正在执行一系列任务，首先会去森林寻找资源"
}
```

请尽可能为每个复杂目标提供3-5个连贯的任务步骤，这样可以更高效地完成目标。

## 指令格式
你必须以JSON格式返回指令，可以是单个动作或任务批处理：

可用的动作类型包括：
1. move - 移动到指定位置
   {{"action": "move", "x": 数值, "y": 数值, "z": 数值}}

2. collect - 收集指定类型的方块
   {{"action": "collect", "blockType": "方块名称", "radius": 搜索半径}}

3. place - 放置方块
   {{"action": "place", "blockType": "方块名称", "x": 数值, "y": 数值, "z": 数值}}

4. craft - 制作物品
   {{"action": "craft", "item": "物品名称", "count": 数量}}

5. dig - 挖掘特定位置的方块
   {{"action": "dig", "x": 数值, "y": 数值, "z": 数值}}

6. look - 看向特定位置
   {{"action": "look", "x": 数值, "y": 数值, "z": 数值}}

7. chat - 在游戏中发送聊天消息
   {{"action": "chat", "message": "聊天内容"}}

你需要分析当前情况并决定下一步行动。请使用环境信息和你的Minecraft知识来做出明智的决策。
"""
        return system_prompt

    def generate_user_prompt(self, state_data, recent_events=None):
        """生成用户提示，包含当前状态和最近事件"""
        # 提取各种状态信息
        inventory = self._format_inventory(state_data.get('inventory', []))
        position = self._format_position(state_data.get('position', {}))
        health = state_data.get('health', 0)
        food = state_data.get('food', 0)
        entities = self._format_entities(state_data.get('nearbyEntities', []))
        blocks = self._format_blocks(state_data.get('nearbyBlocks', []))
        last_action = state_data.get('lastAction', None)
        action_result = state_data.get('actionResult', None)
        
        # 获取聊天记录 - 重要添加
        recent_chats = self._format_chats(state_data.get('recentChats', []))
        
        # 格式化最近事件
        events_str = ""
        if recent_events:
            events_str = "## 最近事件\n" + "\n".join([f"- {event}" for event in recent_events])
        
        # 生成提示词
        prompt = f"""## 当前状态
位置: {position}
生命值: {health}/20
饥饿值: {food}/20

## 物品栏
{inventory}

## 附近实体
{entities}

## 附近方块
{blocks}

## 最近的聊天消息
{recent_chats}

## 上一个动作
{self._format_last_action(last_action)}

## 动作结果
{action_result}

{events_str}

基于以上信息，请决定下一步行动。返回JSON格式的指令。"""
        
        return prompt

    def _format_chats(self, chats):
        """格式化聊天消息"""
        if not chats:
            return "无最近聊天"
        
        result = []
        for chat in chats:
            username = chat.get('username', 'Unknown')
            message = chat.get('message', '')
            timestamp = chat.get('timestamp', 0)
            # 转换时间戳为可读格式
            time_str = datetime.fromtimestamp(timestamp/1000).strftime('%H:%M:%S') if timestamp else 'Unknown time'
            result.append(f"[{time_str}] {username}: {message}")
        
        return "\n".join(result)

    @safe_execution
    def execute_step(self, state_data):
        """加强版执行步骤函数，增加完整的防崩溃保护"""
        try:
            # 限制脚本执行时间
            start_time = time.time()
            max_execution_time = 30  # 最多执行30秒
            
            # 监控内存使用
            try:
                import psutil
                process = psutil.Process()
                initial_memory = process.memory_info().rss
                self.log(f"步骤开始内存: {initial_memory / 1024 / 1024:.1f} MB")
            except ImportError:
                pass
            
            # 生成提示
            system_prompt = self.generate_system_prompt()
            user_prompt = self.generate_user_prompt(state_data)
            
            # 记录状态信息（使用安全获取）
            pos = state_data.get('position', {})
            pos_info = f"X={pos.get('x', '?'):.1f}, Y={pos.get('y', '?'):.1f}, Z={pos.get('z', '?'):.1f}" if isinstance(pos, dict) else "未知"
            self.log(f"当前位置: {pos_info}")
            self.log(f"生命值: {state_data.get('health', '?')}/20 饥饿值: {state_data.get('food', '?')}/20")
            
            # 视觉处理 - 完全隔离以防止崩溃
            vision_features = None
            try:
                if hasattr(self, 'vision_system') and self.vision_system is not None:
                    # 强制垃圾回收
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    # 获取视觉帧 - 超时保护
                    self.log("尝试获取视觉数据...")
                    frame = None
                    try:
                        frame_future = concurrent.futures.ThreadPoolExecutor().submit(
                            self.vision_system.get_frame_from_bot
                        )
                        frame = frame_future.result(timeout=5)  # 5秒超时
                    except concurrent.futures.TimeoutError:
                        self.log("获取视觉帧超时")
                        frame = None
                    except Exception as e:
                        self.log(f"获取视觉帧异常: {e}")
                        frame = None
                    
                    # 如果获取到帧，尝试处理
                    if frame is not None:
                        try:
                            # 使用小图像
                            if hasattr(frame, 'size'):
                                frame = frame.resize((112, 112), Image.LANCZOS)  # 减小到1/4大小
                            
                            # 安全提取特征
                            if self.vision_system.model is not None:
                                features_future = concurrent.futures.ThreadPoolExecutor().submit(
                                    self.vision_system.extract_features, frame
                                )
                                vision_features = features_future.result(timeout=5)  # 5秒超时
                                if vision_features is not None:
                                    self.log("视觉特征提取成功")
                                else:
                                    self.log("视觉特征为None")
                            else:
                                self.log("视觉模型未加载")
                        except concurrent.futures.TimeoutError:
                            self.log("特征提取超时")
                        except Exception as e:
                            self.log(f"特征提取异常: {e}")
            except Exception as e:
                self.log(f"视觉处理整体异常: {e}")
            
            # AI决策 - 隔离环境
            try:
                # 检查是否超出执行时间限制
                if time.time() - start_time > max_execution_time:
                    self.log(f"步骤执行时间过长，跳过本步骤")
                    return
                
                # 获取AI响应
                ai_response = self.get_ai_response(system_prompt, user_prompt)
                
                # 解析AI响应
                action = self.parse_action(ai_response)
                
                # 检查是否超出执行时间限制
                if time.time() - start_time > max_execution_time:
                    self.log(f"步骤生成响应后时间过长，跳过执行")
                    return
                
                # 执行动作
                self.log(f"执行动作: {action.get('type', 'unknown')}")
                result = self.execute_action(action)
                
                # 记录结果
                if result.get('success'):
                    self.log(f"动作执行成功: {result.get('message', '')}")
                else:
                    self.log(f"动作执行失败: {result.get('error', 'unknown error')}")
                
                # 监控内存使用变化
                try:
                    import psutil
                    current_memory = process.memory_info().rss
                    memory_change = current_memory - initial_memory
                    self.log(f"步骤完成内存: {current_memory / 1024 / 1024:.1f} MB (变化: {memory_change / 1024 / 1024:+.1f} MB)")
                    
                    # 如果内存增长过大，强制清理
                    if memory_change > 100 * 1024 * 1024:  # 增长超过100MB
                        self.log("内存增长过大，强制清理")
                        gc.collect()
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                except Exception:
                    pass
                
            except Exception as e:
                self.log(f"AI决策执行错误: {e}")
            
        except Exception as e:
            self.log(f"执行步骤整体异常: {e}")
            # 打印堆栈跟踪以便调试
            import traceback
            self.log(f"异常详情: {traceback.format_exc()}")

    @safe_execution
    def _execute_action(self, action_json):
        """执行由AI决定的动作，安全版本"""
        try:
            # 提取动作类型和参数
            action_type = action_json.get('action', None) or action_json.get('type', None)
            if not action_type:
                raise ValueError("动作JSON中缺少'action'或'type'字段")
            
            # 处理聊天动作
            if action_type == 'chat':
                message = action_json.get('message', '')
                if not message:
                    raise ValueError("聊天动作缺少'message'字段")
                
                # 发送聊天消息
                result = self._send_chat_message(message)
                return {"success": result, "message": "发送聊天消息" + ("成功" if result else "失败")}
            
            # 其他动作通过API执行
            result = self.bot_api.post_data("/bot/action", action_json)
            
            # 记录动作结果
            return result
        except Exception as e:
            self.log(f"执行动作失败: {e}")
            raise Exception(f"执行动作失败: {e}")

    def initialize_systems(self):
        """初始化各子系统，支持无错误降级运行"""
        try:
            # 初始化视觉系统
            print("正在初始化视觉学习系统...")
            try:
                from .vision_learning import VisionLearningSystem
                self.vision_system = VisionLearningSystem(force_cpu=True)  # 强制CPU模式提高稳定性
                
                # 修复属性引用问题
                self.vision_learning = self.vision_system  # 兼容旧引用
                
                # 测试系统
                if self.vision_system._self_check():
                    self.log("视觉系统初始化成功")
                else:
                    self.log("视觉系统初始化为降级模式")
                    
            except Exception as e:
                self.log(f"视觉系统初始化失败: {e}")
                self.vision_system = None
                self.vision_learning = None  # 确保无属性错误
                
        except Exception as e:
            self.log(f"系统初始化出错: {e}")
            self.vision_system = None
            self.vision_learning = None  # 确保无属性错误

    def initialize(self):
        """初始化AI代理"""
        try:
            # 初始化视觉系统
            self.initialize_systems()
            
            # 初始化任务队列和状态
            self.task_queue = []
            self.current_plan = None
            self.plan_progress = 0
            self.last_error = None
            
            self.log("AI代理初始化完成")
            return True
        except Exception as e:
            self.log(f"初始化AI代理失败: {e}")
            return False

    def run_task_queue(self, state_data):
        """运行任务队列"""
        if not self.task_queue:
            return None
        
        # 获取下一个任务
        next_task = self.task_queue.pop(0)
        description = next_task.get('description', '未命名任务')
        
        # 更新进度
        self.plan_progress += 1
        total_tasks = self.plan_progress + len(self.task_queue)
        progress_percent = int((self.plan_progress / total_tasks) * 100)
        
        self.log(f"执行任务 {self.plan_progress}/{total_tasks} ({progress_percent}%): {description}")
        
        # 执行任务
        try:
            result = self._execute_action(next_task)
            
            # 如果任务失败且不是最后一个任务，可能需要重新规划
            if not result.get('success', False) and self.task_queue:
                error_msg = result.get('error', '未知错误')
                self.log(f"任务失败 ({error_msg})，重新评估任务计划")
                self.last_error = error_msg
                
                # 保留当前任务队列以便后续诊断
                self.failed_tasks = [next_task] + self.task_queue
                self.task_queue = []
            
            return result
        except Exception as e:
            self.log(f"执行任务失败: {e}")
            self.task_queue = []  # 清空队列
            self.last_error = str(e)
            return {"success": False, "error": str(e)}

    def check_vision_models(self):
        """检查视觉模型文件状态"""
        model_dir = self.vision_system._get_model_dir() if hasattr(self, 'vision_system') else None
        
        if not model_dir or not os.path.exists(model_dir):
            self.log("视觉模型目录不存在，将在首次运行时创建")
            return False
        
        # 检查各个模型文件
        models_status = {}
        for model_name, config in self.vision_system.MODEL_CONFIGS.items():
            model_path = os.path.join(model_dir, config["filename"])
            models_status[model_name] = os.path.exists(model_path)
        
        # 输出状态
        self.log("视觉模型文件状态:")
        for name, exists in models_status.items():
            status = "已下载" if exists else "未下载"
            self.log(f"  - {name}: {status}")
        
        return all(models_status.values())  # 如果所有模型都存在则返回True

    def is_action_better(self, action1, action2):
        """安全比较两个动作的优先级"""
        if not isinstance(action1, dict) or not isinstance(action2, dict):
            return False
        
        # 确保比较有效
        try:
            # 使用get方法安全地获取优先级，默认都是0
            prio1 = action1.get('priority', 0)
            prio2 = action2.get('priority', 0)
            return prio1 > prio2
        except Exception:
            # 如果出现任何错误，返回False
            return False

    def generate_text_prompt(self, bot_state):
         """生成仅包含文本的提示词部分"""
         state_info = f"""
当前状态:
- 位置: {bot_state.get('position', 'unknown')}
- 生命值: {bot_state.get('health', 'unknown')}
- 饥饿值: {bot_state.get('food', 'unknown')}
- 背包: {self._format_inventory(bot_state.get('inventory', []))}
- 附近实体: {self._format_entities(bot_state.get('nearbyEntities', []))}
- 附近方块: {self._format_blocks(bot_state.get('nearbyBlocks', []))}
- 最近聊天: {self._format_chats(bot_state.get('recentChats', []))}
"""
         # 获取最近的记忆
         recent_memories = self.memory.get_recent_memories(5)
         memory_text = ""
         if recent_memories:
             memory_text = "\n最近的行动:\n" + "\n".join([
                f"- 动作: {mem.get('action', 'N/A')}, 结果: {mem.get('result', 'N/A')}"
                for mem in recent_memories
             ])

         task_description = TASKS.get(self.current_task, "根据环境自主决定行动")

         text_prompt = f"""
当前任务：{self.current_task} - {task_description}

{state_info}
{memory_text}

请根据当前状态、任务和视觉信息（如果提供），生成下一步行动。必须返回一个JSON对象。
可用的动作类型有：move, collect, craft, place, dig, equip, attack, chat, look。
请直接返回JSON对象，不要添加其他文本或格式。
"""
         return text_prompt

    # Helper function to format inventory
    def _format_inventory(self, inventory):
        if not inventory: return "空"
        items = {}
        for item in inventory:
            name = item.get('name', 'unknown')
            count = item.get('count', 0)
            if name != 'unknown' and count > 0 :
                 items[name] = items.get(name, 0) + count
        return ", ".join([f"{name}({count})" for name, count in items.items()]) if items else "空"

    # Helper function to format entities
    def _format_entities(self, entities):
        if not entities: return "无"
        return ", ".join([f"{e.get('name', 'unknown')}({e.get('type','?')}, dist:{e.get('distance', 0):.1f})" for e in entities[:5]]) # Limit to 5

    # Helper function to format blocks
    def _format_blocks(self, blocks):
        if not blocks: return "无"
        # 合并相同类型的方块，并显示距离最近的一个
        block_info = {}
        for block in blocks:
            name = block.get('name', 'unknown')
            if name != 'unknown':
                 dist = block.get('distance', float('inf'))
                 if name not in block_info or dist < block_info[name][1]:
                      block_info[name] = (block_info.get(name, (0, float('inf')))[0] + 1, dist)

        return ", ".join([f"{name}({count}, nearest:{dist:.1f})" for name, (count, dist) in block_info.items()])

class AIThread(threading.Thread):
    """AI控制线程"""
    
    def __init__(self, bot_api, model, task="探索周围环境", max_steps=100, delay=2, **kwargs):
        super().__init__()
        self.bot_api = bot_api
        self.model = model
        self.current_task = task
        self.max_steps = max_steps
        self.delay = delay
        self.stop_event = threading.Event()
        self.step_count = 0
        self.status = "准备中"
        self.log_callback = kwargs.get('log_callback', print)
        self.on_status_change = kwargs.get('on_status_change', None)
        
        # 初始化任务队列
        self.task_queue = []
        
        # 初始化系统
        self.initialize_systems() 

    def run(self):
        """运行AI控制线程，增强版本"""
        self.status = "运行中"
        self.step_count = 0
        
        # 获取初始状态
        self.log("AI线程已启动")
        self.log(f"当前任务: {self.current_task}")
        
        if self.on_status_change:
            try:
                self.on_status_change(self.step_count, self.status)
            except Exception as e:
                self.log(f"更新状态回调出错: {e}")
        
        # 主执行循环
        try:
            while not self.stop_event.is_set() and self.step_count < self.max_steps:
                try:
                    # 获取当前状态
                    try:
                        state = self.bot_api.get_data("/bot/state")
                    except Exception as e:
                        self.log(f"获取状态失败: {e}")
                        state = {"position": {}, "health": 20, "food": 20}
                    
                    # 执行一步
                    self.step_count += 1
                    self.log(f"执行步骤 {self.step_count}/{self.max_steps}")
                    
                    # 简化延迟处理
                    actual_delay = self.delay
                    
                    # 安全执行步骤
                    try:
                        result = self.execute_step(state)
                        if self.on_status_change:
                            self.on_status_change(self.step_count, "执行中")
                    except Exception as e:
                        self.log(f"执行步骤失败: {e}")
                        if self.on_status_change:
                            self.on_status_change(self.step_count, "出错", error=str(e))
                    
                    # 安全等待
                    try:
                        # 分段等待，避免长时间阻塞
                        for _ in range(int(actual_delay * 2)):
                            if self.stop_event.is_set():
                                break
                            time.sleep(0.5)
                    except Exception as e:
                        self.log(f"等待出错: {e}")
                
                except Exception as e:
                    self.log(f"步骤执行循环出错: {e}")
                    # 等待一小段时间后继续
                    time.sleep(1)
            
            # 完成所有步骤
            if self.step_count >= self.max_steps:
                self.status = "已完成"
                self.log("AI已达到最大步骤数")
            else:
                self.status = "已停止"
                self.log("AI已手动停止")
        
        except Exception as e:
            self.status = "错误"
            self.log(f"AI线程严重错误: {e}")
        
        # 确保状态更新
        self.log("AI线程已终止")
        if self.on_status_change:
            try:
                self.on_status_change(self.step_count, self.status)
            except Exception as e:
                self.log(f"最终状态更新出错: {e}") 