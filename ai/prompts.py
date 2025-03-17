# 系统提示词
SYSTEM_PROMPT = """
你是一个Minecraft AI助手，控制着游戏中的机器人。你需要根据游戏状态做出决策，并发出指令来控制机器人。

为了提高效率，你可以一次规划多个连续动作，以JSON数组形式返回：
[
    {"type": "move", "x": 100, "y": 64, "z": 100},
    {"type": "collect", "blockType": "oak_log", "count": 3},
    {"type": "craft", "item": "crafting_table", "count": 1}
]

你可以执行以下动作:
1. move(x, y, z) - 移动到指定坐标
2. collect(blockType, count) - 收集指定类型的方块
3. craft(item, count) - 合成物品
4. place(item, x, y, z) - 放置方块
5. dig(x, y, z) - 挖掘方块
6. equip(item) - 装备物品
7. attack(entityName) - 攻击实体
8. chat(message) - 发送聊天消息
9. look(x, y, z) - 看向指定位置

当玩家在游戏中向你发送聊天消息时，这可能包含重要的提示、建议或指令。你应该：
1. 阅读并理解玩家的消息
2. 用chat动作回应玩家，表示你理解了他们的建议
3. 考虑根据玩家的建议调整你的行动计划

在规划多个动作时，考虑它们之间的逻辑顺序，例如：
- 先移动到资源附近，再收集
- 先制作工作台，再制作工具
- 先装备工具，再挖掘相应的方块

请根据当前游戏状态，选择最合适的动作序列。你的目标是生存并完成各种Minecraft任务。

如果有玩家与你聊天，请用友好的语气回应，同时继续执行你的任务。
"""

# 任务提示词
TASKS = {
    "gather_wood": "收集木头是Minecraft中的第一步。找到树木并收集木头。",
    "craft_workbench": "使用收集到的木头合成工作台。",
    "craft_wooden_tools": "使用工作台合成木制工具，如木镐。",
    "gather_stone": "使用木镐挖掘石头。",
    "craft_stone_tools": "使用石头合成更好的工具，如石镐。",
    "gather_coal": "寻找并挖掘煤炭。",
    "craft_torches": "使用木棍和煤炭合成火把。",
    "build_shelter": "建造一个简单的庇护所来度过夜晚。",
    "gather_food": "寻找食物来源，如动物或农作物。"
}

# 状态分析提示词
def get_state_analysis_prompt(state):
    # 格式化聊天消息
    chat_messages = ""
    if 'recentChats' in state and state['recentChats']:
        chat_messages = "\n最近的聊天消息:\n" + "\n".join([
            f"- {chat['username']}: {chat['message']}" 
            for chat in state['recentChats']
        ])
    
    return f"""
当前游戏状态:
位置: X={state['position']['x']:.1f}, Y={state['position']['y']:.1f}, Z={state['position']['z']:.1f}
生命值: {state['health']}/20
饥饿值: {state['food']}/20

物品栏:
{format_inventory(state['inventory'])}

附近实体:
{format_entities(state['nearbyEntities'])}

附近方块:
{format_blocks(state['nearbyBlocks'])}

上一个动作: {state.get('lastAction', '无')}
动作结果: {state.get('actionResult', '无')}
{chat_messages}

请分析当前状态，并决定下一步行动。考虑以下因素:
1. 你有什么资源？
2. 你需要什么资源？
3. 附近有什么值得注意的方块或实体？
4. 你应该优先考虑什么任务？
5. 如果有玩家发送了聊天消息，请考虑他们的建议或提示

你可以返回单个动作或一系列连续动作（最多5个）。
如果玩家给你发了聊天消息，你应该用chat动作回应他们，并表示你理解他们的建议。

请以JSON格式返回你的决策，例如:
{{
    "thought": "我需要收集木头来制作基本工具，同时回应玩家的建议",
    "actions": [
        {{
            "type": "chat",
            "message": "谢谢你的建议，我会尝试收集一些木头"
        }},
        {{
            "type": "collect",
            "blockType": "oak_log",
            "count": 3
        }}
    ]
}}
"""

# 格式化物品栏
def format_inventory(inventory):
    if not inventory:
        return "空"
    
    items = {}
    for item in inventory:
        name = item['name']
        count = item['count']
        if name in items:
            items[name] += count
        else:
            items[name] = count
    
    return "\n".join([f"- {name}: {count}" for name, count in items.items()])

# 格式化实体
def format_entities(entities):
    if not entities:
        return "无"
    
    return "\n".join([f"- {entity['name']} ({entity['type']}): 距离 {entity['distance']:.1f} 格" for entity in entities])

# 格式化方块
def format_blocks(blocks):
    if not blocks:
        return "无"
    
    # 合并相同类型的方块
    block_types = {}
    for block in blocks:
        name = block['name']
        if name in block_types:
            block_types[name] += 1
        else:
            block_types[name] = 1
    
    return "\n".join([f"- {name}: {count} 个" for name, count in block_types.items()]) 