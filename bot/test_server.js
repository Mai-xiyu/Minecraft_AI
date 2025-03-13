const express = require('express');
const bodyParser = require('body-parser');

// 创建Express服务器
const app = express();
app.use(bodyParser.json());
const PORT = 3002;

// 测试端点
app.get('/status', (req, res) => {
    res.json({
        status: 'ok',
        message: 'API服务器正在运行',
        time: new Date().toISOString()
    });
});

// 启动服务器
app.listen(PORT, () => {
    console.log(`测试API服务器运行在 http://localhost:${PORT}`);
}); 