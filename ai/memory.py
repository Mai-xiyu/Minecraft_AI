import os
import json
import time

class Memory:
    """记忆系统，用于存储和检索游戏状态和决策"""
    
    def __init__(self, memory_file="memory.json", capacity=20):
        self.memory_file = memory_file
        self.memories = []
        self.capacity = capacity
        self.load_memory()
    
    def load_memory(self):
        """加载记忆"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    self.memories = data.get("memories", [])
            except Exception as e:
                print(f"加载记忆失败: {e}")
    
    def save_memory(self):
        """保存记忆"""
        try:
            with open(self.memory_file, "w") as f:
                json.dump({
                    "memories": self.memories
                }, f, indent=2)
        except Exception as e:
            print(f"保存记忆失败: {e}")
    
    def add_memory(self, memory):
        """添加新记忆"""
        self.memories.append(memory)
        if len(self.memories) > self.capacity:
            self.memories.pop(0)
    
    def get_recent_memories(self, count=5):
        """获取最近的记忆"""
        return self.memories[-count:] if self.memories else []
    
    def get_relevant_memories(self, query, count=3):
        """获取与查询相关的记忆"""
        # 简单实现：根据关键词匹配
        relevant = []
        
        for memory in self.memories:
            relevance = 0
            
            # 检查动作类型
            if memory["action"] and "type" in memory["action"] and query in memory["action"]["type"]:
                relevance += 3
            
            # 检查物品名称
            if memory["action"] and "item" in memory["action"] and query in memory["action"]["item"]:
                relevance += 2
            
            # 检查方块类型
            if memory["action"] and "blockType" in memory["action"] and query in memory["action"]["blockType"]:
                relevance += 2
            
            if relevance > 0:
                relevant.append((memory, relevance))
        
        # 按相关性排序
        relevant.sort(key=lambda x: x[1], reverse=True)
        
        # 返回最相关的记忆
        return [memory for memory, _ in relevant[:count]]
    
    def clear(self):
        """清除所有记忆"""
        self.memories = []
        self.save_memory()
    
    def get_all_memories(self):
        """获取所有记忆"""
        return self.memories
    
    def __len__(self):
        return len(self.memories) 