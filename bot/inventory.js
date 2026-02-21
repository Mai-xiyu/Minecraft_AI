/**
 * 获取物品栏中的所有物品
 */
function getInventoryItems(bot) {
    const items = [];
    if (!bot.inventory) return items;

    for (const item of bot.inventory.items()) {
        if (item) {
            const itemData = {
                name: item.name,
                count: item.count,
                slot: item.slot,
                durability: null,
            };

            if (item.maxDurability !== undefined && item.maxDurability > 0) {
                const durabilityUsed = item.durabilityUsed === undefined ? 0 : item.durabilityUsed;
                const remainingDurability = item.maxDurability - durabilityUsed;
                itemData.durability = {
                    current: remainingDurability,
                    max: item.maxDurability,
                };
            }

            items.push(itemData);
        }
    }
    return items;
}

/**
 * 装备物品
 * @param {object} bot
 * @param {string} itemName
 * @param {string} destination - 'hand', 'off-hand', 'head', 'torso', 'legs', 'feet'
 * @returns {Promise<{success: boolean, message?: string, error?: string}>}
 */
async function equipItem(bot, itemName, destination = 'hand') {
    const item = bot.inventory.findInventoryItem(itemName);
    if (!item) {
        return { success: false, error: `物品栏中没有 ${itemName}` };
    }

    try {
        await bot.equip(item, destination);
        return { success: true, message: `已装备 ${itemName} 到 ${destination}` };
    } catch (e) {
        return { success: false, error: `装备失败: ${e.message}` };
    }
}

/**
 * 卸下装备
 * @param {object} bot
 * @param {string} destination - 卸下哪个位置的装备
 * @returns {Promise<{success: boolean, message?: string, error?: string}>}
 */
async function unequipItem(bot, destination = 'hand') {
    try {
        await bot.unequip(destination);
        return { success: true, message: `已卸下 ${destination} 的装备` };
    } catch (e) {
        return { success: false, error: `卸下装备失败: ${e.message}` };
    }
}

/**
 * 丢弃物品
 * @param {object} bot
 * @param {string} itemName
 * @param {number} count
 * @returns {Promise<{success: boolean, message?: string, error?: string}>}
 */
async function dropItem(bot, itemName, count = 1) {
    const item = bot.inventory.findInventoryItem(itemName);
    if (!item) {
        return { success: false, error: `物品栏中没有 ${itemName}` };
    }

    try {
        await bot.toss(item.type, null, Math.min(count, item.count));
        return { success: true, message: `已丢弃 ${count} 个 ${itemName}` };
    } catch (e) {
        return { success: false, error: `丢弃失败: ${e.message}` };
    }
}

module.exports = {
    getInventoryItems,
    equipItem,
    unequipItem,
    dropItem,
};
