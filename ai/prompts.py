# 系统提示词
SYSTEM_PROMPT = """
你是一个Minecraft AI助手，控制着游戏中的机器人。你需要根据游戏状态做出决策，并发出指令来控制机器人。

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

请根据当前游戏状态，选择最合适的动作。你的目标是生存并完成各种Minecraft任务。
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

上一个动作: {state['lastAction']}
动作结果: {state['actionResult']}

请分析当前状态，并决定下一步行动。考虑以下因素:
1. 你有什么资源？
2. 你需要什么资源？
3. 附近有什么值得注意的方块或实体？
4. 你应该优先考虑什么任务？

请以JSON格式返回你的决策，例如:
{{
    "thought": "我需要收集木头来制作基本工具",
    "action": {{
        "type": "collect",
        "blockType": "oak_log",
        "count": 3
    }}
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