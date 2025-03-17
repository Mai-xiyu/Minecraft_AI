import os
import json
import time
import random
from collections import defaultdict

class LearningSystem:
    """AI学习系统，使AI能够从经验中学习和改进"""
    
    def __init__(self, learning_file="learning.json"):
        self.learning_file = learning_file
        self.action_outcomes = defaultdict(list)  # 记录动作结果
        self.successful_strategies = []  # 成功的策略
        self.failed_strategies = []  # 失败的策略
        self.task_knowledge = {}  # 任务相关知识
        self.load_learning()
    
    def load_learning(self):
        """加载学习数据"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, "r") as f:
                    data = json.load(f)
                    self.action_outcomes = defaultdict(list, data.get("action_outcomes", {}))
                    self.successful_strategies = data.get("successful_strategies", [])
                    self.failed_strategies = data.get("failed_strategies", [])
                    self.task_knowledge = data.get("task_knowledge", {})
            except Exception as e:
                print(f"加载学习数据失败: {e}")
    
    def save_learning(self):
        """保存学习数据"""
        try:
            with open(self.learning_file, "w") as f:
                json.dump({
                    "action_outcomes": dict(self.action_outcomes),
                    "successful_strategies": self.successful_strategies,
                    "failed_strategies": self.failed_strategies,
                    "task_knowledge": self.task_knowledge
                }, f, indent=2)
        except Exception as e:
            print(f"保存学习数据失败: {e}")
    
    def record_action_outcome(self, action_type, context, result):
        """记录动作结果"""
        # 简化上下文，只保留关键信息
        simplified_context = {
            "nearby_blocks": [block["name"] for block in context.get("nearbyBlocks", [])[:5]],
            "inventory_has": [item["name"] for item in context.get("inventory", [])],
            "health": context.get("health"),
            "food": context.get("food")
        }
        
        # 记录结果
        key = f"{action_type}_{hash(json.dumps(simplified_context))}"
        self.action_outcomes[key].append({
            "result": result,
            "success": "success" in result.lower(),
            "timestamp": time.time()
        })
        
        # 定期保存
        if random.random() < 0.1:  # 10%概率保存
            self.save_learning()
    
    def learn_from_sequence(self, action_sequence, overall_result):
        """从一系列动作中学习"""
        # 如果整体结果成功，记录为成功策略
        if "success" in overall_result.lower():
            self.successful_strategies.append({
                "sequence": action_sequence,
                "result": overall_result,
                "timestamp": time.time()
            })
        else:
            self.failed_strategies.append({
                "sequence": action_sequence,
                "result": overall_result,
                "timestamp": time.time()
            })
        
        self.save_learning()
    
    def update_task_knowledge(self, task, knowledge):
        """更新任务相关知识"""
        if task not in self.task_knowledge:
            self.task_knowledge[task] = {}
        
        # 更新知识
        self.task_knowledge[task].update(knowledge)
        self.save_learning()
    
    def get_action_success_rate(self, action_type, context=None):
        """获取动作的成功率"""
        if not context:
            # 获取所有该类型动作的成功率
            all_outcomes = []
            for key, outcomes in self.action_outcomes.items():
                if key.startswith(f"{action_type}_"):
                    all_outcomes.extend(outcomes)
            
            if not all_outcomes:
                return 0.5  # 默认50%成功率
            
            success_count = sum(1 for outcome in all_outcomes if outcome["success"])
            return success_count / len(all_outcomes)
        else:
            # 获取特定上下文下的成功率
            simplified_context = {
                "nearby_blocks": [block["name"] for block in context.get("nearbyBlocks", [])[:5]],
                "inventory_has": [item["name"] for item in context.get("inventory", [])],
                "health": context.get("health"),
                "food": context.get("food")
            }
            
            key = f"{action_type}_{hash(json.dumps(simplified_context))}"
            outcomes = self.action_outcomes.get(key, [])
            
            if not outcomes:
                return self.get_action_success_rate(action_type)  # 回退到一般成功率
            
            success_count = sum(1 for outcome in outcomes if outcome["success"])
            return success_count / len(outcomes)
    
    def get_successful_strategy(self, task):
        """获取成功的策略"""
        # 过滤与任务相关的成功策略
        task_strategies = [s for s in self.successful_strategies 
                          if any(task.lower() in str(action).lower() for action in s["sequence"])]
        
        if not task_strategies:
            return None
        
        # 返回最近的成功策略
        return sorted(task_strategies, key=lambda s: s["timestamp"], reverse=True)[0]
    
    def get_task_insights(self, task):
        """获取任务相关的见解"""
        if task not in self.task_knowledge:
            return {}
        
        return self.task_knowledge[task]
    
    def generate_learning_prompt(self, task):
        """生成学习提示"""
        prompt = "基于我的学习和经验:\n\n"
        
        # 添加任务见解
        insights = self.get_task_insights(task)
        if insights:
            prompt += f"关于{task}的见解:\n"
            for key, value in insights.items():
                prompt += f"- {key}: {value}\n"
            prompt += "\n"
        
        # 添加成功策略
        strategy = self.get_successful_strategy(task)
        if strategy:
            prompt += f"成功完成{task}的策略:\n"
            for i, action in enumerate(strategy["sequence"]):
                prompt += f"{i+1}. {json.dumps(action, ensure_ascii=False)}\n"
            prompt += "\n"
        
        # 添加动作成功率
        prompt += "动作成功率:\n"
        for action_type in ["move", "collect", "craft", "place", "dig"]:
            success_rate = self.get_action_success_rate(action_type)
            prompt += f"- {action_type}: {success_rate*100:.1f}%\n"
        
        return prompt 
    
    def learn_from_player_chat(self, username, message, state):
        """从玩家聊天消息中学习"""
        # 提取关键词和指令
        important_keywords = [
            "collect", "craft", "build", "dig", "move", "go", 
            "make", "use", "get", "place", "wood", "stone", 
            "iron", "diamond", "食物", "武器", "工具"
        ]
        
        # 检查消息是否包含关键词
        has_keywords = any(keyword in message.lower() for keyword in important_keywords)
        
        if has_keywords:
            # 保存为指导记忆
            self.task_knowledge.setdefault("player_guidance", []).append({
                "username": username,
                "message": message,
                "state": state,
                "timestamp": time.time()
            })
            
            # 限制大小
            if len(self.task_knowledge["player_guidance"]) > 20:
                self.task_knowledge["player_guidance"].pop(0)
            
            return True
        return False 