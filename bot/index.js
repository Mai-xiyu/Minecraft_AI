const mineflayer = require('mineflayer');
const { pathfinder, Movements } = require('mineflayer-pathfinder');
const { GoalNear } = require('mineflayer-pathfinder').goals;
const collectBlock = require('mineflayer-collectblock').plugin;
const toolPlugin = require('mineflayer-tool').plugin;
const express = require('express');
const bodyParser = require('body-parser');
const vec3 = require('vec3');
const fs = require('fs');
const path = require('path');
const { Vec3 } = require('vec3');
const { goals } = require('mineflayer-pathfinder');
const mcData = require('minecraft-data');

const actions = require('./actions');
const inventory = require('./inventory');
const crafting = require('./crafting');

// 在文件开头添加
process.stdout.setEncoding('utf8');
process.stderr.setEncoding('utf8');

// 创建Express服务器，用于与Python通信
const app = express();
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// 获取配置文件路径
function getConfigPath() {
    const paths = [
        path.join(__dirname, '..', 'config.json'),  // 相对于bot目录
        path.join(process.cwd(), 'config.json'),    // 当前工作目录
    ];
    
    for (const p of paths) {
        if (fs.existsSync(p)) {
            return p;
        }
    }
    throw new Error('找不到配置文件');
}

// 读取配置文件
function loadConfig() {
    try {
        const configPath = getConfigPath();
        const configData = fs.readFileSync(configPath, 'utf8');
        return JSON.parse(configData);
    } catch (err) {
        console.error('读取配置文件失败:', err);
        return {
            deepseek_api_key: "",
            minecraft: {
                host: "0.0.0.0",
                port: 25565,
                username: "AI",
                version: "1.21.1",
                viewDistance: 8,
                chatLengthLimit: 100,
                autoReconnect: true,
                reconnectDelay: 5000
            },
            server: {
                port: 3002,
                host: "localhost"
            }
        };
    }
}

// 全局配置对象
let config = loadConfig();

// 监听配置文件变化
fs.watch(path.join(__dirname, '..', 'config.json'), (eventType, filename) => {
    if (eventType === 'change') {
        console.log('配置文件已更新，重新加载...');
        config = loadConfig();
    }
});

// 机器人状态
let botState = {
    inventory: [],
    position: null,
    health: 0,
    food: 0,
    nearbyEntities: [],
    nearbyBlocks: [],
    currentTask: null,
    lastAction: null,
    actionResult: null,
    recentChats: []
};

// 全局机器人实例
let botInstance = null;

// 设置机器人实例
function setBotInstance(bot) {
  botInstance = bot;
}

// 获取机器人实例
function getBotInstance() {
  return botInstance;
}

// 添加学习系统
class LearningSystem {
    constructor() {
        this.knowledge = {
            crafting: new Map(),  // 记录合成配方
            building: new Map(),   // 记录建筑模式
            exploration: new Map(), // 记录探索区域
            resources: new Map(),   // 记录资源位置
            behaviors: new Map()    // 记录行为模式
        };
        this.loadKnowledge();
    }

    // 保存知识到文件
    saveKnowledge() {
        const data = {
            crafting: Object.fromEntries(this.knowledge.crafting),
            building: Object.fromEntries(this.knowledge.building),
            exploration: Object.fromEntries(this.knowledge.exploration),
            resources: Object.fromEntries(this.knowledge.resources),
            behaviors: Object.fromEntries(this.knowledge.behaviors)
        };
        fs.writeFileSync('knowledge.json', JSON.stringify(data, null, 2));
    }

    // 从文件加载知识
    loadKnowledge() {
        try {
            if (fs.existsSync('knowledge.json')) {
                const data = JSON.parse(fs.readFileSync('knowledge.json'));
                this.knowledge.crafting = new Map(Object.entries(data.crafting || {}));
                this.knowledge.building = new Map(Object.entries(data.building || {}));
                this.knowledge.exploration = new Map(Object.entries(data.exploration || {}));
                this.knowledge.resources = new Map(Object.entries(data.resources || {}));
                this.knowledge.behaviors = new Map(Object.entries(data.behaviors || {}));
            }
        } catch (err) {
            console.error('加载知识库失败:', err);
        }
    }

    // 学习新的合成配方
    learnCrafting(item, recipe) {
        this.knowledge.crafting.set(item, recipe);
        this.saveKnowledge();
    }

    // 学习建筑模式
    learnBuilding(pattern, blocks) {
        this.knowledge.building.set(pattern, blocks);
        this.saveKnowledge();
    }

    // 记录资源位置
    recordResource(type, position) {
        const resources = this.knowledge.resources.get(type) || [];
        resources.push({
            pos: position,
            timestamp: Date.now()
        });
        this.knowledge.resources.set(type, resources);
        this.saveKnowledge();
    }

    // 记录探索区域
    recordExploration(area, details) {
        this.knowledge.exploration.set(area, {
            ...details,
            lastVisited: Date.now()
        });
        this.saveKnowledge();
    }

    // 学习行为模式
    learnBehavior(situation, action, outcome) {
        const behaviors = this.knowledge.behaviors.get(situation) || [];
        behaviors.push({
            action,
            outcome,
            timestamp: Date.now()
        });
        this.knowledge.behaviors.set(situation, behaviors);
        this.saveKnowledge();
    }

    // 学习聊天消息
    learnFromChat(username, message, state) {
        // 实现从聊天消息中学习
        // 这里可以根据需要实现不同的学习逻辑
        console.log(`收到玩家聊天消息: ${username}: ${message}`);
        
        // 将玩家聊天消息作为学习素材
        if (!state.recentChats) {
            state.recentChats = [];
        }
        
        // 保留最近5条聊天记录
        state.recentChats.unshift({
            username: username,
            message: message,
            timestamp: Date.now()
        });
        
        // 限制大小
        if (state.recentChats.length > 5) {
            state.recentChats.pop();
        }
    }
}

// 在文件开头附近
let Viewer = null;
try {
    const { Viewer: ViewerModule } = require('prismarine-viewer');
    Viewer = ViewerModule;
    console.log('已成功加载 prismarine-viewer');
} catch (e) {
    console.warn('加载 prismarine-viewer 失败，视觉功能将被禁用');
    console.warn('错误:', e.message);
}

// 聊天历史
let chatHistory = [];
let chatIdCounter = 0;

// 添加聊天消息
function addChatMessage(username, message, type = 'system') {
    const timestamp = Date.now();
    const chatMsg = {
        id: `msg_${timestamp}`,
        username: username,
        message: message,
        timestamp: timestamp,
        type: type
    };
    
    // 保存聊天记录
    chatHistory.push(chatMsg);
    
    // 限制聊天历史大小
    if (chatHistory.length > 50) {
        chatHistory.shift();
    }
    
    // 添加到机器人状态中
    if (!botState.recentChats) {
        botState.recentChats = [];
    }
    
    // 添加到最近消息
    botState.recentChats.unshift(chatMsg);
    
    // 限制最近聊天消息数量
    if (botState.recentChats.length > 5) {
        botState.recentChats.pop();
    }
    
    return chatMsg;
}

// 执行动作
async function executeAction(bot, action) {
    if (!bot || !bot.entity) {
        throw new Error('机器人未连接或未准备好');
    }
    
    // 兼容性处理：支持action和type字段
    const actionType = action.action || action.type;
    if (!actionType) {
        throw new Error('无效的动作: 缺少action或type字段');
    }
    
    // 记录最后一个动作
    botState.lastAction = action;
    console.log(`执行动作: ${actionType}`);
    
    // 设置动作超时限制
    const actionTimeout = 30000; // 30秒超时
    
    // 使用Promise.race实现超时控制
    try {
        let actionPromise;
        
        switch (actionType) {
            case 'move':
                actionPromise = actions.moveToPosition(bot, action.x, action.y, action.z);
                break;
                
            case 'collect':
                // 确保使用正确参数
                if (!action.blockType) {
                    throw new Error('缺少blockType参数');
                }
                // 使用更新后的collect函数
                actionPromise = actions.collect(bot, action);
                break;
                
            case 'place':
                actionPromise = actions.placeBlock(bot, action.blockType, action.x, action.y, action.z);
                break;
                
            case 'dig':
                actionPromise = actions.digBlock(bot, action.x, action.y, action.z);
                break;
                
            case 'craft':
                actionPromise = crafting.craftItem(bot, action.item, action.count || 1);
                break;
                
            case 'look':
                actionPromise = actions.lookAt(bot, action.x, action.y, action.z);
                break;
                
            case 'chat':
                // 处理聊天动作
                bot.chat(action.message);
                actionPromise = { success: true, message: `已发送聊天消息: ${action.message}` };
                break;
                
            default:
                throw new Error(`未知的动作类型: ${actionType}`);
        }
        
        // 创建超时Promise
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error(`动作执行超时: ${actionType}`)), actionTimeout);
        });
        
        // 竞争执行，哪个先完成或失败就返回哪个
        const result = await Promise.race([actionPromise, timeoutPromise]);
        return result;
        
    } catch (error) {
        console.error(`执行动作失败: ${error.message}`);
        return {
            success: false,
            error: error.message
        };
    }
}

// 设置机器人事件处理器
function setupEventHandlers(bot) {
    // 处理受伤事件
  bot.on('health', () => {
        // 更新健康状态
        botState.health = bot.health;
        botState.food = bot.food;
  });

    // 处理物品栏变化
  bot.on('playerCollect', (collector, collected) => {
    if (collector.username === bot.username) {
            // 延迟更新物品栏，确保变化已经应用
            setTimeout(() => {
                if (bot && bot.entity) {
                    botState.inventory = inventory.getInventoryItems(bot);
                }
            }, 500);
        }
    });
    
    // 处理实体移动
    bot.on('entityMoved', (entity) => {
        // 如果是玩家或者生物，可能需要更新附近实体列表
        if ((entity.type === 'player' || entity.type === 'mob') && bot.entity) {
            const distance = bot.entity.position.distanceTo(entity.position);
            if (distance <= 16) { // 只关心16格内的实体
                // 更新状态
                updateBotState(bot);
            }
        }
    });
    
    // 处理方块放置
    bot.on('blockUpdate', (oldBlock, newBlock) => {
        if (bot.entity && oldBlock && newBlock && oldBlock.name !== newBlock.name) {
            // 如果方块在附近，更新方块列表
            const blockPos = newBlock.position;
            const distance = bot.entity.position.distanceTo(new Vec3(blockPos.x, blockPos.y, blockPos.z));
            
            if (distance <= 10) {
                // 更新状态
                setTimeout(() => updateBotState(bot), 100);
            }
        }
    });
    
    // 处理机器人移动
    bot.on('move', () => {
        // 当机器人移动时更新位置信息
        if (bot.entity) {
            botState.position = {
                x: bot.entity.position.x,
                y: bot.entity.position.y,
                z: bot.entity.position.z
            };
            
            // 每隔一段距离更新周围的方块和实体
            const lastPos = botState.lastPosition || { x: 0, y: 0, z: 0 };
            const dx = botState.position.x - lastPos.x;
            const dy = botState.position.y - lastPos.y;
            const dz = botState.position.z - lastPos.z;
            const movedDistance = Math.sqrt(dx*dx + dy*dy + dz*dz);
            
            if (movedDistance > 5) { // 移动5格以上更新一次
                updateBotState(bot);
                botState.lastPosition = { ...botState.position };
            }
        }
    });
    
    // 处理聊天消息发送
    bot.on('chat:sent', (message) => {
        // 记录机器人发送的消息
        addChatMessage(bot.username, message, 'bot');
    });
}

// 初始化事件和视觉系统
function initBotEvents(bot) {
    // 错误处理
    bot.on('error', (err) => {
        console.error('机器人错误:', err);
    });
    
    // 在bot上添加事件监听器
    setupEventHandlers(bot);
    
    // 添加聊天监听
    bot.on('chat', (username, message) => {
        // 忽略自己发送的消息
        if (username === bot.username) return;
        
        console.log(`收到聊天消息: ${username}: ${message}`);
        
        // 记录聊天消息
        addChatMessage(username, message, 'player');
        
        // 将聊天消息告知学习系统
        if (bot.learning) {
            bot.learning.learnFromChat(username, message, botState);
        }
        
        // 直接更新状态，确保AI下一步能看到最新聊天
        try {
            updateBotState(bot);
        } catch (e) {
            console.error('更新状态时出错:', e);
        }
    });
    
    // 创建学习系统实例
    bot.learning = new LearningSystem();
    
    // 添加视觉组件初始化
    try {
        // 尝试初始化prismarine-viewer
        const { mineflayer: mineflayerViewer } = require('prismarine-viewer');
        
        // 创建一个本地视图服务器 - 注意：服务器已经在3002端口运行，所以使用另一个端口
        mineflayerViewer(bot, { port: 3003, firstPerson: true }); // 使用不同端口避免冲突
        console.log('视觉系统已初始化');
        
        // 附加截图方法
        bot.viewer.generateScreenshot = function() {
            // 这里是简化实现，实际实现可能需要更复杂的代码
            // 返回一个占位图像的Base64字符串
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
        };
    } catch (e) {
        console.warn('视觉系统初始化失败:', e.message);
        console.warn('将使用降级的视觉体验');
    }
    
    // 添加收集成功事件的学习机制
    bot.on('collectBlock:success', (block) => {
        console.log(`成功收集了 ${block.name}`);
        // 通过学习系统记录成功
        if (bot.learning) {
            bot.learning.learnBehavior(
                'collect_block',
                { type: 'collect', blockType: block.name },
                'success'
            );
        }
    });
    
    // 设置定时器更新状态
    setInterval(() => {
        try {
            if (bot.entity) {
                updateBotState(bot);
            }
        } catch (e) {
            console.error('更新状态时出错:', e);
        }
    }, 3000); // 延迟3秒
}

// 启动机器人
async function start() {
    try {
        // 重置状态
        botState = {
            inventory: [],
            position: null,
            health: 0,
            food: 0,
            nearbyEntities: [],
            nearbyBlocks: [],
            currentTask: null,
            lastAction: null,
            actionResult: null,
            recentChats: []
        };
        
        // 使用全局配置变量
        const mcConfig = config.minecraft;
        console.log('创建机器人配置:', mcConfig);
        
        // 创建机器人实例
        const bot = mineflayer.createBot(mcConfig);
        setBotInstance(bot);
        
        // 添加学习系统
        bot.learning = new LearningSystem();
        
        // 等待机器人生成
        await new Promise((resolve, reject) => {
            bot.once('error', err => {
                console.error('连接错误:', err.message);
                reject(err);
            });
            
            bot.once('spawn', () => {
                console.log('机器人已生成在游戏中');
                resolve();
            });
            
            // 设置超时
            setTimeout(() => {
                console.warn('机器人生成超时，尝试继续执行...');
                resolve();
            }, 10000); // 10秒超时
        });
        
        // 等待一小段时间确保完全加载
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 添加插件和初始化
        bot.loadPlugin(pathfinder);
        
        // 正确加载和初始化collectBlock插件
        bot.loadPlugin(collectBlock);
        
        // 确保在使用工具插件前先加载
        bot.loadPlugin(toolPlugin);
        
        // 等待插件完全加载
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 设置移动配置（必须在pathfinder加载后）
        if (bot.pathfinder) {
            const mcData = require('minecraft-data')(bot.version);
            const movements = new Movements(bot, mcData);
            bot.pathfinder.setMovements(movements);
        }
        
        // 初始化事件监听器
        initBotEvents(bot);
        
        return bot;
    } catch (err) {
        console.error('创建机器人失败:', err);
        throw err;
    }
}

// 创建机器人
function createBot(options = {}) {
    const config = loadConfig();
    const mcConfig = config.minecraft;
    
    // 使用配置文件中的设置
    const botOptions = {
        host: options.host || mcConfig.host,
        port: options.port || mcConfig.port,
        username: options.username || mcConfig.username,
        version: options.version || mcConfig.version,  // 使用配置的版本
        auth: 'offline',
        hideErrors: false
    };
    
    console.log(`尝试连接到 ${botOptions.host}:${botOptions.port} 使用版本 ${botOptions.version}...`);
    
    const bot = mineflayer.createBot(botOptions);

    // 错误处理
    bot.on('error', (err) => {
        console.error('机器人错误:', err);
        if (mcConfig.autoReconnect && (err.code === 'ECONNRESET' || err.code === 'ETIMEDOUT')) {
            console.log(`连接问题，${mcConfig.reconnectDelay/1000}秒后尝试重新连接...`);
            setTimeout(() => {
                console.log('重新创建机器人...');
                createBot(options);
            }, mcConfig.reconnectDelay);
        }
    });

    // 在成功连接后加载插件
    bot.once('spawn', () => {
        console.log('机器人已生成在游戏中');
        
        // 加载插件
        try {
            bot.loadPlugin(pathfinder);
            console.log('已加载 pathfinder 插件');
        } catch (err) {
            console.error('加载 pathfinder 插件失败:', err);
        }
        
        try {
            bot.loadPlugin(collectBlock);
            console.log('已加载 collectBlock 插件');
        } catch (err) {
            console.error('加载 collectBlock 插件失败:', err);
        }
        
        try {
            bot.loadPlugin(toolPlugin);
            console.log('已加载 toolPlugin 插件');
        } catch (err) {
            console.error('加载 toolPlugin 插件失败:', err);
        }
        
        updateBotState(bot);
    });

    bot.on('health', () => {
        updateBotState(bot);
    });

    bot.on('playerCollect', (collector, collected) => {
        if (collector.username === bot.username) {
            updateBotState(bot);
        }
    });

    bot.on('death', () => {
        console.log('机器人死亡，等待重生');
        botState.actionResult = 'died';
    });

    bot.on('kicked', (reason) => {
        console.log('机器人被踢出游戏:', reason);
    });

    return bot;
}

// 更新机器人状态
function updateBotState(bot) {
    try {
        // 安全检查：确保bot和bot.entity都存在
        if (!bot || !bot.entity) {
            console.log("机器人尚未完全初始化，跳过状态更新");
            return;
        }
        
        // 获取物品栏信息
        botState.inventory = inventory.getInventoryItems(bot);
        
        // 获取位置信息
        botState.position = {
            x: bot.entity.position.x,
            y: bot.entity.position.y,
            z: bot.entity.position.z
        };
        
        // 获取健康和饥饿度
        botState.health = bot.health || 0;
        botState.food = bot.food || 0;
        
        // 获取附近实体信息
        botState.nearbyEntities = [];
        if (bot.entities) {
            for (const entityId in bot.entities) {
                const entity = bot.entities[entityId];
                if (entity === bot.entity) continue; // 跳过自己
                
                const distance = bot.entity.position.distanceTo(entity.position);
                if (distance <= 16) { // 只考虑16格内的实体
                    botState.nearbyEntities.push({
                        id: entityId,
                        name: entity.name || entity.username || 'unknown',
                        type: entity.type || 'unknown',
                        position: {
                            x: entity.position.x,
                            y: entity.position.y,
                            z: entity.position.z
                        },
                        distance: distance
                    });
                }
            }
        }
        
        // 获取附近方块信息（使用更安全的方式）
        botState.nearbyBlocks = [];
        try {
            const radius = 5; // 扫描半径
            const playerPos = bot.entity.position;
            
            // 使用循环避免可能的错误
            for (let x = Math.floor(playerPos.x) - radius; x <= Math.floor(playerPos.x) + radius; x++) {
                for (let y = Math.floor(playerPos.y) - radius; y <= Math.floor(playerPos.y) + radius; y++) {
                    for (let z = Math.floor(playerPos.z) - radius; z <= Math.floor(playerPos.z) + radius; z++) {
                        try {
                            const pos = new Vec3(x, y, z);
                            const block = bot.blockAt(pos);
                            
                    if (block && block.name !== 'air') {
                                const distance = bot.entity.position.distanceTo(pos);
                        botState.nearbyBlocks.push({
                            name: block.name,
                            position: {
                                        x: x,
                                        y: y,
                                        z: z
                                    },
                                    distance: distance
                                });
                            }
                        } catch (blockError) {
                            // 忽略单个方块的错误
                            console.log(`读取方块(${x},${y},${z})时出错:`, blockError.message);
                        }
                }
            }
        }
        
        // 按距离排序
        botState.nearbyBlocks.sort((a, b) => a.distance - b.distance);
        botState.nearbyBlocks = botState.nearbyBlocks.slice(0, 20); // 只保留最近的20个方块
        } catch (e) {
            console.error("扫描附近方块时出错:", e.message);
        }
        
        // 如果没有聊天记录字段，添加它
        if (!botState.recentChats) {
            botState.recentChats = [];
        }
    } catch (err) {
        console.error('更新状态时出错:', err);
    }
}

// 执行动作
async function executeActionByType(bot, action) {
        switch (action.type) {
            case 'move':
                await actions.moveToPosition(bot, action.x, action.y, action.z);
                break;
            case 'collect':
                await actions.collectBlock(bot, action.blockType, action.count);
                break;
            case 'craft':
                await crafting.craftItem(bot, action.item, action.count);
                break;
            case 'place':
                await actions.placeBlock(bot, action.item, action.x, action.y, action.z);
                break;
            case 'dig':
                await actions.digBlock(bot, action.x, action.y, action.z);
                break;
            case 'equip':
                await inventory.equipItem(bot, action.item);
                break;
            case 'attack':
                await actions.attackEntity(bot, action.entityName);
                break;
            case 'chat':
                bot.chat(action.message);
                break;
            case 'look':
                await actions.lookAt(bot, action.x, action.y, action.z);
                break;
            default:
                throw new Error(`未知动作类型: ${action.type}`);
        }
}

// 状态端点
app.get('/status', (req, res) => {
    res.json({
        status: 'ok',
        config: config,
        time: new Date().toISOString()
    });
});

// 更新配置端点
app.post('/config', (req, res) => {
    try {
        const newConfig = req.body;
        config = newConfig;
        
        // 保存到文件
        fs.writeFileSync(
            path.join(__dirname, '..', 'config.json'),
            JSON.stringify(newConfig, null, 2)
        );
        
        res.json({ status: 'ok', message: '配置已更新' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 添加获取机器人状态的端点
app.get('/bot/status', (req, res) => {
  const bot = getBotInstance();
    if (!bot) {
    return res.json({
      connected: false,
      message: '机器人未连接'
    });
  }
  
    // 如果机器人存在但实体还没加载完成，返回部分状态
    if (!bot.entity) {
        return res.json({
            connected: true,
            loading: true,
            message: '机器人正在连接中',
            state: {
                inventory: [],
                position: null,
                health: 0,
                food: 0,
                nearbyEntities: [],
                nearbyBlocks: [],
                recentChats: botState.recentChats || []
            }
        });
    }
    
    // 正常更新状态
    try {
  updateBotState(bot);
  res.json({
    connected: true,
    state: botState
  });
    } catch (e) {
        res.json({
            connected: true,
            error: e.message,
            state: botState
        });
    }
});

// 添加执行动作的端点
app.post('/bot/action', async (req, res) => {
    try {
  const bot = getBotInstance();
  if (!bot || !bot.entity) {
    return res.status(400).json({
                success: false,
                error: '机器人未连接或实体未加载'
            });
        }
        
        // 执行动作并获取结果
        const result = await executeAction(bot, req.body);
        
        // 在执行后更新状态
        updateBotState(bot);
        
        // 返回完整结果，包括更新后的状态
        return res.json({
            ...result,
            state: {
                position: botState.position,
                health: botState.health,
                food: botState.food,
                inventory: botState.inventory.slice(0, 10)  // 只返回前10项以减少数据量
            }
        });
  } catch (err) {
        console.error('Action执行错误:', err);
        return res.status(500).json({
            success: false,
      error: err.message
    });
  }
});

// 添加新的API端点
app.get('/knowledge', (req, res) => {
    const bot = getBotInstance();
    if (!bot) {
        return res.status(400).json({ error: '机器人未连接' });
    }
    res.json(bot.learning.knowledge);
});

app.post('/learn', (req, res) => {
    const bot = getBotInstance();
    if (!bot) {
        return res.status(400).json({ error: '机器人未连接' });
    }
    
    const { type, data } = req.body;
    switch (type) {
        case 'crafting':
            bot.learning.learnCrafting(data.item, data.recipe);
            break;
        case 'building':
            bot.learning.learnBuilding(data.pattern, data.blocks);
            break;
        case 'behavior':
            bot.learning.learnBehavior(data.situation, data.action, data.outcome);
            break;
        default:
            return res.status(400).json({ error: '未知的学习类型' });
    }
    
    res.json({ status: 'ok', message: '学习成功' });
});

// 发送聊天消息
app.post('/bot/chat', (req, res) => {
    const bot = getBotInstance();
    if (!bot) {
        return res.status(400).json({ error: '机器人未连接' });
    }
    
    const { message } = req.body;
    if (!message || typeof message !== 'string') {
        return res.status(400).json({ error: '无效的消息' });
    }
    
    try {
        // 发送到游戏中
        bot.chat(message);
        
        // 记录消息
        const chatMsg = addChatMessage('玩家', message, 'player');
        
        res.json({ success: true, messageId: chatMsg.id });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 获取聊天历史
app.get('/bot/chat/history', (req, res) => {
    res.json(chatHistory);
});

// 提供视觉帧数据的端点
app.get('/bot/vision', (req, res) => {
    const bot = getBotInstance();
    if (!bot || !bot.entity) {
        return res.status(404).json({
            error: '机器人未连接或实体未加载'
        });
    }
    
    try {
        // 尝试使用prismarine-viewer获取视觉帧
        if (typeof bot.viewer !== 'undefined' && bot.viewer.generateScreenshot) {
            // 使用prismarine-viewer生成截图
            const screenshot = bot.viewer.generateScreenshot();
            
            // 确保Base64字符串格式正确
            let base64Data = screenshot;
            // 如果不是以base64,开头，添加前缀
            if (!base64Data.startsWith('data:image')) {
                base64Data = 'data:image/png;base64,' + base64Data;
            }
            
            // 确保Base64字符串长度是4的倍数
            const mainData = base64Data.split('base64,')[1];
            const padding = mainData.length % 4;
            if (padding) {
                const paddedData = mainData + '='.repeat(4 - padding);
                base64Data = base64Data.split('base64,')[0] + 'base64,' + paddedData;
            }
            
            // 返回Base64编码的图像数据
            res.json({
                success: true,
                format: 'png',
                data: base64Data
            });
        } else {
            // 返回降级的视觉体验
            res.json({
                success: false,
                error: '视觉系统未初始化，无法获取截图',
                fallback: {
                    position: bot.entity.position,
                    entities: Object.values(bot.entities)
                        .filter(e => e !== bot.entity)
                        .slice(0, 5)
                        .map(e => ({
                            name: e.name || e.username || 'unknown',
                            type: e.type,
                            position: e.position,
                            distance: bot.entity.position.distanceTo(e.position)
                        })),
                    blocks: botState.nearbyBlocks.slice(0, 10)
                }
            });
        }
    } catch (err) {
        console.error('生成视觉帧时出错:', err);
        res.status(500).json({
            error: '生成视觉帧失败: ' + err.message
        });
    }
});

// 使用配置文件中的服务器设置
const serverConfig = config.server;
const server = app.listen(serverConfig.port, serverConfig.host, () => {
    console.log(`服务器运行在 http://${serverConfig.host}:${serverConfig.port}`);
    console.log('准备连接到Minecraft服务器...');
    
    // 启动机器人
    start();
});

// 设置更长的超时时间
server.setTimeout(180000); // 3分钟超时，确保足够长

// 添加降级视觉端点函数
function createFallbackVisionEndpoint() {
    app.get('/bot/vision', (req, res) => {
        res.status(200).json({
            status: 'vision_degraded',
            message: '视觉系统降级模式',
            error: 'canvas模块未安装或视觉系统初始化失败'
        });
    });
}

module.exports = { start, getBotInstance }; 