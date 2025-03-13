// 合成物品
async function craftItem(bot, itemName, count = 1) {
    const mcData = require('minecraft-data')(bot.version);
    const item = mcData.itemsByName[itemName];
    
    if (!item) {
        throw new Error(`未知物品: ${itemName}`);
    }
    
    // 查找合成配方
    const recipes = bot.recipesFor(item.id, null, null, mcData.crafting_tables);
    
    if (recipes.length === 0) {
        throw new Error(`找不到 ${itemName} 的合成配方`);
    }
    
    // 选择第一个配方
    const recipe = recipes[0];
    
    // 检查是否需要工作台
    if (recipe.requiresTable) {
        // 寻找附近的工作台
        const craftingTable = bot.findBlock({
            matching: mcData.blocksByName.crafting_table.id,
            maxDistance: 32
        });
        
        if (!craftingTable) {
            throw new Error('需要工作台但找不到工作台');
        }
        
        // 移动到工作台附近
        await bot.pathfinder.goto(new bot.pathfinder.goals.GoalNear(
            craftingTable.position.x, 
            craftingTable.position.y, 
            craftingTable.position.z, 
            1
        ));
        
        // 在工作台上合成
        await bot.craft(recipe, count, craftingTable);
    } else {
        // 在物品栏中合成
        await bot.craft(recipe, count);
    }
}

module.exports = {
    craftItem
}; 