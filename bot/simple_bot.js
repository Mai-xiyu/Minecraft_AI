const mineflayer = require('mineflayer');

// 创建机器人
const bot = mineflayer.createBot({
    host: 'localhost',
    port: 25565,  // 使用 Minecraft 显示的端口号
    username: 'SimpleBot',
    version: '1.21.1'
});

// 事件处理
bot.on('login', () => {
    console.log('已登录到服务器');
});

bot.on('spawn', () => {
    console.log('已在游戏中生成');
    console.log('位置:', bot.entity.position);
});

bot.on('chat', (username, message) => {
    if (username === bot.username) return;
    console.log(`${username}: ${message}`);
    
    // 简单的命令响应
    if (message === 'hi') {
        bot.chat('Hello!');
    }
});

bot.on('error', (err) => {
    console.error('错误:', err);
});

bot.on('end', (reason) => {
    console.log('连接结束:', reason);
}); 