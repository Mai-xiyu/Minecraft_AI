const { goals: { GoalNear } } = require('mineflayer-pathfinder');

/**
 * 合成物品
 * @param {object} bot
 * @param {string} itemName - 物品名称
 * @param {number} count - 数量 (默认 1)
 * @returns {Promise<{success: boolean, message?: string, error?: string}>}
 */
async function craftItem(bot, itemName, count = 1) {
    const mcData = require('minecraft-data')(bot.version);
    const item = mcData.itemsByName[itemName];

    if (!item) {
        return { success: false, error: `未知物品: ${itemName}` };
    }

    // 查找合成配方
    const recipes = bot.recipesFor(item.id, null, null, null);

    if (recipes.length === 0) {
        return { success: false, error: `找不到 ${itemName} 的合成配方` };
    }

    const recipe = recipes[0];

    try {
        if (recipe.requiresTable) {
            // 寻找附近的工作台
            const craftingTable = bot.findBlock({
                matching: mcData.blocksByName.crafting_table.id,
                maxDistance: 32,
            });

            if (!craftingTable) {
                return { success: false, error: '需要工作台但找不到附近的工作台' };
            }

            // 移动到工作台附近
            const goal = new GoalNear(
                craftingTable.position.x,
                craftingTable.position.y,
                craftingTable.position.z,
                1
            );
            await bot.pathfinder.goto(goal);

            // 在工作台上合成
            await bot.craft(recipe, count, craftingTable);
        } else {
            await bot.craft(recipe, count);
        }

        return { success: true, message: `成功合成了 ${count} 个 ${itemName}` };
    } catch (e) {
        return { success: false, error: `合成失败: ${e.message}` };
    }
}

module.exports = { craftItem };
