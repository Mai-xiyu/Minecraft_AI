const mineflayer = require('mineflayer');
const { pathfinder } = require('mineflayer-pathfinder');

// 创建机器人
const bot = mineflayer.createBot({
    host: 'localhost',
    port: 25565,  // 使用 Minecraft 显示的端口号
    username: 'TestBot',
    version: '1.20.1'  // 指定 Minecraft 版本
});

// 加载pathfinder插件
bot.loadPlugin(pathfinder);

// 监听spawn事件
bot.once('spawn', () => {
    console.log('机器人已生成');
    console.log('pathfinder插件状态:', bot.pathfinder ? '已加载' : '未加载');
});

// 错误处理
bot.on('error', (err) => {
    console.error('发生错误:', err);
});

bot.on('end', () => {
    console.log('连接已关闭');
});

// 添加更多事件监听
bot.on('login', () => {
    console.log('已登录到服务器');
});

bot.on('kicked', (reason) => {
    console.log('被踢出服务器:', reason);
});

bot.on('end', (reason) => {
    console.log('连接结束:', reason);
}); 