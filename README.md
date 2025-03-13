# Minecraft AI

一个基于本地大语言模型的 Minecraft AI 代理系统，能够在 Minecraft 中自主执行各种任务。AI 代理可以使用本地 DeepSeek-1.5b 模型或 DeepSeek API 进行决策，通过模式识别和缓存系统来提高效率，并具有完整的记忆系统来学习和改进行为。

作者：Mai-xiyu(Mai-xiyu)  
邮箱：maixiyumc@gmail.com

## 主要特性

- 支持本地 DeepSeek-1.5b 模型或 DeepSeek API
- 支持多种任务：探索、采集、建造、战斗等
- 具有记忆系统和模式识别能力
- 使用缓存系统提高响应速度
- 完整的 GUI 控制界面
- 支持实时状态监控和任务调整

## 安装步骤

1. 安装Python 3.8或更高版本
2. 安装Node.js 14或更高版本
3. 安装依赖：
   ```bash
   pip install torch transformers numpy requests PyQt6
   cd bot
   npm install
   ```

## 启动方法

直接运行 `start.bat` 或分别启动：

1. 启动机器人服务器：
   ```bash
   cd bot
   npm start
   ```

2. 启动AI控制面板：
   ```bash
   python run.py --local --cache --prediction
   ```

## 命令行参数

- `--local`: 使用本地模型
- `--cache`: 启用缓存
- `--prediction`: 启用动作预测
- `--debug`: 启用调试模式

## 配置文件

编辑 `config.json` 可以修改：
- Minecraft连接设置
- AI参数（包括是否使用本地模型）
- 服务器设置
- DeepSeek API密钥（如果不使用本地模型）

## 系统要求

- Python 3.8或更高版本（推荐3.11版本）
- Node.js 14或更高版本
- Minecraft Java版（支持1.16.5至1.21.1）

## 使用方法

### 1. 选择AI模式

你可以选择两种模式运行AI：

1. **本地模型模式**（推荐）
   - 需要约4GB显存
   - 启动时使用 `--local` 参数
   - 不需要API密钥
   - 响应更快

2. **API模式**
   - 需要 DeepSeek API 密钥
   - 不需要本地GPU
   - 网络依赖性高

### 2. 配置

根据选择的模式，进行相应配置：

- **本地模型模式**：
  - 确保有足够的显存
  - 首次运行会自动下载模型

- **API模式**：
  - 在[DeepSeek官网](https://deepseek.com)注册并获取API密钥
  - 在配置中填入API密钥

### 3. 启动Minecraft

1. 启动Minecraft并创建一个新世界
2. 确保已开启局域网共享（按下ESC，点击"对局域网开放"）
3. 记下显示的端口号

### 4. 启动AI

1. 在配置页面设置好所有参数
2. 点击"保存配置"
3. 切换到控制页面
4. 点击"启动AI"按钮

### 5. AI任务

AI可以执行多种任务，包括但不限于：

- 采集木材（gather_wood）
- 挖矿（mine）
- 建造简单结构（build）
- 探索周围环境（explore）

## 故障排除

### 常见问题

1. **无法启动GUI界面**
   - 检查是否安装了tkinter
   - 尝试使用命令行版本：`python cli_version.py`

2. **无法连接到Minecraft**
   - 确认Minecraft已启动并开启了局域网共享
   - 检查端口号是否正确
   - 确认防火墙未阻止连接

3. **API密钥错误**
   - 确认API密钥输入正确
   - 检查API密钥是否有效

4. **Node.js依赖问题**
   - 重新运行`install_dependencies.bat`
   - 检查Node.js版本是否兼容

## 赞助支持

如果您觉得这个项目有用，可以通过赞助码支持作者继续开发。
赞助码图片位于程序目录下的`zanzhuma.jpg`。
### 或者点个Star 球球了qwq

## 许可证

本项目采用MIT许可证。详见LICENSE文件。 
