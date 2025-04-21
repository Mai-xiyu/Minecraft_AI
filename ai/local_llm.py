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
    
    def chat(self, messages, temperature=0.7, max_tokens=2048):
        """生成回复，处理结构化的消息列表"""
        try:
            # 构建适合本地模型的文本提示词
            full_prompt = "You are a helpful Minecraft AI agent. Answer in JSON format.\n\n"
            text_input_for_history = ""

            # 遍历消息列表，构建文本提示
            for msg in messages:
                role = msg['role']
                content = msg['content']

                if role == "system":
                    full_prompt = f"{content}\n\n"
                    continue # 系统消息不加入历史记录

                prompt_line = ""
                if role == "user":
                    prompt_line += "User: "
                    # 处理用户消息内容 (可能是列表)
                    if isinstance(content, list):
                        text_parts = []
                        has_image = False
                        for item in content:
                            if item['type'] == 'text':
                                text_parts.append(item['text'])
                            elif item['type'] == 'image_url':
                                has_image = True
                        prompt_line += " ".join(text_parts)
                        if has_image:
                            prompt_line += "\n[Note: An image was provided with this message.]"
                        text_input_for_history = prompt_line # Store user text for history
                    else: # 如果 content 是字符串
                        prompt_line += content
                        text_input_for_history = prompt_line # Store user text for history

                elif role == "assistant":
                    prompt_line += f"Assistant: {content}"

                full_prompt += prompt_line + "\n"

            # 确保以 Assistant: 结尾，提示模型生成回复
            if not full_prompt.endswith("Assistant: "):
                 full_prompt += "Assistant: "

            print("本地模型接收的提示词 (截断):", full_prompt[:500] + "...") # Debug log

            # 编码
            inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)

            # 生成
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.95,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id # Explicitly set pad_token_id
                )

            # 解码并提取助手回复
            # 使用 [len(full_prompt):] 可能不准确，因为编码/解码可能改变长度
            # 更好的方法是解码整个输出，然后找到助手的回复部分
            full_decoded_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # 查找最后一个 "Assistant: " 之后的内容
            last_assistant_marker = "Assistant:"
            last_marker_index = full_decoded_output.rfind(last_assistant_marker)
            if last_marker_index != -1:
                assistant_response = full_decoded_output[last_marker_index + len(last_assistant_marker):].strip()
            else:
                # 如果找不到标记，可能生成有问题，尝试取最后一部分
                assistant_response = full_decoded_output[len(full_prompt):].strip()
                print("警告: 未在本地模型输出中找到 'Assistant:' 标记，提取可能不准确")

            print("本地模型原始响应 (截断):", assistant_response[:200] + "...") # Debug log

            # 记录对话历史 (使用提取的文本部分)
            if text_input_for_history: # Make sure we have user text to add
                 self.add_to_history("user", text_input_for_history.replace("User: ", "").strip()) # Remove marker
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