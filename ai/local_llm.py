import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class LocalLLM:
    """本地大语言模型"""
    
    def __init__(self, model_name="deepseek-ai/deepseek-coder-1.5b", 
                 base_url="https://huggingface.co/deepseek-ai/deepseek-coder-1.5b"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {self.device}")
        
        # 加载模型和分词器
        print("正在加载DeepSeek 1.5b模型...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto",
            trust_remote_code=True
        )
        print("DeepSeek模型加载完成")
        
        self.conversation_history = []
        self.max_history_length = 10
    
    def chat(self, prompt, temperature=0.7, max_tokens=2048):
        """生成回复"""
        try:
            # 构建完整提示词
            full_prompt = "You are a helpful Minecraft AI agent. Answer in JSON format.\n\n"
            
            # 添加历史对话
            for msg in self.conversation_history:
                if msg["role"] == "user":
                    full_prompt += f"User: {msg['content']}\n"
                elif msg["role"] == "assistant":
                    full_prompt += f"Assistant: {msg['content']}\n"
            
            # 添加当前提示
            full_prompt += f"User: {prompt}\nAssistant: "
            
            # 编码
            inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)
            
            # 生成
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.95,
                    do_sample=True
                )
                
            # 解码并提取助手回复
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            assistant_response = response[len(full_prompt):].strip()
            
            # 记录对话历史
            self.add_to_history("user", prompt)
            self.add_to_history("assistant", assistant_response)
            
            return assistant_response
        
        except Exception as e:
            print(f"本地模型推理错误: {e}")
            return f"{{\"type\": \"chat\", \"message\": \"发生错误: {str(e)}\"}}"
    
    def add_to_history(self, role, content):
        """添加消息到历史记录"""
        self.conversation_history.append({"role": role, "content": content})
        
        # 如果历史记录过长，删除最早的消息
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = [] 