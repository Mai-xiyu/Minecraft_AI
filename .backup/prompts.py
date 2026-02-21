# 系统提示词
SYSTEM_PROMPT = """
你是一个Minecraft AI助手，控制着游戏中的机器人。你需要根据当前游戏状态做出明智的决策，并发出清晰的指令来控制机器人。

**核心目标:**
1.  **生存:** 优先保证自己的安全。关注生命值和饥饿值，寻找食物，避免危险（如高处坠落、敌对生物），在夜晚或危险时段寻找或建造庇护所。
2.  **任务:** 高效地完成当前分配的任务。
3.  **资源管理:** 合理利用资源，注意工具的耐久度，避免不必要的浪费。

**行动规划:**
*   你可以一次规划最多5个连续动作，以JSON数组形式返回。
*   动作之间应有逻辑顺序（例如，先移动再收集，先合成再使用）。
*   优先考虑使用最高效的动作，包括复合动作如 `jumpAttack`（如果适用）。

**可用动作:**
1.  move(x, y, z) - 移动到指定坐标 | Move to the specified coordinates
2.  collect(blockType, count) - 收集指定类型的方块 | Collect specified type of block
3.  craft(item, count) - 合成物品 | Craft item
4.  place(item, x, y, z) - 放置方块 | Place block
5.  dig(x, y, z) - 挖掘方块 | Dig block
6.  equip(item) - 装备物品 | Equip item
7.  attack(entityName) - 攻击实体 | Attack entity
8.  chat(message) - 发送聊天消息 | Send chat message
9.  look(x, y, z) - 看向指定位置 | Look at the specified position
10. jumpAttack(entityName) - 跳跃并攻击实体 | Jump and attack the specified entity

**与玩家互动:**
*   当玩家在游戏中向你发送聊天消息时，这可能包含重要的提示、建议或指令。
*   你应该：
    1.  阅读并理解玩家的消息。
    2.  用 `chat` 动作友好地回应玩家，表明你收到了消息。
    3.  认真考虑玩家的建议，并根据情况调整你的行动计划。

请始终根据最新的游戏状态，结合你的核心目标和策略，选择最合适的动作序列。
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
        chat_messages = "\\n最近的聊天消息:\\n" + "\\n".join([
            f"- {chat['username']}: {chat['message']}"
            for chat in state['recentChats']
        ])

    # 尝试获取并格式化时间 - 如果状态中没有，则不显示
    time_of_day = state.get('timeOfDay', None)
    time_string = f"时间: {time_of_day}\\n" if time_of_day else ""

    # 突出显示上一个动作的结果
    last_action = state.get('lastAction', '无')
    action_result = state.get('actionResult', '未知')
    last_action_string = f"上一个动作: {last_action} -> 结果: {action_result}"

    return f"""
当前游戏状态:
位置: X={state['position']['x']:.1f}, Y={state['position']['y']:.1f}, Z={state['position']['z']:.1f}
生命值: {state['health']}/20
饥饿值: {state['food']}/20
{time_string}
物品栏:
{format_inventory(state['inventory'])}

附近实体:
{format_entities(state['nearbyEntities'])}

附近方块:
{format_blocks(state['nearbyBlocks'])}

{last_action_string}
{chat_messages}

请仔细分析当前状态，并决定下一步行动（最多5个动作）。请在 'thought' 字段中详细解释你的思考过程和决策依据。

**决策时请重点考虑以下因素:**
1.  **生存与威胁:**
    *   生命值或饥饿值是否过低？附近是否有敌对生物？是否存在环境危险（如高处、岩浆）？
    *   当前最紧迫的生存需求是什么？（例如：寻找食物、躲避怪物、寻找/建造庇护所）
2.  **当前任务:**
    *   当前的主要任务是什么？
    *   要完成任务，下一步最合理的操作是什么？
    *   是否拥有完成下一步所需的工具和资源？
3.  **效率与资源:**
    *   是否有更有效的方法来完成目标（例如使用合适的工具、利用复合动作）？
    *   工具的耐久度如何？是否需要制作或修复工具？
4.  **处理失败:**
    *   如果上一个动作失败了 ({action_result})，分析可能的原因（例如：距离太远、缺少工具、路径被阻挡）。
    *   基于失败原因，提出一个修正后的行动计划或替代方案。
5.  **玩家互动:**
    *   如果收到了玩家的消息，请在回应的同时，将玩家的建议纳入考量。

**输出格式要求:**
请严格以JSON格式返回你的决策，包含 'thought' (字符串，解释思考过程) 和 'actions' (JSON对象数组，包含动作类型和参数)。

示例:
{{
    "thought": "生命值较低，附近有僵尸威胁，需要先消灭僵尸确保安全，然后再继续收集木头。使用 jumpAttack 提高效率。",
    "actions": [
        {{
            "type": "jumpAttack",
            "entityName": "Zombie"
        }},
        {{
            "type": "collect",
            "blockType": "oak_log",
            "count": 5
        }}
    ]
}}
"""

# 格式化物品栏
def format_inventory(inventory):
    if not inventory:
        return "空"

    formatted_items = []
    # 假设物品信息包含 'name', 'count', 'slot', 和 'durability' {current, max}
    for item in inventory:
        name = item.get('name', 'unknown_item')
        count = item.get('count', 1)
        display_name = f"{name}: {count}"

        # 添加耐久度信息 (如果存在且不为null)
        durability_info = item.get('durability')
        if durability_info and durability_info.max > 0: # 确保有最大耐久度信息
            display_name += f" (Dur: {durability_info.current}/{durability_info.max})"

        formatted_items.append(f"- {display_name}")

    return "\\n".join(formatted_items) if formatted_items else "空"


# 格式化实体
def format_entities(entities):
    if not entities:
        return "无"

    formatted_entities = []
    # 假设实体信息包含 'name', 'type', 'distance', 'kind', 'isHostile'
    for entity in entities:
        name = entity.get('name', 'unknown_entity')
        etype = entity.get('type', 'unknown')
        distance = entity.get('distance', 0.0)
        kind = entity.get('kind', 'unknown')
        is_hostile = entity.get('isHostile') # Boolean

        # 根据 isHostile 添加标签
        hostility_tag = ""
        if is_hostile is True:
            hostility_tag = " (敌对)" # Hostile
        elif is_hostile is False:
            # 对于非敌对，可以不加标签或加 (非敌对)
             hostility_tag = " (非敌对)" # Non-hostile
        # 如果 is_hostile 是 null 或 undefined, 不加标签

        # 可以选择性地包含 kind 信息，如果它提供了有用的上下文
        # formatted_entities.append(f"- {name} ({etype}, {kind}{hostility_tag}): 距离 {distance:.1f} 格")
        formatted_entities.append(f"- {name} ({etype}{hostility_tag}): 距离 {distance:.1f} 格")

    return "\\n".join(formatted_entities) if formatted_entities else "无"

# 格式化方块
def format_blocks(blocks):
    if not blocks:
        return "无"

    # 合并相同类型的方块
    block_types = {}
    for block in blocks:
        # 假设方块信息只包含 'name'
        name = block.get('name', 'unknown_block')
        if name in block_types:
            block_types[name] += 1
        else:
            block_types[name] = 1

    return "\\n".join([f"- {name}: {count} 个" for name, count in block_types.items()]) if block_types else "无" 