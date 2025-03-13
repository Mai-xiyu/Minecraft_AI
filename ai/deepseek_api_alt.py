import requests
import json

class DeepSeekAPI:
    """DeepSeek API接口（使用requests库）"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
        self.conversation_history = []
        self.max_history_length = 10  # 保留最近10条消息
    
    def add_to_history(self, role, content):
        """添加消息到历史记录"""
        self.conversation_history.append({"role": role, "content": content})
        
        # 如果历史记录过长，删除最早的消息
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def chat(self, prompt, temperature=0.7, max_tokens=2048):
        """与DeepSeek聊天"""
        try:
            # 添加用户消息到历史记录
            self.add_to_history("user", prompt)
            
            # 准备请求数据
            data = {
                "model": self.model,
                "messages": self.conversation_history,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json=data
            )
            
            # 检查响应
            if response.status_code == 200:
                result = response.json()
                reply = result["choices"][0]["message"]["content"]
                
                # 添加助手回复到历史记录
                self.add_to_history("assistant", reply)
                
                return reply
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                print(error_msg)
                return f"错误: {error_msg}"
                
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            return f"错误: {str(e)}"
    
    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = [] 