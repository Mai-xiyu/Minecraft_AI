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
    
    bot.pathfinder.setMovements(movements);
    const goal = new GoalNear(x, y, z, 1); // 移动到距离目标1格内
    
    return new Promise((resolve, reject) => {
        bot.pathfinder.setGoal(goal);
        
        // 设置超时
        const timeout = setTimeout(() => {
            bot.pathfinder.setGoal(null);
            reject(new Error('移动超时'));
        }, 30000); // 30秒超时
        
        // 检查是否到达
        const checkInterval = setInterval(() => {
            if (bot.entity.position.distanceTo(position) < 2) {
                clearInterval(checkInterval);
                clearTimeout(timeout);
                bot.pathfinder.setGoal(null);
                resolve();
            }
        }, 1000);
        
        // 处理路径错误
        bot.pathfinder.once('goal_failed', () => {
            clearInterval(checkInterval);
            clearTimeout(timeout);
            reject(new Error('无法找到路径'));
        });
    });
}

// 收集指定类型的方块
async function collectBlock(bot, blockType, count = 1) {
    const mcData = require('minecraft-data')(bot.version);
    const blockId = mcData.blocksByName[blockType]?.id;
    
    if (!blockId) {
        throw new Error(`未知方块类型: ${blockType}`);
    }
    
    let collected = 0;
    while (collected < count) {
        // 寻找最近的目标方块
        const block = bot.findBlock({
            matching: blockId,
            maxDistance: 32
        });
        
        if (!block) {
            throw new Error(`找不到更多的 ${blockType}`);
        }
        
        try {
            await bot.collectBlock.collect(block);
            collected++;
            console.log(`已收集 ${collected}/${count} 个 ${blockType}`);
        } catch (err) {
            throw new Error(`收集 ${blockType} 失败: ${err.message}`);
        }
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
        }, 1000);
    });
    
    // 攻击实体
    bot.lookAt(entity.position.offset(0, entity.height, 0));
    bot.attack(entity);
}

// 看向指定位置
async function lookAt(bot, x, y, z) {
    const position = vec3(x, y, z);
    await bot.lookAt(position);
}

module.exports = {
    moveToPosition,
    collectBlock,
    placeBlock,
    digBlock,
    attackEntity,
    lookAt
}; 