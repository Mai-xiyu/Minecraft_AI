const { goals: { GoalNear, GoalBlock } } = require('mineflayer-pathfinder');
const vec3 = require('vec3');
const Movements = require('mineflayer-pathfinder').Movements;

// 移动到指定位置
async function moveToPosition(bot, x, y, z) {
    const position = vec3(x, y, z);
    
    // 在这里初始化 Movements
    const mcData = require('minecraft-data')(bot.version);
    const movements = new Movements(bot, mcData);
    movements.canDig = true;
    movements.allow1by1towers = true;
    movements.allowFreeMotion = true;
    
    // 设置机器人的movements
    bot.pathfinder.setMovements(movements);
    
    // 计算目标位置的距离
    const currentPosition = bot.entity.position;
    const distance = currentPosition.distanceTo(position);
    
    // 设置超时时间，根据距离动态调整
    // 每格方块大约需要0.5秒，再加上10秒的基础时间
    const timeoutMs = Math.max(20000, distance * 500 + 10000);
    
    console.log(`移动到 (${x}, ${y}, ${z})，距离: ${distance.toFixed(2)}，超时: ${timeoutMs/1000}秒`);
    
    try {
        // 创建一个超时Promise
        const timeout = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('移动超时')), timeoutMs);
        });
        
        // 创建移动Promise
        const movement = new Promise(async (resolve) => {
            // 设置寻路目标
            const goal = new GoalNear(x, y, z, 1);
            await bot.pathfinder.goto(goal);
            resolve();
        });
        
        // 使用Promise.race来实现超时
        await Promise.race([movement, timeout]);
        
        return {
            success: true,
            message: `已移动到 (${x}, ${y}, ${z})附近`,
            position: bot.entity.position
        };
    } catch (err) {
        console.error('移动失败:', err.message);
        return {
            success: false,
            error: err.message,
            position: bot.entity.position
        };
    }
}

// 添加检查插件是否加载的函数
function ensurePluginsLoaded(bot) {
    // 检查pathfinder插件
    if (!bot.pathfinder) {
        throw new Error('pathfinder插件未加载');
    }
    
    // 检查collectBlock插件
    if (!bot.collectBlock) {
        // 尝试加载插件
        try {
            const collectBlock = require('mineflayer-collectblock').plugin;
            bot.loadPlugin(collectBlock);
            console.log('动态加载了collectBlock插件');
        } catch (e) {
            throw new Error('collectBlock插件未加载且无法动态加载: ' + e.message);
        }
    }
}

// 修改收集方法
async function collect(bot, action) {
    // 首先检查插件是否加载
    ensurePluginsLoaded(bot);
    
    const blockName = action.blockType;
    if (!blockName) {
        throw new Error('未指定要收集的方块类型');
    }
    
    const mcData = require('minecraft-data')(bot.version);
    const blockType = mcData.blocksByName[blockName];
    
    if (!blockType) {
        throw new Error(`未知的方块类型: ${blockName}`);
    }
    
    console.log(`搜索附近的 ${blockName}...`);
    
    // 查找范围
    const searchRadius = action.radius || 32;
    
    // 尝试查找指定方块
    const blockPosition = bot.findBlock({
        matching: blockType.id,
        maxDistance: searchRadius
    });
    
    if (!blockPosition) {
        return {
            success: false,
            error: `找不到附近的 ${blockName}`
        };
    }
    
    console.log(`找到 ${blockName} 位于 ${blockPosition.position.toString()}`);
    
    try {
        // 确保collectBlock可用
        if (!bot.collectBlock || typeof bot.collectBlock.collect !== 'function') {
            throw new Error('collectBlock插件未正确初始化');
        }
        
        // 收集方块
        await bot.collectBlock.collect(blockPosition);
        console.log(`成功收集了 ${blockName}`);
        
        return {
            success: true,
            message: `成功收集了 ${blockName}`
        };
    } catch (e) {
        console.error(`收集 ${blockName} 失败:`, e);
        return {
            success: false,
            error: `收集失败: ${e.message}`
        };
    }
}

// 放置方块
async function placeBlock(bot, itemName, x, y, z) {
    const position = vec3(x, y, z);
    
    // 先移动到附近
    await moveToPosition(bot, x, y, z);
    
    // 找到要放置的方块
    const mcData = require('minecraft-data')(bot.version);
    const item = mcData.itemsByName[itemName];
    
    if (!item) {
        throw new Error(`未知物品: ${itemName}`);
    }
    
    // 检查物品栏
    const itemInInventory = bot.inventory.findInventoryItem(item.id);
    if (!itemInInventory) {
        throw new Error(`物品栏中没有 ${itemName}`);
    }
    
    // 找到可以放置方块的位置
    const block = bot.blockAt(position);
    const referenceBlock = bot.blockAt(position.offset(0, -1, 0));
    
    if (!block || !referenceBlock) {
        throw new Error('无法找到放置位置');
    }
    
    // 装备物品
    await bot.equip(itemInInventory, 'hand');
    
    // 放置方块
    await bot.placeBlock(referenceBlock, vec3(0, 1, 0));
}

// 挖掘方块
async function digBlock(bot, x, y, z) {
    const position = vec3(x, y, z);
    const block = bot.blockAt(position);
    
    if (!block || block.name === 'air') {
        throw new Error('该位置没有方块');
    }
    
    // 移动到方块附近
    await moveToPosition(bot, x, y, z);
    
    // 选择合适的工具
    await bot.tool.equipForBlock(block);
    
    // 挖掘方块
    await bot.dig(block);
}

// 攻击实体
async function attackEntity(bot, entityName) {
    // 寻找最近的目标实体
    const entity = Object.values(bot.entities).find(e => 
        (e.name === entityName || e.username === entityName || e.displayName === entityName) && 
        e.position.distanceTo(bot.entity.position) < 32
    );
    
    if (!entity) {
        throw new Error(`找不到实体: ${entityName}`);
    }
    
    // 移动到实体附近
    const goal = new GoalNear(entity.position.x, entity.position.y, entity.position.z, 2);
    bot.pathfinder.setGoal(goal);
    
    // 等待接近
    await new Promise((resolve) => {
        const interval = setInterval(() => {
            if (bot.entity.position.distanceTo(entity.position) < 3) {
                clearInterval(interval);
                bot.pathfinder.setGoal(null);
                resolve();
            }
        }, 1000); // Reduced interval for faster check
    });
    
    // 攻击实体
    bot.lookAt(entity.position.offset(0, entity.height, 0));
    bot.attack(entity);
}

// --- 新增复合动作：跳跃攻击 ---
async function jumpAttack(bot, targetIdOrName) {
    console.log(`尝试跳跃攻击目标: ${targetIdOrName}`);
    // 查找目标实体 (通过ID或名称)
    const targetEntity = findEntityByIdOrName(bot, targetIdOrName);

    if (!targetEntity) {
        console.warn(`跳跃攻击失败: 找不到目标 ${targetIdOrName}`);
        return { success: false, error: `找不到目标实体: ${targetIdOrName}` };
    }

    const distance = bot.entity.position.distanceTo(targetEntity.position);
    console.log(`目标距离: ${distance.toFixed(2)}`);

    // 检查距离是否合适
    if (distance > 5) { // 如果太远，先移动过去
        console.log("目标太远，先移动靠近...");
        try {
            const goal = new GoalNear(targetEntity.position.x, targetEntity.position.y, targetEntity.position.z, 2);
            await bot.pathfinder.goto(goal);
            console.log("已移动到目标附近。");
        } catch (moveError) {
            console.error(`移动到目标 ${targetIdOrName} 失败:`, moveError);
            return { success: false, error: `移动到目标失败: ${moveError.message}` };
        }
    }

    // 执行跳跃攻击
    try {
        bot.lookAt(targetEntity.position.offset(0, targetEntity.height * 0.8, 0)); // 稍微向下看一点可能有助于命中
        bot.setControlState('jump', true); // 开始跳跃
        
        // 等待一小段时间让跳跃生效
        await bot.waitForTicks(2); // 2 ticks (约100ms) - 需要根据实际情况调整

        // 执行攻击
        bot.attack(targetEntity);
        console.log(`对 ${targetIdOrName} (ID: ${targetEntity.id}) 执行了攻击`);

        // 等待攻击动画完成或一小段时间
        await bot.waitForTicks(1);

        bot.setControlState('jump', false); // 结束跳跃
        console.log(`完成对 ${targetIdOrName} 的跳跃攻击`);
        return { success: true, message: `成功对 ${targetIdOrName} 执行了跳跃攻击` };

    } catch (attackError) {
        console.error(`跳跃攻击时发生错误:`, attackError);
        bot.setControlState('jump', false); // 确保跳跃状态被重置
        return { success: false, error: `跳跃攻击失败: ${attackError.message}` };
    }
}

// 辅助函数：通过ID或名称查找实体
function findEntityByIdOrName(bot, idOrName) {
    return Object.values(bot.entities).find(e => 
        e.id == idOrName || // 检查数字ID
        e.username === idOrName || // 检查玩家名称
        e.name === idOrName // 检查实体名称 (例如 'skeleton', 'zombie')
        // 可以根据需要添加 displayName 等
    );
}
// ---------------------------------

// 看向指定位置
async function lookAt(bot, x, y, z) {
    const position = vec3(x, y, z);
    await bot.lookAt(position);
}

// 确保所有函数正确导出
module.exports = {
    moveToPosition,
    collect,           // 确保这是正确名称
    placeBlock,
    digBlock,
    attackEntity,
    jumpAttack,        // 导出新增函数
    lookAt
}; 