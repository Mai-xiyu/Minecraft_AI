import json
import os
import time
import hashlib

class CacheSystem:
    """缓存系统，用于存储和复用API响应"""
    
    def __init__(self, cache_file="ai_cache.json", ttl=86400): # 默认缓存1天
        self.cache_file = cache_file
        self.ttl = ttl
        self.cache = {}
        self.load_cache()
        
    def load_cache(self):
        """加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"加载缓存失败: {e}")
                self.cache = {}
    
    def save_cache(self):
        """保存缓存"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def get_cache_key(self, prompt, temperature, max_tokens):
        """生成缓存键"""
        # 使用哈希来避免过长的键
        data = f"{prompt}|{temperature}|{max_tokens}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, prompt, temperature=0.7, max_tokens=2048):
        """从缓存获取结果"""
        key = self.get_cache_key(prompt, temperature, max_tokens)
        if key in self.cache:
            cached = self.cache[key]
            # 检查是否过期
            if time.time() - cached["timestamp"] < self.ttl:
                print("使用缓存的响应")
                return cached["response"]
            else:
                # 过期了，删除
                del self.cache[key]
                self.save_cache()
        return None
    
    def put(self, prompt, response, temperature=0.7, max_tokens=2048):
        """添加到缓存"""
        key = self.get_cache_key(prompt, temperature, max_tokens)
        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }
        # 每10次更新保存一次，避免频繁IO
        if len(self.cache) % 10 == 0:
            self.save_cache() 