const mineflayer = require('mineflayer');
const { pathfinder, Movements } = require('mineflayer-pathfinder');
const collectBlock = require('mineflayer-collectblock').plugin;
const toolPlugin = require('mineflayer-tool').plugin;
const express = require('express');
const bodyParser = require('body-parser');
const { Vec3 } = require('vec3');
const fs = require('fs');
const path = require('path');

const actions = require('./actions');
const inventory = require('./inventory');
const crafting = require('./crafting');

process.stdout.setEncoding('utf8');
process.stderr.setEncoding('utf8');

// ─── Express 服务器 ──────────────────────────────────────
const app = express();
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// ─── 配置加载 ────────────────────────────────────────────
function getConfigPath() {
    const paths = [
        path.join(__dirname, '..', 'config.json'),
        path.join(process.cwd(), 'config.json'),
    ];
    for (const p of paths) {
        if (fs.existsSync(p)) return p;
    }
    throw new Error('找不到配置文件');
}

function loadConfig() {
    try {
        const configPath = getConfigPath();
        return JSON.parse(fs.readFileSync(configPath, 'utf8'));
    } catch (err) {
        console.error('读取配置文件失败:', err.message);
        return {
            minecraft: {
                host: '0.0.0.0', port: 25565, username: 'AI',
                version: '1.21.1', viewDistance: 8, chatLengthLimit: 100,
                autoReconnect: true, reconnectDelay: 5000,
            },
            server: { port: 3002, host: 'localhost' },
        };
    }
}

let config = loadConfig();

// 监听配置文件变化
try {
    fs.watch(path.join(__dirname, '..', 'config.json'), (eventType) => {
        if (eventType === 'change') {
            console.log('配置文件已更新，重新加载...');
            config = loadConfig();
        }
    });
} catch (e) { /* 忽略 watch 失败 */ }

// ─── 机器人状态 ──────────────────────────────────────────
let botState = {
    inventory: [], position: null, health: 0, food: 0,
    nearbyEntities: [], nearbyBlocks: [],
    currentTask: null, lastAction: null, actionResult: null,
    recentChats: [], timeOfDay: '未知',
};

let botInstance = null;
function setBotInstance(bot) { botInstance = bot; }
function getBotInstance() { return botInstance; }

// ─── 聊天系统 ────────────────────────────────────────────
let chatHistory = [];

function addChatMessage(username, message, type = 'system') {
    const chatMsg = {
        id: `msg_${Date.now()}`,
        username, message,
        timestamp: Date.now(),
        type,
    };
    chatHistory.push(chatMsg);
    if (chatHistory.length > 50) chatHistory.shift();

    if (!botState.recentChats) botState.recentChats = [];
    botState.recentChats.unshift(chatMsg);
    if (botState.recentChats.length > 5) botState.recentChats.pop();

    return chatMsg;
}

// ─── 统一动作执行 ────────────────────────────────────────
async function executeAction(bot, action) {
    if (!bot || !bot.entity) {
        throw new Error('机器人未连接或未准备好');
    }

    const actionType = action.type || action.action;
    if (!actionType) {
        throw new Error('缺少动作类型 (type)');
    }

    botState.lastAction = action;
    console.log(`[executeAction] ${actionType}`, JSON.stringify(action));

    const ACTION_TIMEOUT = 30000;
    let actionPromise;

    switch (actionType) {
        case 'moveTo':
            actionPromise = actions.moveToPosition(bot, action.x, action.y, action.z);
            break;

        case 'collect':
            if (!action.blockType) throw new Error('collect 需要 blockType 参数');
            actionPromise = actions.collect(bot, action);
            break;

        case 'placeBlock':
            actionPromise = actions.placeBlock(bot, action.itemName, action.x, action.y, action.z);
            break;

        case 'dig':
            actionPromise = actions.digBlock(bot, action.x, action.y, action.z);
            break;

        case 'attack':
            if (!action.target) throw new Error('attack 需要 target 参数');
            actionPromise = actions.attackEntity(bot, action.target);
            break;

        case 'jumpAttack':
            if (!action.target) throw new Error('jumpAttack 需要 target 参数');
            actionPromise = actions.jumpAttack(bot, action.target);
            break;

        case 'lookAt':
            actionPromise = actions.lookAt(bot, action.x, action.y, action.z);
            break;

        case 'equip':
            actionPromise = inventory.equipItem(bot, action.itemName, action.destination || 'hand');
            break;

        case 'unequip':
            actionPromise = inventory.unequipItem(bot, action.destination || 'hand');
            break;

        case 'useHeldItem':
            bot.activateItem();
            return { success: true, message: '使用了手持物品' };

        case 'craft':
            actionPromise = crafting.craftItem(bot, action.itemName, action.count || 1);
            break;

        case 'chat':
            if (!action.message) throw new Error('chat 需要 message 参数');
            bot.chat(action.message);
            addChatMessage(bot.username || 'Bot', action.message, 'bot');
            return { success: true, message: `已发送聊天: ${action.message}` };

        case 'wait':
            const ticks = action.ticks || 20;
            await bot.waitForTicks(ticks);
            return { success: true, message: `等待了 ${ticks} ticks` };

        case 'dropItem':
            const dropItemName = action.itemName;
            const dropCount = action.count || 1;
            if (!dropItemName) throw new Error('dropItem 需要 itemName 参数');
            const mcDataDrop = require('minecraft-data')(bot.version);
            const dropItemType = mcDataDrop.itemsByName[dropItemName];
            if (!dropItemType) throw new Error(`未知物品: ${dropItemName}`);
            const dropTarget = bot.inventory.findInventoryItem(dropItemType.id);
            if (!dropTarget) throw new Error(`物品栏中没有 ${dropItemName}`);
            await bot.tossStack(dropTarget);
            return { success: true, message: `已丢弃 ${dropItemName}` };

        case 'eat':
            actionPromise = actions.eat(bot, action.itemName || null);
            break;

        case 'fish':
            actionPromise = actions.fish(bot, action.duration || null);
            break;

        case 'smelt':
            if (!action.itemName) throw new Error('smelt 需要 itemName 参数');
            actionPromise = actions.smelt(bot, action.itemName, action.fuelName || null, action.count || 1);
            break;

        case 'openChest':
        case 'depositItem':
        case 'withdrawItem':
            {
                const chestAction = actionType === 'depositItem' ? 'deposit'
                    : actionType === 'withdrawItem' ? 'withdraw'
                    : (action.chestAction || 'view');
                actionPromise = actions.openChest(bot, action.x, action.y, action.z, chestAction, action.itemName, action.count);
            }
            break;

        case 'sleep':
            actionPromise = actions.sleep(bot);
            break;

        case 'followPlayer':
            if (!action.playerName) throw new Error('followPlayer 需要 playerName 参数');
            actionPromise = actions.followPlayer(bot, action.playerName, action.distance || 3);
            break;

        case 'explore':
            actionPromise = actions.explore(bot, action.radius || 50);
            break;

        default:
            throw new Error(`未知的动作类型: ${actionType}`);
    }

    // 超时控制
    try {
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error(`动作执行超时: ${actionType}`)), ACTION_TIMEOUT)
        );
        const result = await Promise.race([actionPromise, timeoutPromise]);
        return result || { success: true, message: `${actionType} 执行完成` };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ─── 状态更新 ────────────────────────────────────────────
function updateBotState(bot) {
    try {
        if (!bot || !bot.entity) return;

        botState.inventory = inventory.getInventoryItems(bot);
        botState.position = {
            x: bot.entity.position.x,
            y: bot.entity.position.y,
            z: bot.entity.position.z,
        };
        botState.health = bot.health || 0;
        botState.food = bot.food || 0;

        try { botState.timeOfDay = bot.time.timeOfDay; }
        catch { botState.timeOfDay = '未知'; }

        // 附近实体 (16 格内)
        botState.nearbyEntities = [];
        if (bot.entities) {
            for (const entityId in bot.entities) {
                const entity = bot.entities[entityId];
                if (entity === bot.entity) continue;
                const distance = bot.entity.position.distanceTo(entity.position);
                if (distance <= 16) {
                    botState.nearbyEntities.push({
                        id: entityId,
                        name: entity.name || entity.username || 'unknown',
                        type: entity.type || 'unknown',
                        kind: entity.kind || 'unknown',
                        isHostile: entity.kind === 'Hostile mobs',
                        position: { x: entity.position.x, y: entity.position.y, z: entity.position.z },
                        distance,
                    });
                }
            }
        }

        // 附近方块 (3 格内, 最多 20 个)
        botState.nearbyBlocks = [];
        try {
            const radius = 3;
            const pp = bot.entity.position;
            for (let x = Math.floor(pp.x) - radius; x <= Math.floor(pp.x) + radius; x++) {
                for (let y = Math.floor(pp.y) - radius; y <= Math.floor(pp.y) + radius; y++) {
                    for (let z = Math.floor(pp.z) - radius; z <= Math.floor(pp.z) + radius; z++) {
                        try {
                            const pos = new Vec3(x, y, z);
                            const block = bot.blockAt(pos);
                            if (block && block.name !== 'air') {
                                botState.nearbyBlocks.push({
                                    name: block.name,
                                    position: { x, y, z },
                                    distance: bot.entity.position.distanceTo(pos),
                                });
                            }
                        } catch { /* 忽略单个方块错误 */ }
                    }
                }
            }
            botState.nearbyBlocks.sort((a, b) => a.distance - b.distance);
            botState.nearbyBlocks = botState.nearbyBlocks.slice(0, 20);
        } catch (e) {
            console.error('扫描方块出错:', e.message);
        }

        if (!botState.recentChats) botState.recentChats = [];
    } catch (err) {
        console.error('更新状态出错:', err.message);
    }
}

// ─── 事件处理 ────────────────────────────────────────────
function setupEventHandlers(bot) {
    bot.on('health', () => {
        botState.health = bot.health;
        botState.food = bot.food;
    });

    bot.on('playerCollect', (collector) => {
        if (collector.username === bot.username) {
            setTimeout(() => {
                if (bot && bot.entity) botState.inventory = inventory.getInventoryItems(bot);
            }, 500);
        }
    });

    bot.on('move', () => {
        if (bot.entity) {
            botState.position = {
                x: bot.entity.position.x,
                y: bot.entity.position.y,
                z: bot.entity.position.z,
            };
        }
    });

    bot.on('chat', (username, message) => {
        if (username === bot.username) return;
        console.log(`[chat] ${username}: ${message}`);
        addChatMessage(username, message, 'player');
        try { updateBotState(bot); } catch (e) { /* ignore */ }
    });

    bot.on('death', () => {
        console.log('机器人死亡，等待重生');
        botState.actionResult = 'died';
    });

    bot.on('kicked', (reason) => {
        console.log('被踢出:', reason);
    });

    // 定时更新状态
    setInterval(() => {
        try { if (bot.entity) updateBotState(bot); }
        catch (e) { /* ignore */ }
    }, 3000);
}

// ─── 启动机器人 ──────────────────────────────────────────
async function start() {
    try {
        botState = {
            inventory: [], position: null, health: 0, food: 0,
            nearbyEntities: [], nearbyBlocks: [],
            currentTask: null, lastAction: null, actionResult: null,
            recentChats: [], timeOfDay: '未知',
        };

        const mcConfig = { ...config.minecraft, auth: 'offline' };
        console.log('创建机器人:', mcConfig.host + ':' + mcConfig.port, '版本:', mcConfig.version);
        const bot = mineflayer.createBot(mcConfig);
        setBotInstance(bot);

        // 错误处理与自动重连
        bot.on('error', (err) => {
            console.error('机器人错误:', err.message);
            if (config.minecraft.autoReconnect && (err.code === 'ECONNRESET' || err.code === 'ETIMEDOUT')) {
                console.log(`${config.minecraft.reconnectDelay / 1000}s 后重连...`);
                // 清理旧实例再重连
                try { bot.end(); } catch (_) { /* ignore */ }
                botInstance = null;
                setTimeout(() => start(), config.minecraft.reconnectDelay);
            }
        });

        // 等待生成
        await new Promise((resolve, reject) => {
            bot.once('error', reject);
            bot.once('spawn', () => {
                bot.removeListener('error', reject);
                resolve();
            });
            setTimeout(() => {
                bot.removeListener('error', reject);
                resolve();
            }, 10000);
        });

        await new Promise(r => setTimeout(r, 2000));

        // 加载插件
        bot.loadPlugin(pathfinder);
        bot.loadPlugin(collectBlock);
        bot.loadPlugin(toolPlugin);

        await new Promise(r => setTimeout(r, 1000));

        // 设置 pathfinder
        if (bot.pathfinder) {
            const mcData = require('minecraft-data')(bot.version);
            const movements = new Movements(bot, mcData);
            bot.pathfinder.setMovements(movements);
        }

        setupEventHandlers(bot);
        console.log('机器人已就绪');
        return bot;
    } catch (err) {
        console.error('创建机器人失败:', err.message);
        throw err;
    }
}

// ─── API 路由 ────────────────────────────────────────────

// 服务器状态
app.get('/status', (req, res) => {
    res.json({ status: 'ok', config, time: new Date().toISOString() });
});

// 更新配置
app.post('/config', (req, res) => {
    try {
        config = req.body;
        fs.writeFileSync(
            path.join(__dirname, '..', 'config.json'),
            JSON.stringify(config, null, 2)
        );
        res.json({ status: 'ok', message: '配置已更新' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 机器人状态
app.get('/bot/status', (req, res) => {
    const bot = getBotInstance();
    if (!bot) {
        return res.json({ connected: false, message: '机器人未连接' });
    }
    if (!bot.entity) {
        return res.json({
            connected: true, loading: true, message: '机器人正在连接中',
            state: {
                inventory: [], position: null, health: 0, food: 0,
                nearbyEntities: [], nearbyBlocks: [],
                recentChats: botState.recentChats || [],
                timeOfDay: botState.timeOfDay,
            },
        });
    }
    try {
        updateBotState(bot);
        res.json({ connected: true, state: botState });
    } catch (e) {
        res.json({ connected: true, error: e.message, state: botState });
    }
});

// 执行动作 (统一入口)
app.post('/bot/action', async (req, res) => {
    try {
        const bot = getBotInstance();
        if (!bot || !bot.entity) {
            return res.status(400).json({ success: false, error: '机器人未连接' });
        }

        const result = await executeAction(bot, req.body);
        updateBotState(bot);

        return res.json({
            ...result,
            state: {
                position: botState.position,
                health: botState.health,
                food: botState.food,
                inventory: botState.inventory.slice(0, 10),
                timeOfDay: botState.timeOfDay,
            },
        });
    } catch (err) {
        console.error('Action 错误:', err.message);
        return res.status(500).json({ success: false, error: err.message });
    }
});

// 发送聊天
app.post('/bot/chat', (req, res) => {
    const bot = getBotInstance();
    if (!bot) return res.status(400).json({ error: '机器人未连接' });

    const { message } = req.body;
    if (!message || typeof message !== 'string') {
        return res.status(400).json({ error: '无效的消息' });
    }

    try {
        bot.chat(message);
        const chatMsg = addChatMessage('玩家', message, 'player');
        res.json({ success: true, messageId: chatMsg.id });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 聊天历史
app.get('/bot/chat/history', (req, res) => {
    res.json(chatHistory);
});

// ─── 启动服务器 ──────────────────────────────────────────
const serverConfig = config.server;
const server = app.listen(serverConfig.port, serverConfig.host, () => {
    console.log(`服务器运行在 http://${serverConfig.host}:${serverConfig.port}`);
    console.log('准备连接到Minecraft服务器...');
    start();
});
server.setTimeout(180000);

// ─── 优雅关闭 ────────────────────────────────────────────
function gracefulShutdown(signal) {
    console.log(`\n收到 ${signal}, 正在优雅关闭...`);
    const bot = getBotInstance();
    if (bot) {
        try { bot.end(); } catch (_) { /* ignore */ }
    }
    server.close(() => {
        console.log('服务器已关闭');
        process.exit(0);
    });
    // 如果 3 秒内未关闭则强制退出
    setTimeout(() => process.exit(1), 3000);
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

module.exports = { start, getBotInstance };
