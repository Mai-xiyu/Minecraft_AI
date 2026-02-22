const { goals: { GoalNear } } = require('mineflayer-pathfinder');
const vec3 = require('vec3');
const Movements = require('mineflayer-pathfinder').Movements;

// 缓存 mcData 和 movements 以避免每次调用都重新创建
let _cachedMcData = null;
let _cachedMovements = null;
let _cachedBotVersion = null;

function getMcData(bot) {
    if (_cachedMcData && _cachedBotVersion === bot.version) return _cachedMcData;
    _cachedMcData = require('minecraft-data')(bot.version);
    _cachedBotVersion = bot.version;
    _cachedMovements = null; // 版本变了要重建 movements
    return _cachedMcData;
}

function getMovements(bot) {
    const mcData = getMcData(bot);
    if (_cachedMovements) return _cachedMovements;
    _cachedMovements = new Movements(bot, mcData);
    _cachedMovements.canDig = true;
    _cachedMovements.allow1by1towers = true;
    _cachedMovements.allowFreeMotion = true;
    return _cachedMovements;
}

/**
 * 确保 pathfinder 和 collectBlock 插件已加载
 */
function ensurePluginsLoaded(bot) {
    if (!bot.pathfinder) {
        throw new Error('pathfinder 插件未加载');
    }
    if (!bot.collectBlock) {
        try {
            const collectBlock = require('mineflayer-collectblock').plugin;
            bot.loadPlugin(collectBlock);
        } catch (e) {
            throw new Error('collectBlock 插件未加载: ' + e.message);
        }
    }
}

/**
 * 移动到指定坐标
 */
async function moveToPosition(bot, x, y, z) {
    const position = vec3(x, y, z);
    const movements = getMovements(bot);
    bot.pathfinder.setMovements(movements);

    const currentPosition = bot.entity.position;
    const distance = currentPosition.distanceTo(position);
    const timeoutMs = Math.max(20000, distance * 500 + 10000);

    console.log(`[moveTo] (${x}, ${y}, ${z}), 距离: ${distance.toFixed(2)}, 超时: ${timeoutMs / 1000}s`);

    try {
        const timeout = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('移动超时')), timeoutMs)
        );
        const movement = (async () => {
            const goal = new GoalNear(x, y, z, 1);
            await bot.pathfinder.goto(goal);
        })();

        await Promise.race([movement, timeout]);
        return {
            success: true,
            message: `已移动到 (${x}, ${y}, ${z}) 附近`,
            position: bot.entity.position,
        };
    } catch (err) {
        return { success: false, error: err.message, position: bot.entity.position };
    }
}

/**
 * 收集指定方块
 */
async function collect(bot, action) {
    ensurePluginsLoaded(bot);

    const blockName = action.blockType;
    if (!blockName) {
        return { success: false, error: '未指定 blockType' };
    }

    const mcData = getMcData(bot);
    const blockType = mcData.blocksByName[blockName];
    if (!blockType) {
        return { success: false, error: `未知方块类型: ${blockName}` };
    }

    const searchRadius = action.radius || 32;
    const count = action.count || 1;
    let collected = 0;

    console.log(`[collect] ${blockName}, 半径=${searchRadius}, 数量=${count}`);

    try {
        for (let i = 0; i < count; i++) {
            const block = bot.findBlock({
                matching: blockType.id,
                maxDistance: searchRadius,
            });
            if (!block) {
                if (collected > 0) {
                    return { success: true, message: `收集了 ${collected}/${count} 个 ${blockName} (附近已无更多)` };
                }
                return { success: false, error: `找不到附近的 ${blockName}` };
            }

            await bot.collectBlock.collect(block);
            collected++;
        }

        return { success: true, message: `成功收集了 ${collected} 个 ${blockName}` };
    } catch (e) {
        return { success: false, error: `收集失败: ${e.message}`, collected };
    }
}

/**
 * 放置方块
 */
async function placeBlock(bot, itemName, x, y, z) {
    try {
        // 移动到目标位置旁边 (而非目标位置本身, 否则机器人会挡住放置)
        await moveToPosition(bot, x + 1, y, z);

        const mcData = getMcData(bot);
        const item = mcData.itemsByName[itemName];
        if (!item) {
            return { success: false, error: `未知物品: ${itemName}` };
        }

        const itemInInventory = bot.inventory.findInventoryItem(item.id);
        if (!itemInInventory) {
            return { success: false, error: `物品栏中没有 ${itemName}` };
        }

        const position = vec3(x, y, z);
        const referenceBlock = bot.blockAt(position.offset(0, -1, 0));
        if (!referenceBlock) {
            return { success: false, error: '无法找到放置参考方块' };
        }

        await bot.equip(itemInInventory, 'hand');
        await bot.placeBlock(referenceBlock, vec3(0, 1, 0));

        return { success: true, message: `已在 (${x}, ${y}, ${z}) 放置 ${itemName}` };
    } catch (e) {
        return { success: false, error: `放置失败: ${e.message}` };
    }
}

/**
 * 挖掘方块
 */
async function digBlock(bot, x, y, z) {
    try {
        const position = vec3(x, y, z);
        const block = bot.blockAt(position);
        if (!block || block.name === 'air') {
            return { success: false, error: '该位置没有方块' };
        }

        await moveToPosition(bot, x, y, z);
        await bot.tool.equipForBlock(block);
        await bot.dig(block);

        return { success: true, message: `已挖掘 (${x}, ${y}, ${z}) 的 ${block.name}` };
    } catch (e) {
        return { success: false, error: `挖掘失败: ${e.message}` };
    }
}

/**
 * 通过 ID 或名称查找实体
 */
function findEntityByIdOrName(bot, idOrName) {
    return Object.values(bot.entities).find(
        (e) =>
            e.id == idOrName ||
            e.username === idOrName ||
            e.name === idOrName ||
            e.displayName === idOrName
    );
}

/**
 * 攻击实体
 */
async function attackEntity(bot, target) {
    const entity = findEntityByIdOrName(bot, target);
    if (!entity) {
        return { success: false, error: `找不到实体: ${target}` };
    }

    try {
        const distance = bot.entity.position.distanceTo(entity.position);
        if (distance > 4) {
            const goal = new GoalNear(entity.position.x, entity.position.y, entity.position.z, 2);
            await bot.pathfinder.goto(goal);
        }

        await bot.lookAt(entity.position.offset(0, entity.height, 0));
        await bot.attack(entity);

        return { success: true, message: `已攻击 ${target}` };
    } catch (e) {
        return { success: false, error: `攻击失败: ${e.message}` };
    }
}

/**
 * 跳跃攻击
 */
async function jumpAttack(bot, target) {
    const entity = findEntityByIdOrName(bot, target);
    if (!entity) {
        return { success: false, error: `找不到目标实体: ${target}` };
    }

    try {
        const distance = bot.entity.position.distanceTo(entity.position);
        if (distance > 5) {
            const goal = new GoalNear(entity.position.x, entity.position.y, entity.position.z, 2);
            await bot.pathfinder.goto(goal);
        }

        await bot.lookAt(entity.position.offset(0, entity.height * 0.8, 0));
        bot.setControlState('jump', true);
        await bot.waitForTicks(2);
        await bot.attack(entity);
        await bot.waitForTicks(1);
        bot.setControlState('jump', false);

        return { success: true, message: `成功对 ${target} 执行了跳跃攻击` };
    } catch (e) {
        bot.setControlState('jump', false);
        return { success: false, error: `跳跃攻击失败: ${e.message}` };
    }
}

/**
 * 看向指定坐标
 */
async function lookAt(bot, x, y, z) {
    try {
        const pos = vec3(x, y, z);
        await bot.lookAt(pos);
        return { success: true, message: `已看向 (${x}, ${y}, ${z})` };
    } catch (e) {
        return { success: false, error: `看向失败: ${e.message}` };
    }
}

/**
 * 吃食物
 * @param {object} bot
 * @param {string|null} itemName - 指定食物名, 为空则自动选择
 */
async function eat(bot, itemName) {
    const mcData = getMcData(bot);
    let foodItem = null;

    if (itemName) {
        const itemType = mcData.itemsByName[itemName];
        if (!itemType) return { success: false, error: `未知物品: ${itemName}` };
        foodItem = bot.inventory.findInventoryItem(itemType.id);
        if (!foodItem) return { success: false, error: `物品栏中没有 ${itemName}` };
    } else {
        // 自动选择食物 (foodPoints > 0 的物品)
        const foodNames = Object.values(mcData.foods || {}).map(f => f.name);
        for (const item of bot.inventory.items()) {
            if (foodNames.includes(item.name)) {
                foodItem = item;
                break;
            }
        }
        // 备用: 按名称模糊查找常见食物
        if (!foodItem) {
            const commonFoods = ['cooked_beef', 'cooked_porkchop', 'bread', 'cooked_chicken',
                'cooked_mutton', 'cooked_salmon', 'cooked_cod', 'baked_potato', 'golden_apple',
                'apple', 'carrot', 'melon_slice', 'sweet_berries', 'cookie', 'cake'];
            for (const name of commonFoods) {
                const type = mcData.itemsByName[name];
                if (type) {
                    const found = bot.inventory.findInventoryItem(type.id);
                    if (found) { foodItem = found; break; }
                }
            }
        }
        if (!foodItem) return { success: false, error: '物品栏中没有可食用的食物' };
    }

    try {
        await bot.equip(foodItem, 'hand');
        bot.activateItem();
        await bot.waitForTicks(30); // ~1.5 秒等待进食
        bot.deactivateItem();
        return { success: true, message: `已食用 ${foodItem.name}`, food: bot.food };
    } catch (e) {
        return { success: false, error: `进食失败: ${e.message}` };
    }
}

/**
 * 钓鱼
 * @param {object} bot
 * @param {number} duration - 最长等待 ticks (默认 600 = ~30秒)
 */
async function fish(bot, duration) {
    const mcData = getMcData(bot);
    const rodType = mcData.itemsByName['fishing_rod'];
    if (!rodType) return { success: false, error: '版本不支持钓鱼' };

    const rod = bot.inventory.findInventoryItem(rodType.id);
    if (!rod) return { success: false, error: '物品栏中没有钓鱼竿' };

    try {
        await bot.equip(rod, 'hand');
        bot.activateItem(); // 抛竿

        const maxTicks = duration || 600;
        const collected = await new Promise((resolve) => {
            let done = false;
            const onCollect = (collector, collected) => {
                if (collector === bot.entity) {
                    done = true;
                    resolve({ caught: true, item: collected?.name || 'unknown' });
                }
            };
            bot.on('playerCollect', onCollect);
            // 超时
            setTimeout(() => {
                if (!done) {
                    bot.removeListener('playerCollect', onCollect);
                    resolve({ caught: false });
                }
            }, maxTicks * 50);
        });

        bot.activateItem(); // 收竿
        if (collected.caught) {
            return { success: true, message: `钓到了 ${collected.item}` };
        }
        return { success: true, message: '钓鱼超时, 未钓到东西' };
    } catch (e) {
        return { success: false, error: `钓鱼失败: ${e.message}` };
    }
}

/**
 * 熔炼物品
 */
async function smelt(bot, itemName, fuelName, count) {
    const mcData = getMcData(bot);

    // 1. 寻找熔炉
    const furnaceBlock = bot.findBlock({
        matching: mcData.blocksByName['furnace']?.id,
        maxDistance: 32,
    });
    if (!furnaceBlock) return { success: false, error: '附近没有找到熔炉' };

    // 2. 走到熔炉旁
    const fb = furnaceBlock.position;
    await moveToPosition(bot, fb.x, fb.y, fb.z);

    // 3. 打开熔炉
    try {
        const furnace = await bot.openFurnace(furnaceBlock);

        // 放入物品
        const inputItem = mcData.itemsByName[itemName];
        if (!inputItem) { furnace.close(); return { success: false, error: `未知物品: ${itemName}` }; }
        const invItem = bot.inventory.findInventoryItem(inputItem.id);
        if (!invItem) { furnace.close(); return { success: false, error: `物品栏中没有 ${itemName}` }; }

        await furnace.putInput(invItem.type, null, count || 1);

        // 放入燃料 (如果指定或熔炉没有燃料)
        if (fuelName || !furnace.fuelItem()) {
            const fname = fuelName || 'coal';
            const fuelType = mcData.itemsByName[fname];
            if (fuelType) {
                const fuelInv = bot.inventory.findInventoryItem(fuelType.id);
                if (fuelInv) {
                    await furnace.putFuel(fuelInv.type, null, 1);
                }
            }
        }

        // 等待熔炼 (最多30秒)
        await new Promise(r => setTimeout(r, 12000));

        // 尝试取出
        const output = furnace.outputItem();
        if (output) {
            await furnace.takeOutput();
        }
        furnace.close();

        return { success: true, message: `已将 ${itemName} 放入熔炉熔炼` };
    } catch (e) {
        return { success: false, error: `熔炼失败: ${e.message}` };
    }
}

/**
 * 打开箱子并存入/取出物品
 * @param {string} action - 'deposit' 或 'withdraw'
 */
async function openChest(bot, x, y, z, chestAction, itemName, count) {
    const mcData = getMcData(bot);
    const pos = vec3(x, y, z);

    // 走到箱子旁
    await moveToPosition(bot, x, y, z);

    const block = bot.blockAt(pos);
    if (!block) return { success: false, error: '该位置没有方块' };

    try {
        const chest = await bot.openContainer(block);

        if (chestAction === 'deposit') {
            const itemType = mcData.itemsByName[itemName];
            if (!itemType) { chest.close(); return { success: false, error: `未知物品: ${itemName}` }; }
            const invItem = bot.inventory.findInventoryItem(itemType.id);
            if (!invItem) { chest.close(); return { success: false, error: `物品栏中没有 ${itemName}` }; }
            await chest.deposit(invItem.type, null, count || invItem.count);
            chest.close();
            return { success: true, message: `已将 ${count || invItem.count} 个 ${itemName} 存入箱子` };
        } else if (chestAction === 'withdraw') {
            const itemType = mcData.itemsByName[itemName];
            if (!itemType) { chest.close(); return { success: false, error: `未知物品: ${itemName}` }; }
            await chest.withdraw(itemType.id, null, count || 1);
            chest.close();
            return { success: true, message: `已从箱子取出 ${count || 1} 个 ${itemName}` };
        } else {
            // 只是查看箱子内容
            const items = chest.containerItems().map(i => ({ name: i.name, count: i.count }));
            chest.close();
            return { success: true, message: `箱子内容: ${JSON.stringify(items)}`, items };
        }
    } catch (e) {
        return { success: false, error: `箱子操作失败: ${e.message}` };
    }
}

/**
 * 在床上睡觉
 */
async function sleep(bot) {
    const mcData = getMcData(bot);

    // 搜索附近的床 (所有颜色)
    const bedNames = Object.keys(mcData.blocksByName).filter(n => n.endsWith('_bed'));
    const bedIds = bedNames.map(n => mcData.blocksByName[n]?.id).filter(Boolean);

    const bedBlock = bot.findBlock({
        matching: bedIds,
        maxDistance: 32,
    });
    if (!bedBlock) return { success: false, error: '附近没有找到床' };

    // 走到床旁
    const bp = bedBlock.position;
    await moveToPosition(bot, bp.x, bp.y, bp.z);

    try {
        await bot.sleep(bedBlock);
        // 等待一段时间 (等天亮或被打断)
        await new Promise((resolve) => {
            bot.once('wake', resolve);
            setTimeout(resolve, 15000);
        });
        return { success: true, message: '已睡觉并醒来' };
    } catch (e) {
        return { success: false, error: `睡觉失败: ${e.message} (可能不是夜晚或附近有怪物)` };
    }
}

/**
 * 跟随玩家
 */
async function followPlayer(bot, playerName, distance) {
    const { GoalFollow } = require('mineflayer-pathfinder').goals;

    const target = bot.players[playerName];
    if (!target || !target.entity) {
        return { success: false, error: `找不到玩家: ${playerName}` };
    }

    const followDist = distance || 3;
    const movements = getMovements(bot);
    bot.pathfinder.setMovements(movements);

    try {
        const goal = new GoalFollow(target.entity, followDist);
        bot.pathfinder.setGoal(goal, true); // dynamic=true 持续跟随

        // 跟随一段时间 (20 秒)
        await new Promise(r => setTimeout(r, 20000));
        bot.pathfinder.setGoal(null); // 停止跟随
        return { success: true, message: `已跟随 ${playerName} 一段时间` };
    } catch (e) {
        bot.pathfinder.setGoal(null);
        return { success: false, error: `跟随失败: ${e.message}` };
    }
}

/**
 * 探索周围环境: 随机移动并收集发现信息
 */
async function explore(bot, radius) {
    const exploreRadius = radius || 50;
    const pos = bot.entity.position;

    // 随机选择方向
    const angle = Math.random() * 2 * Math.PI;
    const dist = 10 + Math.random() * (exploreRadius - 10);
    const targetX = Math.floor(pos.x + Math.cos(angle) * dist);
    const targetZ = Math.floor(pos.z + Math.sin(angle) * dist);

    // 先尝试获取目标 Y 坐标 (取当前高度)
    const targetY = Math.floor(pos.y);

    console.log(`[explore] 探索方向 (${targetX}, ${targetY}, ${targetZ}), 半径=${exploreRadius}`);

    try {
        await moveToPosition(bot, targetX, targetY, targetZ);
    } catch (e) {
        // 移动失败也没关系, 可能到了一半
    }

    // 扫描新位置附近的有趣方块
    const mcData = getMcData(bot);
    const interestingBlocks = [];
    const interesting = new Set([
        'diamond_ore', 'deepslate_diamond_ore', 'gold_ore', 'deepslate_gold_ore',
        'iron_ore', 'deepslate_iron_ore', 'coal_ore', 'deepslate_coal_ore',
        'lapis_ore', 'deepslate_lapis_ore', 'redstone_ore', 'deepslate_redstone_ore',
        'emerald_ore', 'deepslate_emerald_ore', 'copper_ore', 'deepslate_copper_ore',
        'chest', 'spawner', 'crafting_table', 'furnace', 'anvil',
        'enchanting_table', 'brewing_stand', 'village_bell',
    ]);

    const scanRadius = 8;
    const cp = bot.entity.position;
    for (let dx = -scanRadius; dx <= scanRadius; dx++) {
        for (let dy = -scanRadius; dy <= scanRadius; dy++) {
            for (let dz = -scanRadius; dz <= scanRadius; dz++) {
                try {
                    const block = bot.blockAt(vec3(
                        Math.floor(cp.x) + dx,
                        Math.floor(cp.y) + dy,
                        Math.floor(cp.z) + dz
                    ));
                    if (block && interesting.has(block.name)) {
                        interestingBlocks.push({
                            name: block.name,
                            position: { x: block.position.x, y: block.position.y, z: block.position.z },
                        });
                    }
                } catch { /* ignore */ }
            }
        }
    }

    // 附近实体
    const nearbyEntities = [];
    for (const id in bot.entities) {
        const e = bot.entities[id];
        if (e === bot.entity) continue;
        const d = bot.entity.position.distanceTo(e.position);
        if (d <= 16) {
            nearbyEntities.push({
                name: e.name || e.username || 'unknown',
                type: e.type,
                distance: d.toFixed(1),
            });
        }
    }

    return {
        success: true,
        message: `探索完成。发现 ${interestingBlocks.length} 个有价值方块, ${nearbyEntities.length} 个实体`,
        position: { x: bot.entity.position.x, y: bot.entity.position.y, z: bot.entity.position.z },
        interestingBlocks: interestingBlocks.slice(0, 20),
        nearbyEntities: nearbyEntities.slice(0, 10),
    };
}

module.exports = {
    moveToPosition,
    collect,
    placeBlock,
    digBlock,
    attackEntity,
    jumpAttack,
    lookAt,
    eat,
    fish,
    smelt,
    openChest,
    sleep,
    followPlayer,
    explore,
    queryRecipe,
    queryBlockInfo,
    searchBlocks,
    queryItemInfo,
};

// ── 知识查询动作 (不消耗游戏操作, 只返回信息) ──────────

/**
 * 查询物品合成配方
 * @param {object} bot
 * @param {string} itemName - 物品名称
 * @returns {Promise<{success: boolean, message: string}>}
 */
async function queryRecipe(bot, itemName) {
    const mcData = getMcData(bot);
    const item = mcData.itemsByName[itemName];
    if (!item) {
        return { success: false, error: `未知物品: ${itemName}` };
    }

    // 获取所有配方 (不管物品栏有没有材料)
    const allRecipes = bot.recipesAll(item.id, null, null);
    // 获取当前可用配方 (物品栏满足)
    const availableRecipes = bot.recipesFor(item.id, null, null, null);
    // 需要工作台的配方
    const tableRecipes = bot.recipesAll(item.id, null, true);

    if (allRecipes.length === 0 && tableRecipes.length === 0) {
        // 尝试从 mcData.recipes 查找
        const rawRecipes = mcData.recipes?.[item.id] || [];
        if (rawRecipes.length === 0) {
            return { success: true, message: `${itemName} 没有合成配方 (可能需要通过挖掘、交易或熔炼获取)` };
        }
    }

    const lines = [`## ${itemName} 的合成配方\n`];

    // 解析配方详情
    const recipes = [...allRecipes, ...tableRecipes];
    const seen = new Set();
    for (const recipe of recipes) {
        const key = JSON.stringify(recipe.ingredients || recipe.inShape || recipe.delta);
        if (seen.has(key)) continue;
        seen.add(key);

        const needsTable = recipe.requiresTable ? '需要工作台' : '手工合成';
        lines.push(`### 配方 (${needsTable})`);

        // 获取原料
        if (recipe.delta) {
            const inputs = recipe.delta.filter(d => d.count < 0);
            const outputs = recipe.delta.filter(d => d.count > 0);
            if (inputs.length > 0) {
                lines.push('所需材料:');
                for (const inp of inputs) {
                    const inItem = mcData.items[inp.id];
                    const name = inItem ? inItem.name : `id:${inp.id}`;
                    lines.push(`  - ${name} x${Math.abs(inp.count)}`);
                }
            }
            if (outputs.length > 0) {
                for (const out of outputs) {
                    const outItem = mcData.items[out.id];
                    const name = outItem ? outItem.name : `id:${out.id}`;
                    lines.push(`产出: ${name} x${out.count}`);
                }
            }
        }
    }

    // 当前物品栏可合成情况
    if (availableRecipes.length > 0) {
        lines.push(`\n✅ 当前物品栏可以直接合成 ${itemName}`);
    } else {
        lines.push(`\n❌ 当前物品栏材料不足以合成 ${itemName}`);

        // 列出缺少的材料
        if (recipes.length > 0 && recipes[0].delta) {
            const inputs = recipes[0].delta.filter(d => d.count < 0);
            lines.push('缺少的材料:');
            for (const inp of inputs) {
                const inItem = mcData.items[inp.id];
                const name = inItem ? inItem.name : `id:${inp.id}`;
                const needed = Math.abs(inp.count);
                // 检查物品栏有多少
                const invCount = bot.inventory.items()
                    .filter(i => i.type === inp.id)
                    .reduce((sum, i) => sum + i.count, 0);
                if (invCount < needed) {
                    lines.push(`  - ${name}: 需要 ${needed}, 拥有 ${invCount}, 还缺 ${needed - invCount}`);
                }
            }
        }
    }

    return { success: true, message: lines.join('\n') };
}

/**
 * 查询方块信息 (硬度、工具、掉落物)
 * @param {object} bot
 * @param {string} blockName
 */
async function queryBlockInfo(bot, blockName) {
    const mcData = getMcData(bot);
    const block = mcData.blocksByName[blockName];
    if (!block) {
        return { success: false, error: `未知方块: ${blockName}` };
    }

    const lines = [`## ${blockName} 方块信息\n`];
    lines.push(`- ID: ${block.id}`);
    lines.push(`- 硬度: ${block.hardness ?? '不可破坏'}`);
    lines.push(`- 爆炸抗性: ${block.resistance ?? '未知'}`);
    lines.push(`- 是否透明: ${block.transparent ? '是' : '否'}`);

    // 需要的工具
    if (block.material) {
        lines.push(`- 材质类型: ${block.material}`);
    }
    if (block.harvestTools) {
        const tools = Object.keys(block.harvestTools).map(id => {
            const tool = mcData.items[parseInt(id)];
            return tool ? tool.name : `id:${id}`;
        });
        lines.push(`- 需要工具: ${tools.join(', ')}`);
    } else if (block.hardness !== null && block.hardness >= 0) {
        lines.push(`- 需要工具: 任何工具/徒手`);
    }

    // 掉落物
    try {
        const loot = mcData.blockLoot?.[blockName];
        if (loot && loot.drops) {
            lines.push(`\n### 掉落物:`);
            for (const drop of loot.drops) {
                const dropItem = mcData.items[drop.id] || mcData.items[drop.item];
                const name = dropItem ? dropItem.name : (drop.name || '未知');
                lines.push(`  - ${name}`);
            }
        }
    } catch { /* blockLoot may not exist */ }

    // 附近搜索
    const found = bot.findBlock({
        matching: block.id,
        maxDistance: 64,
    });
    if (found) {
        const dist = bot.entity.position.distanceTo(found.position).toFixed(1);
        lines.push(`\n📍 最近的 ${blockName} 在 (${found.position.x}, ${found.position.y}, ${found.position.z}), 距离 ${dist} 格`);
    } else {
        lines.push(`\n📍 64 格内未找到 ${blockName}`);
    }

    return { success: true, message: lines.join('\n') };
}

/**
 * 大范围搜索方块
 * @param {object} bot
 * @param {string} blockName
 * @param {number} maxDistance - 搜索半径 (默认64)
 */
async function searchBlocks(bot, blockName, maxDistance) {
    const mcData = getMcData(bot);
    const block = mcData.blocksByName[blockName];
    if (!block) {
        return { success: false, error: `未知方块: ${blockName}` };
    }

    const radius = maxDistance || 64;
    const positions = bot.findBlocks({
        matching: block.id,
        maxDistance: radius,
        count: 10,
    });

    if (!positions || positions.length === 0) {
        return { success: true, message: `在 ${radius} 格范围内未找到 ${blockName}` };
    }

    const lines = [`## 搜索结果: ${blockName} (${radius}格范围内)\n`];
    lines.push(`找到 ${positions.length} 个:\n`);

    for (const pos of positions.slice(0, 8)) {
        const dist = bot.entity.position.distanceTo(pos).toFixed(1);
        lines.push(`- (${pos.x}, ${pos.y}, ${pos.z}) 距离: ${dist}格`);
    }

    // 推荐最近的
    if (positions.length > 0) {
        const nearest = positions[0];
        lines.push(`\n💡 最近的在 (${nearest.x}, ${nearest.y}, ${nearest.z})`);
        lines.push(`建议: 使用 moveTo 前往或 collect 直接采集`);
    }

    return { success: true, message: lines.join('\n') };
}

/**
 * 查询物品信息 (可合成、可食用、获取途径)
 * @param {object} bot
 * @param {string} itemName
 */
async function queryItemInfo(bot, itemName) {
    const mcData = getMcData(bot);
    const item = mcData.itemsByName[itemName];
    if (!item) {
        return { success: false, error: `未知物品: ${itemName}` };
    }

    const lines = [`## ${itemName} 物品信息\n`];
    lines.push(`- ID: ${item.id}`);
    lines.push(`- 最大堆叠: ${item.stackSize}`);

    // 是否食物
    const food = Object.values(mcData.foods || {}).find(f => f.id === item.id || f.name === itemName);
    if (food) {
        lines.push(`- 🍖 可食用: 恢复 ${food.foodPoints || '?'} 饥饿值, ${food.saturation || '?'} 饱和度`);
    }

    // 物品栏中有多少
    const invCount = bot.inventory.items()
        .filter(i => i.type === item.id)
        .reduce((sum, i) => sum + i.count, 0);
    lines.push(`- 物品栏中拥有: ${invCount}`);

    // 合成配方
    const recipes = bot.recipesAll(item.id, null, null);
    const tableRecipes = bot.recipesAll(item.id, null, true);
    if (recipes.length > 0 || tableRecipes.length > 0) {
        lines.push(`- ✅ 可合成 (共 ${recipes.length + tableRecipes.length} 个配方)`);
        lines.push(`  使用 queryRecipe 查看详细配方`);
    } else {
        lines.push(`- ❌ 不可合成`);
    }

    // 获取途径提示
    lines.push(`\n### 获取途径:`);

    // 检查是否有对应方块可挖掘
    const blockEquiv = mcData.blocksByName[itemName];
    if (blockEquiv) {
        lines.push(`- 挖掘 ${itemName} 方块`);
        const found = bot.findBlock({ matching: blockEquiv.id, maxDistance: 64 });
        if (found) {
            lines.push(`  (最近在 ${found.position.x}, ${found.position.y}, ${found.position.z})`);
        }
    }

    // 熔炼来源 (常见的映射)
    const smeltSources = {
        'iron_ingot': 'raw_iron 或 iron_ore',
        'gold_ingot': 'raw_gold 或 gold_ore',
        'copper_ingot': 'raw_copper 或 copper_ore',
        'glass': 'sand',
        'stone': 'cobblestone',
        'smooth_stone': 'stone',
        'brick': 'clay_ball',
        'charcoal': 'oak_log (任意原木)',
        'cooked_beef': 'beef',
        'cooked_porkchop': 'porkchop',
        'cooked_chicken': 'chicken',
        'cooked_mutton': 'mutton',
        'cooked_salmon': 'salmon',
        'cooked_cod': 'cod',
        'baked_potato': 'potato',
    };
    if (smeltSources[itemName]) {
        lines.push(`- 熔炼: ${smeltSources[itemName]}`);
    }

    if (recipes.length > 0 || tableRecipes.length > 0) {
        lines.push(`- 合成: 使用 queryRecipe 查看详情`);
    }

    return { success: true, message: lines.join('\n') };
}
