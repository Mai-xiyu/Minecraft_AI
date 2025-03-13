// 获取物品栏中的所有物品
function getInventoryItems(bot) {
    const items = [];
    
    if (!bot.inventory) return items;
    
    // 主物品栏
    for (const item of bot.inventory.items()) {
        if (item) {
            items.push({
                name: item.name,
                count: item.count,
                slot: item.slot
            });
        }
    }
    
    return items;
}

// 装备物品
async function equipItem(bot, itemName) {
    const item = bot.inventory.findInventoryItem(itemName);
    
    if (!item) {
        throw new Error(`物品栏中没有 ${itemName}`);
    }
    
    await bot.equip(item, 'hand');
}

// 丢弃物品
async function dropItem(bot, itemName, count = 1) {
    const item = bot.inventory.findInventoryItem(itemName);
    
    if (!item) {
        throw new Error(`物品栏中没有 ${itemName}`);
    }
    
    await bot.toss(item.type, null, Math.min(count, item.count));
}

module.exports = {
    getInventoryItems,
    equipItem,
    dropItem
}; 