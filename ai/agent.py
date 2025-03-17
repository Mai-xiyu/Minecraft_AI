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
        self.logger = logging.getLogger("MinecraftAI.Agent")
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
                print("使用本地大语言模型")
            except Exception as e:
                print(f"本地模型加载失败: {e}")
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
        
        # 视觉系统 - 修改为默认开启
        self.use_vision = True  # 默认开启
        try:
            # 从配置中获取视觉模型类型
            vision_config = self.config.get('vision', {})
            vision_model = vision_config.get('vision_model', 'MobileNet')  # 默认使用轻量级模型
            
            # 初始化视觉学习系统
            self.vision_learning = VisionLearningSystem(model_name=vision_model)
            print("视觉学习系统已初始化")
        except Exception as e:
            print(f"视觉系统初始化出现问题，将以降级模式运行: {e}")
            # 不关闭视觉系统，但标记为降级模式
            self.vision_system_degraded = True
    
    def set_task(self, task):
        """设置当前任务"""
        if task in TASKS:
            self.current_task = task
            self.logger.info(f"设置任务: {task} - {TASKS[task]}")
            return True
        else:
            self.logger.error(f"未知任务: {task}")
            return False
    
    def step(self):
        """执行一个步骤"""
        try:
            # 获取机器人当前状态
            print("正在获取机器人状态...")  # 调试日志
            bot_status = self.get_bot_status()
            if not bot_status or not bot_status.get('connected'):
                raise Exception("机器人未连接")
            print("机器人状态:", bot_status)  # 调试日志
            
            # 如果启用了视觉，获取当前视觉画面
            current_frame = None
            if self.use_vision:
                # 直接从API获取
                current_frame = self.vision_learning.get_frame_from_bot(f"{self.mc_api}/bot/vision")
            
            # 1. 尝试使用模式识别进行预测
            if self.use_prediction and len(self.memory.memories) > 10:
                predicted_action = self.pattern_recognition.predict_action(bot_status.get('state', {}))
                if predicted_action:
                    similarity = self.pattern_recognition.calculate_similarity(
                        self.pattern_recognition.encode_state(bot_status.get('state', {})),
                        self.pattern_recognition.encode_state(bot_status.get('state', {}))
                    )
                    
                    if similarity > self.prediction_threshold:
                        print(f"使用预测的动作: {predicted_action}")
                        self.predictions_used += 1
                        
                        # 执行预测的动作
                        try:
                            bot_response = requests.post(
                                f"{self.mc_api}/bot/action",
                                json=predicted_action,
                                timeout=5
                            )
                            
                            if bot_response.status_code == 200:
                                result = bot_response.json()
                                
                                # 检查预测是否成功
                                if "success" in str(result).lower():
                                    self.prediction_successes += 1
                                
                                # 记录动作和结果
                                self.memory.add_memory({
                                    'action': predicted_action,
                                    'result': result,
                                    'timestamp': time.time(),
                                    'predicted': True
                                })
                                
                                # 更新模式识别
                                self.pattern_recognition.add_observation(
                                    bot_status.get('state', {}), 
                                    predicted_action, 
                                    result
                                )
                                
                                # 执行动作后，使用视觉学习
                                if self.use_vision and current_frame is not None:
                                    self.vision_learning.learn_from_frame(current_frame, bot_status.get('state', {}), predicted_action, result)
                                
                                return result
                        except:
                            pass  # 预测失败，回退到常规流程
            
            # 2. 生成提示词
            print("正在生成提示词...")  # 调试日志
            prompt = self.generate_prompt(self.current_task)
            print("生成的提示词:", prompt)  # 调试日志
            
            # 3. 尝试从缓存获取
            cached_response = self.cache.get(prompt)
            if cached_response:
                self.cached_responses += 1
                response = cached_response
            else:
                # 4. 使用本地模型或API
                if self.use_local_model:
                    response = self.local_model.chat(prompt)
                else:
                    self.api_calls += 1
                    response = self.api.chat(prompt)
                    
                    # 将响应添加到缓存
                    self.cache.put(prompt, response)
            
            # 处理响应
            if not response or not response.strip():
                raise Exception("API返回空响应")
            
            # 清理响应文本
            response = self._clean_response(response)
            print("清理后的响应:", response)  # 调试日志
            
            # 解析响应为动作
            try:
                action = self._parse_action(response)
                print("解析的动作:", action)  # 调试日志
                
                # 发送动作到机器人服务器
                try:
                    print("正在发送动作到机器人服务器...")  # 调试日志
                    bot_response = requests.post(
                        f"{self.mc_api}/bot/action",
                        json=action,
                        timeout=5
                    )
                    
                    print("机器人服务器响应状态码:", bot_response.status_code)  # 调试日志
                    
                    if bot_response.status_code != 200:
                        raise Exception(f"机器人服务器返回错误: {bot_response.status_code}")
                    
                    result = bot_response.json()
                    print("机器人执行结果:", result)  # 调试日志
                    
                    # 记录动作和结果
                    self.memory.add_memory({
                        'action': action,
                        'result': result,
                        'timestamp': time.time()
                    })
                    
                    # 更新模式识别系统
                    self.pattern_recognition.add_observation(
                        bot_status.get('state', {}), 
                        action, 
                        result
                    )
                    
                    # 执行动作后，使用视觉学习
                    if self.use_vision and current_frame is not None:
                        self.vision_learning.learn_from_frame(current_frame, bot_status.get('state', {}), action, result)
                    
                    # 每10步打印绩效统计
                    if (self.api_calls + self.cached_responses + self.predictions_used) % 10 == 0:
                        print(f"API调用: {self.api_calls}, 缓存命中: {self.cached_responses}, "
                              f"预测使用: {self.predictions_used}, 预测成功率: "
                              f"{self.prediction_successes/max(1, self.predictions_used):.2f}")
                    
                    return result
                    
                except requests.exceptions.RequestException as e:
                    print(f"与机器人服务器通信失败: {e}")  # 调试日志
                    raise Exception(f"与机器人服务器通信失败: {e}")
                
            except Exception as e:
                print(f"解析响应失败: {e}")  # 调试日志
                raise Exception(f"解析响应失败: {str(e)}\n响应内容: {response}")
            
        except Exception as e:
            print(f"步骤执行失败: {e}")  # 调试日志
            raise Exception(f"执行步骤失败: {e}")
    
    def _clean_response(self, response):
        """清理API响应文本"""
        try:
            # 基本清理
            response = response.strip()
            
            # 移除可能的Markdown代码块标记
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            # 再次清理空白
            response = response.strip()
            
            # 确保响应以{开始，以}结束
            if not response.startswith('{') or not response.endswith('}'):
                # 尝试提取JSON对象
                import re
                json_match = re.search(r'\{[^{}]*\}', response)
                if json_match:
                    response = json_match.group()
                else:
                    # 尝试修复常见的格式问题
                    response = response.replace("'", '"')  # 替换单引号
                    response = response.replace("\n", "")  # 移除换行
                    response = response.replace(" ", "")   # 移除空格
                    
                    if not (response.startswith('{') and response.endswith('}')):
                        raise Exception("响应不包含有效的JSON对象")
            
            return response
            
        except Exception as e:
            raise Exception(f"清理响应失败: {str(e)}\n原始响应: {response}")
    
    def _parse_action(self, response):
        """解析动作JSON"""
        try:
            import json
            action = json.loads(response)
            
            # 验证基本格式
            if not isinstance(action, dict):
                raise Exception("响应不是有效的JSON对象")
            
            # 处理action字段
            if 'action' in action and isinstance(action['action'], dict):
                action = action['action']
            
            # 验证必需字段
            if 'type' not in action:
                raise Exception("动作缺少type字段")
            
            # 验证动作类型
            valid_types = ['move', 'collect', 'craft', 'place', 'dig', 'equip', 'attack', 'chat', 'look']
            if action['type'] not in valid_types:
                raise Exception(f"无效的动作类型: {action['type']}")
            
            # 验证必需参数
            self._validate_action_params(action)
            
            return action
            
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析错误: {str(e)}")
        except Exception as e:
            raise Exception(f"动作解析错误: {str(e)}")
    
    def _validate_action_params(self, action):
        """验证动作参数"""
        action_type = action['type']
        
        # 定义每种动作类型需要的参数
        required_params = {
            'move': ['x', 'y', 'z'],
            'collect': ['blockType', 'count'],
            'craft': ['item', 'count'],
            'place': ['item', 'x', 'y', 'z'],
            'dig': ['x', 'y', 'z'],
            'equip': ['item'],
            'attack': ['entityName'],
            'chat': ['message'],
            'look': ['x', 'y', 'z']
        }
        
        # 检查必需参数
        if action_type in required_params:
            for param in required_params[action_type]:
                if param not in action:
                    raise Exception(f"动作 {action_type} 缺少必需参数: {param}")
    
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
        """加载配置文件"""
        try:
            # 尝试多个可能的配置文件位置
            possible_paths = [
                # 当前目录
                "config.json",
                # 可执行文件所在目录
                os.path.join(os.path.dirname(sys.executable), "config.json"),
                # 程序运行目录
                os.path.join(os.getcwd(), "config.json")
            ]
            
            for config_path in possible_paths:
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding='utf-8') as f:
                        return json.load(f)
                    
            raise FileNotFoundError("找不到配置文件")
        
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            # 返回默认配置
            return {
                "deepseek_api_key": "",
                "minecraft": {
                    "host": "0.0.0.0",
                    "port": 25565,
                    "username": "AI",
                    "version": "1.21.1"
                },
                "server": {
                    "port": 3002,
                    "host": "localhost"
                },
                "ai": {
                    "steps": 100,
                    "delay": 3
                }
            }
    
    def _init_conversation(self):
        """初始化与DeepSeek的对话"""
        self.deepseek.clear_history()
        self.deepseek.add_to_history("system", SYSTEM_PROMPT)
    
    def get_bot_status(self):
        """获取机器人状态"""
        try:
            response = requests.get(
                f"{self.mc_api}/bot/status",
                timeout=15  # 增加超时时间从5秒到15秒
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"状态码: {response.status_code}, 错误信息: {response.text}")
                return None
        except Exception as e:
            print(f"与机器人服务器通信失败: {e}")
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
        # 使用参数或配置文件中的值
        steps = steps or self.ai_config.get('steps', 100)
        delay = delay or self.ai_config.get('delay', 3)
        
        print(f"启动Minecraft AI代理...")
        print(f"学习系统状态: {'启用' if self.ai_config.get('learning_enabled', True) else '禁用'}")
        
        try:
            for i in range(steps):
                print(f"\n步骤 {i+1}/{steps}")
                success = self.run_step()
                
                if not success:
                    print("步骤执行失败，尝试恢复...")
                    time.sleep(delay * 2)
                
                time.sleep(delay)
                
        except KeyboardInterrupt:
            print("\n用户中断，停止AI代理")
        except Exception as e:
            print(f"运行时错误: {e}")
        finally:
            print("AI代理已停止")
            
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