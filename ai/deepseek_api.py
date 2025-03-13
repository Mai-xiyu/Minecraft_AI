import os
import json
import time
from openai import OpenAI
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
    
    def chat(self, prompt, temperature=0.7, max_tokens=2048):
        """调用DeepSeek API进行对话"""
        try:
            # 构建消息历史
            messages = []
            
            # 添加系统提示
            messages.append({
                "role": "system", 
                "content": "你是一个Minecraft机器人AI助手，需要返回JSON格式的动作指令。"
            })
            
            # 添加历史对话
            for msg in self.conversation_history:
                messages.append(msg)
                
            # 添加当前提示
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            print("发送到DeepSeek的提示词:", prompt)  # 调试日志
            
            # 发送请求
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=(10, 60)
            )
            
            print("DeepSeek API响应状态码:", response.status_code)  # 调试日志
            
            if response.status_code != 200:
                raise Exception(f"API调用失败: HTTP {response.status_code}")
            
            response_json = response.json()
            if not response_json or 'choices' not in response_json:
                raise Exception("API返回无效响应")
            
            content = response_json["choices"][0]["message"]["content"]
            if not content or not content.strip():
                raise Exception("API返回空内容")
            
            print("DeepSeek返回内容:", content)  # 调试日志
            
            # 记录对话历史
            self.add_to_history("user", prompt)
            self.add_to_history("assistant", content)
            
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