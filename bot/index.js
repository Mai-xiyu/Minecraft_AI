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
app.use(bodyParser.json());

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
    actionResult: null
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
}

// 初始化机器人事件监听器
function initBotEvents(bot) {
  // 错误处理
  bot.on('error', (err) => {
    console.error('机器人错误:', err);
    if (config.minecraft.autoReconnect && (err.code === 'ECONNRESET' || err.code === 'ETIMEDOUT')) {
      console.log(`连接问题，${config.minecraft.reconnectDelay/1000}秒后尝试重新连接...`);
      setTimeout(() => {
        console.log('重新创建机器人...');
        start();
      }, config.minecraft.reconnectDelay);
    }
  });

  // 在成功连接后更新状态
  bot.once('spawn', () => {
    console.log('机器人已生成在游戏中');
    
    // 设置视距
    try {
      bot.settings.viewDistance = config.minecraft.viewDistance;
      console.log(`设置视距为: ${config.minecraft.viewDistance}`);
    } catch (err) {
      console.error('设置视距失败:', err);
    }
    
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

  // 创建学习系统实例
  const learning = new LearningSystem();

  // 添加合成能力
  bot.on('craftingComplete', (recipe) => {
    learning.learnCrafting(recipe.result.name, recipe);
  });

  // 添加探索能力
  bot.on('move', () => {
    const pos = bot.entity.position;
    const area = `${Math.floor(pos.x/16)},${Math.floor(pos.z/16)}`;
    
    learning.recordExploration(area, {
      biome: bot.biome,
      blocks: bot.findBlocks({
        matching: (block) => block.name !== 'air',
        maxDistance: 16,
        count: 10
      })
    });
  });

  // 添加资源发现能力
  bot.on('blockUpdate', (oldBlock, newBlock) => {
    if (newBlock && newBlock.name !== 'air') {
      learning.recordResource(newBlock.name, newBlock.position);
    }
  });

  // 添加行为学习能力
  bot.on('actionComplete', (action, result) => {
    const situation = {
      position: bot.entity.position,
      inventory: bot.inventory.items(),
      nearbyEntities: Object.values(bot.entities)
        .filter(e => e.type !== 'object')
        .map(e => ({ type: e.type, distance: e.position.distanceTo(bot.entity.position) }))
    };
    learning.learnBehavior(JSON.stringify(situation), action, result);
  });

  // 扩展executeAction函数
  const originalExecuteAction = executeAction;
  executeAction = async function(bot, action) {
    const result = await originalExecuteAction(bot, action);
    
    // 触发行为学习
    bot.emit('actionComplete', action, result);
    
    return result;
  };
}

// 在文件开头添加start函数的定义
function start() {
    try {
        const mcConfig = config.minecraft;
        
        // 创建机器人选项
        const botOptions = {
            host: mcConfig.host,
            port: mcConfig.port,
            username: mcConfig.username,
            version: mcConfig.version,
            hideErrors: false
        };
        
        console.log('创建机器人配置:', botOptions);
        
        // 创建机器人实例
        const bot = mineflayer.createBot(botOptions);
        
        // 设置全局实例
        setBotInstance(bot);
        
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
        // 更新物品栏
        botState.inventory = inventory.getInventoryItems(bot);
        
        // 更新位置和健康状态
        botState.position = bot.entity.position;
        botState.health = bot.health;
        botState.food = bot.food;
        
        // 更新附近实体
        botState.nearbyEntities = Object.values(bot.entities)
            .filter(entity => entity.type !== 'object' && entity.username !== bot.username)
            .filter(entity => entity.position.distanceTo(bot.entity.position) < 16)
            .map(entity => ({
                name: entity.name || entity.username || entity.displayName || 'unknown',
                type: entity.type,
                distance: entity.position.distanceTo(bot.entity.position)
            }));
        
        // 更新附近方块
        const blockRadius = 5;
        botState.nearbyBlocks = [];
        for (let x = -blockRadius; x <= blockRadius; x++) {
            for (let y = -blockRadius; y <= blockRadius; y++) {
                for (let z = -blockRadius; z <= blockRadius; z++) {
                    const block = bot.blockAt(bot.entity.position.offset(x, y, z));
                    if (block && block.name !== 'air') {
                        botState.nearbyBlocks.push({
                            name: block.name,
                            position: {
                                x: block.position.x,
                                y: block.position.y,
                                z: block.position.z
                            },
                            distance: Math.sqrt(x*x + y*y + z*z)
                        });
                    }
                }
            }
        }
        
        // 按距离排序
        botState.nearbyBlocks.sort((a, b) => a.distance - b.distance);
        botState.nearbyBlocks = botState.nearbyBlocks.slice(0, 20); // 只保留最近的20个方块
    } catch (err) {
        console.error('更新状态时出错:', err);
    }
}

// 执行动作
async function executeAction(bot, action) {
    botState.lastAction = action;
    botState.actionResult = 'pending';
    
    try {
        console.log(`执行动作: ${action.type}`);
        
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
        
        botState.actionResult = 'success';
    } catch (err) {
        console.error(`执行动作 ${action.type} 时出错:`, err);
        botState.actionResult = `error: ${err.message}`;
    }
    
    updateBotState(bot);
    return botState;
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
  if (!bot || !bot.entity) {
    return res.json({
      connected: false,
      message: '机器人未连接'
    });
  }
  
  updateBotState(bot);
  res.json({
    connected: true,
    state: botState
  });
});

// 添加执行动作的端点
app.post('/bot/action', async (req, res) => {
  const bot = getBotInstance();
  if (!bot || !bot.entity) {
    return res.status(400).json({
      error: '机器人未连接'
    });
  }
  
  try {
    const action = req.body;
    const result = await executeAction(bot, action);
    res.json(result);
  } catch (err) {
    res.status(500).json({
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

// 使用配置文件中的服务器设置
const serverConfig = config.server;
app.listen(serverConfig.port, serverConfig.host, () => {
    console.log(`服务器运行在 http://${serverConfig.host}:${serverConfig.port}`);
    console.log('准备连接到Minecraft服务器...');
    
    // 启动机器人
    start();
});

module.exports = { start, getBotInstance }; 