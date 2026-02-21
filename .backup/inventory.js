// 获取物品栏中的所有物品
function getInventoryItems(bot) {
    const items = [];
    
    if (!bot.inventory) return items;
    
    // 主物品栏
    for (const item of bot.inventory.items()) {
        if (item) {
            const itemData = {
                name: item.name,
                count: item.count,
                slot: item.slot,
                // 添加耐久度信息 (如果适用)
                durability: null // Default to null
            };

            // 检查是否有最大耐久度信息且大于0 (表明是可损坏物品)
            if (item.maxDurability !== undefined && item.maxDurability > 0) {
                // Mineflayer 的 item 对象通常有 durabilityUsed 属性
                // 如果没有，则假定为0 (全新)
                const durabilityUsed = item.durabilityUsed === undefined ? 0 : item.durabilityUsed;
                const remainingDurability = item.maxDurability - durabilityUsed;
                itemData.durability = {
                    current: remainingDurability,
                    max: item.maxDurability
                };
            }

            items.push(itemData);
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