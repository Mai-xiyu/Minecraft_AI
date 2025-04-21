import os
import json
import time
from openai import OpenAI
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

class DeepSeekAPI:
    """DeepSeek API接口"""
    
    def __init__(self, api_key=None):
        # 如果没有提供API密钥，从配置文件读取
        if not api_key:
            try:
                with open("config.json", "r") as f:
                    config = json.load(f)
                    api_key = config.get("deepseek_api_key")
            except Exception as e:
                print(f"读取配置文件失败: {e}")
                api_key = None
        
        if not api_key:
            raise ValueError("未提供DeepSeek API密钥")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = "deepseek-chat"
        self.conversation_history = []
        self.max_history_length = 10  # 保留最近10条消息
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        
        # 配置请求会话
        self.session = requests.Session()
        
        # 配置重试策略
        retries = Retry(
            total=3,  # 最多重试3次
            backoff_factor=1,  # 重试间隔
            status_forcelist=[500, 502, 503, 504],  # 需要重试的HTTP状态码
            allowed_methods=["POST"]  # 允许重试的请求方法
        )
        
        # 将重试策略应用到会话
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
    
    def add_to_history(self, role, content):
        """添加消息到历史记录"""
        self.conversation_history.append({"role": role, "content": content})
        
        # 如果历史记录过长，删除最早的消息
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def chat(self, messages, temperature=0.7, max_tokens=2048):
        """调用DeepSeek API进行对话，接受结构化消息列表"""
        try:
            # print("发送到DeepSeek的消息:", json.dumps(messages, indent=2, ensure_ascii=False)) # 详细调试日志
            self.logger.info(f"发送 {len(messages)} 条消息到 DeepSeek API")

            # 发送请求
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model, # Use self.model
                    "messages": messages, # Directly use the provided messages list
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=(10, 60) # connection timeout 10s, read timeout 60s
            )

            self.logger.info(f"DeepSeek API 响应状态码: {response.status_code}")

            if response.status_code != 200:
                error_content = response.text
                self.logger.error(f"API 调用失败: HTTP {response.status_code} - {error_content}")
                # 尝试解析错误信息
                try:
                    error_json = response.json()
                    error_detail = error_json.get('error', {}).get('message', error_content)
                except json.JSONDecodeError:
                    error_detail = error_content
                raise Exception(f"API调用失败: HTTP {response.status_code} - {error_detail}")

            response_json = response.json()
            if not response_json or 'choices' not in response_json or not response_json['choices']:
                 self.logger.error(f"API 返回无效响应: {response_json}")
                 raise Exception("API返回无效响应或空choices列表")

            # 检查 choices[0] 是否存在
            if not response_json['choices'][0] or 'message' not in response_json['choices'][0]:
                 self.logger.error(f"API 响应缺少 message 结构: {response_json['choices'][0]}")
                 raise Exception("API响应缺少message结构")

            content = response_json["choices"][0]["message"].get("content")
            if content is None: # 明确检查 None，因为空字符串可能是有效响应
                 self.logger.warning(f"API 返回的 content 为 None: {response_json['choices'][0]['message']}")
                 # 可以选择返回空字符串或抛出异常，这里返回空字符串
                 content = ""
            elif not content.strip():
                 self.logger.warning("API 返回空内容字符串")

            self.logger.info("DeepSeek 返回内容处理完毕")
            # self.logger.debug(f"DeepSeek 返回内容: {content[:200]}...") # Debug log for content start

            # 记录对话历史 (只记录最后的用户和助手消息)
            # 注意：传入的 messages 可能包含系统消息等，这里简化历史记录
            # last_user_message = next((msg for msg in reversed(messages) if msg['role'] == 'user'), None)
            # if last_user_message:
            #     self.add_to_history("user", json.dumps(last_user_message['content'])) # 可能需要更好地处理多模态内容
            # self.add_to_history("assistant", content)

            return content

        except requests.exceptions.Timeout:
            print("DeepSeek API请求超时")  # 调试日志
            raise Exception("API请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            print("无法连接到DeepSeek API服务器")  # 调试日志
            raise Exception("无法连接到API服务器，请检查网络连接")
        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API请求异常: {e}")  # 调试日志
            raise Exception(f"API请求失败: {e}")
        except Exception as e:
            print(f"DeepSeek API调用错误: {e}")  # 调试日志
            raise Exception(f"API调用错误: {e}")
        finally:
            # 清理会话
            self.session.close()
    
    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = []

    def get_chat_completion(self, system_prompt, user_prompt):
        """使用DeepSeek API获取聊天回复，简化版"""
        try:
            # 添加有关任务批处理的提示
            if "任务批处理" not in system_prompt:
                system_prompt += """
## 任务批处理能力
你可以一次返回多个连续任务，但暂时请避免使用这个功能，只返回单个动作。
示例格式:

```json
{"action": "move", "x": 100, "y": 64, "z": -200, "chat": "我正在移动到新的位置"}
```

暂时不要使用任务批处理功能，直到系统更加稳定。
"""
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.5,  # 降低温度以获得更可预测的结果
                "max_tokens": 1024   # 减少token数量
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception("API响应格式错误")
        except Exception as e:
            logging.error(f"DeepSeek API异常: {e}")
            # 返回一个简单的默认响应，而不是抛出异常
            return '{"action": "look", "x": 0, "y": 64, "z": 0, "chat": "我无法执行完整的任务，正在环顾四周重新定位"}' 