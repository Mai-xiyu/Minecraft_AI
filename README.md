# Minecraft AI

一个基于本地大语言模型的 Minecraft AI 代理系统，能够在 Minecraft 中自主执行各种任务。AI 代理可以使用本地 DeepSeek-1.5b 模型或 DeepSeek API 进行决策，通过模式识别和缓存系统来提高效率，并具有完整的记忆系统来学习和改进行为。

作者：Mai-xiyu(Mai-xiyu)  
邮箱：maixiyumc@gmail.com  
版本：v1.2.0

## 主要特性

- 支持本地 DeepSeek-1.5b 模型或 DeepSeek API
- 支持多种任务：探索、采集、建造、战斗等
- 具有记忆系统和模式识别能力
- 使用缓存系统提高响应速度
- 完整的 GUI 控制界面
- 支持实时状态监控和任务调整
- **新增！视觉学习系统** - AI可以通过"看"游戏画面来学习
- **新增！自定义任务功能** - 可以创建和保存自定义任务

## 安装步骤

1. 安装Python 3.8或更高版本
2. 安装Node.js 14或更高版本
3. 安装依赖：
   ```bash
   pip install torch transformers numpy requests PyQt6 opencv-python pillow torchvision mss
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
- `--vision`: 启用视觉学习系统

## 配置文件

编辑 `config.json` 可以修改：
- Minecraft连接设置
- AI参数（包括是否使用本地模型）
- 服务器设置
- DeepSeek API密钥（如果不使用本地模型）
- 视觉系统设置

## 系统要求

- Python 3.8或更高版本（推荐3.11版本）
- Node.js 14或更高版本
- Minecraft Java版（支持1.16.5至1.21.1）
- 视觉学习系统需要：
  - 对于ResNet18：推荐4GB以上显存
  - 对于MobileNet：适合CPU或低性能GPU

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

- 探索世界（explore）
- 收集资源（gather）
- 建造房屋（build）
- 种植农作物（farm）
- 挖矿（mine）
- 制作物品（craft）
- 与敌对生物战斗（combat）

### 6. 使用视觉学习系统（新增！）

视觉学习系统允许AI通过"看"游戏画面来学习：

1. 在配置界面中启用视觉系统
2. 选择适合您硬件的视觉模型：
   - ResNet18 (18M参数|44MB|适合GPU) - 默认推荐选项
   - MobileNet (4M参数|14MB|手机/CPU) - 适合低性能设备
   - 自定义模型 (计划在未来版本实现)
3. 保存配置并启动AI

视觉系统会帮助AI识别游戏中的方块、实体和环境，大大提高决策能力。

> 注意：当前版本中，"自定义模型"选项仅为界面预留，尚未完全实现。将在未来版本中支持用户导入自定义训练的模型。

### 7. 自定义任务（新增！）

现在您可以创建和保存自定义任务：

1. 在配置界面的"初始任务"字段中输入自定义任务描述
2. 点击旁边的"保存"按钮将任务添加到预设列表
3. 自定义任务会在下次启动时自动加载

这使您可以为AI指定更具体的行为，如"建造一座两层木屋"或"收集10个铁矿石"。

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

5. **视觉系统错误**
   - 检查是否安装了必要的依赖：`pip install opencv-python pillow torch torchvision mss`
   - 对于ResNet18模型，确保有足够的GPU显存
   - 如果遇到内存问题，尝试切换到MobileNet模型
### 视觉系统依赖安装说明

视觉系统依赖`canvas`模块，该模块在某些系统上可能需要额外步骤：

**Windows:**
```bash
npm install -g windows-build-tools
cd bot
npm install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev
cd bot
npm install
```

**Mac:**
```bash
brew install pkg-config cairo pango libpng jpeg giflib librsvg
cd bot
npm install
```

如果安装遇到困难，系统会自动降级为无视觉模式运行。 

## 视觉模型下载

系统使用预训练的视觉模型进行图像处理。有两种方式获取这些模型：

### 1. 自动下载

首次运行时，系统会自动下载所需的视觉模型。这需要互联网连接，且可能需要几分钟时间。
模型文件将保存在以下位置：
- Windows: `%USERPROFILE%\AppData\Local\MinecraftAI\models`
- Linux/Mac: `~/.minecraftai/models`

### 2. 手动下载

您也可以在GUI界面中点击"下载视觉模型"按钮来预先下载所有模型文件。
这在您有稳定的网络连接时非常有用，可以避免程序运行过程中因网络问题导致的中断。

### 模型文件大小

- MobileNetV2: 约14MB
- ResNet18: 约44MB

下载完成后，系统将始终从本地加载模型，不再需要网络连接。 

如果安装遇到困难，系统会自动降级为无视觉模式运行。 
## 最近更新 (v1.2.0)

- 新增视觉学习系统，AI现在可以"看见"游戏世界
- 添加自定义任务功能，可以创建和保存个性化任务
- 添加多种视觉模型选项，适应不同硬件配置
- 改进UI，添加版本号显示
- 优化性能和稳定性

## 赞助支持

如果您觉得这个项目有用，可以通过赞助码支持作者继续开发。
赞助码图片位于程序目录下的`zanzhuma.jpg`。
### 或者点个Star 球球了qwq

## 许可证

本项目采用MIT许可证。详见LICENSE文件。 
