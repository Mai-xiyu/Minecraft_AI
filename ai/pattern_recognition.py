import numpy as np
import json
from collections import defaultdict

class PatternRecognition:
    """模式识别系统，识别状态-动作模式并预测动作"""
    
    def __init__(self):
        self.state_action_pairs = []
        self.action_patterns = defaultdict(list)
        self.scenario_templates = {}
    
    def encode_state(self, state):
        """将状态编码为特征向量"""
        # 简化状态到关键特征
        features = {
            "position": [state.get("position", {}).get("x", 0), 
                         state.get("position", {}).get("y", 0), 
                         state.get("position", {}).get("z", 0)],
            "health": state.get("health", 0),
            "food": state.get("food", 0),
            "nearby_blocks": [b.get("name", "") for b in state.get("nearbyBlocks", [])[:5]],
            "inventory": [i.get("name", "") for i in state.get("inventory", [])]
        }
        return json.dumps(features, sort_keys=True)
    
    def add_observation(self, state, action, result):
        """添加观察到的状态-动作对"""
        encoded_state = self.encode_state(state)
        self.state_action_pairs.append((encoded_state, action, result))
        
        # 记录动作模式
        action_type = action.get("type", "unknown")
        self.action_patterns[action_type].append((encoded_state, action, result))
        
        # 识别并保存常见场景模板
        self.identify_scenarios()
    
    def identify_scenarios(self):
        """识别常见场景模板"""
        if len(self.state_action_pairs) < 10:
            return
            
        # 分析最近10次动作
        recent_pairs = self.state_action_pairs[-10:]
        
        # 检查是否存在相似的状态序列
        state_sequence = [s for s, _, _ in recent_pairs]
        
        # 简单检测：如果相同动作连续执行
        action_sequence = [a.get("type", "") for _, a, _ in recent_pairs]
        
        for i in range(len(action_sequence) - 2):
            if action_sequence[i] == action_sequence[i+1] == action_sequence[i+2]:
                # 发现重复动作模式
                pattern_key = f"repeated_{action_sequence[i]}"
                if pattern_key not in self.scenario_templates:
                    self.scenario_templates[pattern_key] = {
                        "pattern": action_sequence[i:i+3],
                        "actions": [a for _, a, _ in recent_pairs[i:i+3]],
                        "count": 1
                    }
                else:
                    self.scenario_templates[pattern_key]["count"] += 1
    
    def predict_action(self, current_state):
        """根据当前状态预测最佳动作"""
        if not self.state_action_pairs:
            return None
            
        encoded_state = self.encode_state(current_state)
        
        # 查找最相似的状态
        similarity_scores = []
        for prev_state, action, result in self.state_action_pairs:
            # 计算相似度 (简单实现)
            similarity = self.calculate_similarity(encoded_state, prev_state)
            success = "success" in str(result).lower() if result else False
            similarity_scores.append((similarity, action, success))
        
        # 按相似度排序，只考虑成功的动作
        similarity_scores = [s for s in similarity_scores if s[2]]
        if not similarity_scores:
            return None
            
        similarity_scores.sort(reverse=True)
        
        # 返回最相似状态下的动作
        return similarity_scores[0][1]
    
    def calculate_similarity(self, state1, state2):
        """计算两个状态的相似度"""
        # 简单实现：文本匹配度
        s1 = json.loads(state1)
        s2 = json.loads(state2)
        
        # 位置相似度
        pos_sim = 1.0 / (1.0 + np.linalg.norm(
            np.array(s1["position"]) - np.array(s2["position"])
        ))
        
        # 生命值相似度
        health_sim = 1.0 - abs(s1["health"] - s2["health"]) / 20.0
        
        # 饥饿值相似度
        food_sim = 1.0 - abs(s1["food"] - s2["food"]) / 20.0
        
        # 附近方块相似度
        common_blocks = set(s1["nearby_blocks"]).intersection(set(s2["nearby_blocks"]))
        block_sim = len(common_blocks) / max(len(s1["nearby_blocks"]), len(s2["nearby_blocks"]), 1)
        
        # 物品栏相似度
        common_items = set(s1["inventory"]).intersection(set(s2["inventory"]))
        inv_sim = len(common_items) / max(len(s1["inventory"]), len(s2["inventory"]), 1)
        
        # 综合相似度
        return 0.3 * pos_sim + 0.1 * health_sim + 0.1 * food_sim + 0.2 * block_sim + 0.3 * inv_sim 