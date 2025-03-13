import os
import json
import time
import requests
import logging
import sys
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
                timeout=5
            )
            
            if response.status_code != 200:
                raise Exception(f"获取状态失败: {response.status_code}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取机器人状态失败: {e}")
    
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
        # 准备提示词
        prompt = get_state_analysis_prompt(state)
        
        # 如果有当前任务，添加任务信息
        if self.current_task and self.current_task in TASKS:
            prompt += f"\n\n当前任务: {self.current_task}\n{TASKS[self.current_task]}"
            
            # 添加学习系统的见解
            if self.ai_config.get("learning_enabled", True):
                learning_prompt = self.learning.generate_learning_prompt(self.current_task)
                prompt += f"\n\n{learning_prompt}"
        
        # 获取最近的记忆
        recent_memories = self.memory.get_recent_memories(3)
        if recent_memories:
            prompt += "\n\n最近的行动:\n"
            for i, memory in enumerate(recent_memories):
                action_str = json.dumps(memory["action"], ensure_ascii=False)
                result_str = memory["result"] if isinstance(memory["result"], str) else json.dumps(memory["result"], ensure_ascii=False)
                prompt += f"{i+1}. 动作: {action_str}, 结果: {result_str}\n"
        
        # 调用DeepSeek API
        response = self.deepseek.chat(
            prompt, 
            temperature=self.ai_config.get("temperature", 0.7),
            max_tokens=self.ai_config.get("max_tokens", 2048)
        )
        
        # 解析响应
        try:
            # 尝试直接解析JSON
            action_data = json.loads(response)
            return action_data
        except json.JSONDecodeError:
            # 如果不是纯JSON，尝试从文本中提取JSON部分
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    action_data = json.loads(json_str)
                    return action_data
                else:
                    print("无法从响应中提取JSON")
                    return {"thought": "无法理解当前状态", "action": {"type": "chat", "message": "我需要重新评估情况"}}
            except Exception as e:
                print(f"解析响应失败: {e}")
                return {"thought": "解析错误", "action": {"type": "chat", "message": "我遇到了一些问题，需要重新思考"}}
    
    def run_step(self):
        """运行一个决策步骤"""
        # 获取当前状态
        state = self.get_bot_status()
        if not state:
            print("无法获取机器人状态")
            return False
        
        # 决定动作
        decision = self.decide_action(state)
        
        # 提取思考和动作
        thought = decision.get("thought", "无思考过程")
        action = decision.get("action", {"type": "chat", "message": "我不确定该做什么"})
        
        print(f"思考: {thought}")
        print(f"动作: {json.dumps(action, ensure_ascii=False)}")
        
        # 发送动作
        result = self.send_action(action)
        
        # 更新记忆和学习系统
        if result:
            # 更新记忆
            self.memory.add_state(state, action, result.get("actionResult", "unknown"))
            
            # 更新学习系统
            if self.ai_config.get("learning_enabled", True):
                self.learning.record_action_outcome(
                    action.get("type", "unknown"), 
                    state, 
                    result.get("actionResult", "unknown")
                )
                
                # 记录动作序列
                self.action_sequence.append(action)
                
                # 如果完成了任务，学习整个序列
                if "success" in result.get("actionResult", "").lower() and len(self.action_sequence) > 0:
                    self.learning.learn_from_sequence(
                        self.action_sequence.copy(), 
                        result.get("actionResult", "unknown")
                    )
                    # 重置动作序列
                    self.action_sequence = []
                    
                    # 更新任务知识
                    if self.current_task:
                        self.learning.update_task_knowledge(self.current_task, {
                            "last_completed": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "inventory_after": json.dumps([item["name"] for item in state["inventory"]])
                        })
            
            # 更新当前状态
            self.last_action = action
            self.action_result = result.get("actionResult", "unknown")
            
            return True
        else:
            print("执行动作失败")
            return False
    
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