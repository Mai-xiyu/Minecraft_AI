# Minecraft AI

一个基于本地大语言模型的 Minecraft AI 代理系统，能够在 Minecraft 中自主执行各种任务。AI 代理可以使用本地 DeepSeek-1.5b 模型或 DeepSeek API 进行决策，通过模式识别和缓存系统来提高效率，并具有完整的记忆系统来学习和改进行为。(明知是史，为何不避¿) 
 A Minecraft AI agent system based on local large language models, capable of autonomously performing various tasks in Minecraft. The AI agent can use local DeepSeek-1.5b models or the DeepSeek API for decision-making, leveraging pattern recognition and caching systems for improved efficiency, and features a complete memory system for learning and behavior refinement.

作者 | Author：饩雨(God_xiyu⎮Mai_xiyu)  
邮箱 | Email：mai_xiyu@vip.qq.com  
版本 | Version：v1.2.7

## 等我挑个时间重写该项目
## 思维导图 ⎮ Mind Map
![Minecraft AI 控制核心逻辑](mindmapcn.png)
![Minecraft AI core control logic](mindmapen.png)


## 主要特性 | Key Features

- 支持本地 DeepSeek-1.5b 模型或 DeepSeek API | Supports local DeepSeek-1.5b model or DeepSeek API
- 支持多种任务：探索、采集、建造、战斗等 | Supports multiple tasks: exploration, gathering, building, combat, etc.
- 具有记忆系统和模式识别能力 | Features memory system and pattern recognition capabilities
- 使用缓存系统提高响应速度 | Uses caching system to improve response speed
- 完整的 GUI 控制界面 | Complete GUI control panel
- 支持实时状态监控和任务调整 | Supports real-time status monitoring and task adjustment
- **新增！视觉学习系统 | New! Vision Learning System** - AI 可以通过"看"游戏画面来学习 | AI can learn by "seeing" the game screen (Note: Basic implementation, ResNet18 recommended, limited by resources)
- **新增！自定义任务功能 | New! Custom Tasks Feature** - 可以创建和保存自定义任务 | Allows creating and saving custom tasks
- **新增！多语言支持 (i18n) | New! Multilingual Support (i18n)** - GUI 和日志支持中文和英文切换 | GUI and logs support switching between Chinese and English.
- **新增！复合动作 | New! Compound Actions** - 支持更流畅的动作组合，如 `jumpAttack` | Supports more fluid action combinations, like `jumpAttack`.
- **新增！自动依赖检查 | New! Automatic Dependency Check** - 启动时自动检查并尝试安装 Python 依赖 | Automatically checks and attempts to install Python dependencies on startup.

## 安装步骤 | Installation Steps

1. 安装Python 3.8或更高版本 | Install Python 3.8 or higher
2. 安装Node.js 14或更高版本 | Install Node.js 14 or higher
3. 安装依赖 | Install dependencies：
   ```bash
   # Python 依赖 (提示：现在 run.py 会尝试自动安装这些) | Python Dependencies (Note: run.py now attempts auto-install)
   pip install torch transformers numpy requests PyQt6 opencv-python pillow torchvision mss
   # Bot 依赖 | Bot Dependencies
   cd bot
   npm install
   ```
   *注意 | Note: `run.py` 现在启动时会检查并尝试自动安装缺失的 Python 依赖项 | `run.py` now checks and attempts to automatically install missing Python dependencies on startup.*

## 启动方法 | How to Start

直接运行 `start.bat` (Windows) 或分别启动 | Run `start.bat` (Windows) directly or start separately:

1. 启动机器人服务器 | Start the Bot Server：
   ```bash
   cd bot
   npm start
   ```

2. 启动AI控制面板 | Start the AI Control Panel：
   ```bash
   # 示例：同时启用本地模型、缓存和预测 | Example: Enabling local model, cache, and prediction
   python run.py --local --cache --prediction
   ```

## 命令行参数 | Command Line Arguments

- `--local`: 使用本地模型 | Use local model
- `--cache`: 启用缓存 | Enable cache
- `--prediction`: 启用动作预测 | Enable action prediction
- `--debug`: 启用调试模式 | Enable debug mode
- `--vision`: 启用视觉学习系统 | Enable vision learning system

## 配置文件 | Configuration File

编辑 `config.json` 可以修改 | Edit `config.json` to modify:
- Minecraft连接设置 | Minecraft connection settings
- AI参数（包括是否使用本地模型） | AI parameters (including whether to use local model)
- 服务器设置 | Server settings
- DeepSeek API密钥（如果不使用本地模型） | DeepSeek API key (if not using local model)
- 视觉系统设置 | Vision system settings
- GUI 语言设置 (`language`: "en" or "zh") | GUI language setting (`language`: "en" or "zh")

## 系统要求 | System Requirements

- Python 3.8或更高版本（推荐3.11版本） | Python 3.8 or higher (3.11 recommended)
- Node.js 14或更高版本 | Node.js 14 or higher
- Minecraft Java版（支持1.16.5至1.21.1） | Minecraft Java Edition (Supports 1.16.5 to 1.21.1)
- 视觉学习系统需要 | Vision learning system requires:
  - 对于ResNet18 | For ResNet18：推荐4GB以上显存 | 4GB+ VRAM recommended
  - 对于MobileNet | For MobileNet：适合CPU或低性能GPU | Suitable for CPU or low-performance GPUs

## 使用方法 | Usage Guide

### 1. 选择AI模式 | 1. Choose AI Mode

你可以选择两种模式运行AI | You can run the AI in two modes：

1. **本地模型模式 | Local Model Mode**（推荐 | Recommended）
   - 需要约4GB显存 | Requires ~4GB VRAM
   - 启动时使用 `--local` 参数 | Use `--local` argument on startup
   - 不需要API密钥 | No API key needed
   - 响应更快 | Faster response

2. **API模式 | API Mode**
   - 需要 DeepSeek API 密钥 | Requires DeepSeek API key
   - 不需要本地GPU | No local GPU needed
   - 网络依赖性高 | High network dependency

### 2. 配置 | 2. Configuration

根据选择的模式，进行相应配置 | Configure according to the chosen mode：

- **本地模型模式 | Local Model Mode**：
  - 确保有足够的显存 | Ensure sufficient VRAM
  - 首次运行会自动下载模型 | Models are downloaded automatically on first run

- **API模式 | API Mode**：
  - 在[DeepSeek官网](https://deepseek.com)注册并获取API密钥 | Register and get an API key from the [DeepSeek official website](https://deepseek.com)
  - 在配置中填入API密钥 | Enter the API key in the configuration

### 3. 启动Minecraft | 3. Start Minecraft

1. 启动Minecraft并创建一个新世界 | Start Minecraft and create a new world
2. 确保已开启局域网共享（按下ESC，点击"对局域网开放"） | Ensure LAN sharing is enabled (Press ESC, click "Open to LAN")
3. 记下显示的端口号 | Note the displayed port number

### 4. 启动AI | 4. Start AI

1. 在配置页面设置好所有参数 | Set all parameters on the configuration page
2. 点击"保存配置" | Click "Save Configuration"
3. 切换到控制页面 | Switch to the control page
4. 点击"启动AI"按钮 | Click the "Start AI" button

### 5. AI任务 | 5. AI Tasks

AI可以执行多种任务，包括但不限于 | AI can perform various tasks, including but not limited to：

- 探索世界 | Explore world (`explore`)
- 收集资源 | Gather resources (`gather`)
- 建造房屋 | Build structures (`build`)
- 种植农作物 | Farm crops (`farm`)
- 挖矿 | Mine ores (`mine`)
- 制作物品 | Craft items (`craft`)
- 与敌对生物战斗 | Combat hostile mobs (`combat`)

### 6. 使用视觉学习系统（新增！） | 6. Using the Vision Learning System (New!)

视觉学习系统允许AI通过"看"游戏画面来学习 | The vision learning system allows the AI to learn by "seeing" the game screen：

1. 在配置界面中启用视觉系统 | Enable the vision system in the configuration interface
2. 选择适合您硬件的视觉模型 | Choose the vision model suitable for your hardware：
   - ResNet18 (18M参数|44MB|适合GPU) | ResNet18 (18M Params|44MB|GPU Recommended) - 默认推荐选项 | Default recommended option
   - MobileNet (4M参数|14MB|手机/CPU) | MobileNet (4M Params|14MB|Mobile/CPU) - 适合低性能设备 | Suitable for low-performance devices
   - 自定义模型 | Custom Model (计划在未来版本实现 | Planned for future versions)
3. 保存配置并启动AI | Save the configuration and start the AI

视觉系统会帮助AI识别游戏中的方块、实体和环境，大大提高决策能力。 | The vision system helps the AI recognize blocks, entities, and the environment in the game, significantly improving decision-making capabilities.

> 注意 | Note：当前版本中，"自定义模型"选项仅为界面预留，尚未完全实现。将在未来版本中支持用户导入自定义训练的模型。 | In the current version, the "Custom Model" option is reserved in the interface but not fully implemented. Support for importing custom-trained models will be added in future versions.

### 7. 自定义任务（新增！） | 7. Custom Tasks (New!)

现在您可以创建和保存自定义任务 | You can now create and save custom tasks：

1. 在配置界面的"初始任务"字段中输入自定义任务描述 | Enter the custom task description in the "Initial Task" field on the configuration page
2. 点击旁边的"保存"按钮将任务添加到预设列表 | Click the adjacent "Save" button to add the task to the preset list
3. 自定义任务会在下次启动时自动加载 | Custom tasks will be automatically loaded on the next startup

这使您可以为AI指定更具体的行为，如"建造一座两层木屋"或"收集10个铁矿石"。 | This allows you to assign more specific behaviors to the AI, such as "build a two-story wooden house" or "collect 10 iron ores".

## 故障排除 | Troubleshooting

### 常见问题 | Common Issues

1. **无法启动GUI界面 | Cannot start GUI interface**
   - 检查是否安装了 PyQt6 等依赖 | Check if dependencies like PyQt6 are installed
   - 尝试从命令行直接运行 `python run.py` 查看错误信息 | Try running `python run.py` directly from the command line to see error messages

2. **无法连接到Minecraft | Cannot connect to Minecraft**
   - 确认Minecraft已启动并开启了局域网共享 | Confirm Minecraft is running and Open to LAN is enabled
   - 检查端口号是否正确 | Check if the port number is correct
   - 确认防火墙未阻止连接 | Confirm the firewall is not blocking the connection

3. **API密钥错误 | API Key Error**
   - 确认API密钥输入正确 | Confirm the API key is entered correctly
   - 检查API密钥是否有效 | Check if the API key is valid

4. **Node.js依赖问题 | Node.js Dependency Issues**
   - 在 `bot` 目录下重新运行 `npm install` | Re-run `npm install` in the `bot` directory
   - 检查Node.js版本是否兼容 | Check Node.js version compatibility

5. **视觉系统错误 | Vision System Errors**
   - 检查是否安装了必要的依赖：`pip install opencv-python pillow torch torchvision mss` | Check if necessary dependencies are installed: `pip install opencv-python pillow torch torchvision mss`
   - 对于ResNet18模型，确保有足够的GPU显存 | For the ResNet18 model, ensure sufficient GPU VRAM
   - 如果遇到内存问题，尝试切换到MobileNet模型 | If memory issues occur, try switching to the MobileNet model

### 视觉系统依赖安装说明 | Vision System Dependency Installation Guide

视觉系统依赖`canvas`模块 (Bot端需要)，该模块在某些系统上可能需要额外步骤 | The vision system relies on the `canvas` module (required by the Bot), which may need extra steps on some systems：

**Windows:**
```bash
npm install -g windows-build-tools
cd bot
npm install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update && sudo apt-get install build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev
cd bot
npm install
```

**Mac:**
```bash
brew install pkg-config cairo pango libpng jpeg giflib librsvg
cd bot
npm install
```

如果安装遇到困难，系统会自动降级为无视觉模式运行。 | If installation difficulties arise, the system will automatically degrade to run without vision mode.

## 视觉模型下载 | Vision Model Download

系统使用预训练的视觉模型进行图像处理。有两种方式获取这些模型 | The system uses pre-trained vision models for image processing. There are two ways to obtain these models：

### 1. 自动下载 | 1. Automatic Download

首次运行时，系统会自动下载所需的视觉模型（如果选择了视觉模式）。这需要互联网连接，且可能需要几分钟时间。 | On the first run (if vision mode is selected), the system will automatically download the required vision models. This requires an internet connection and may take several minutes.
模型文件将保存在以下位置 | Model files will be saved in the following locations：
- Windows: `%USERPROFILE%\.minecraft_ai\models` (注意：缓存目录已改为 `.minecraft_ai`) | Windows: `%USERPROFILE%\.minecraft_ai\models` (Note: Cache directory changed to `.minecraft_ai`)
- Linux/Mac: `~/.minecraft_ai/models`

### 2. 手动下载 | 2. Manual Download

您也可以在GUI界面中点击"下载视觉模型"按钮来预先下载所有模型文件。 | You can also click the "Download Vision Models" button in the GUI interface to pre-download all model files.
这在您有稳定的网络连接时非常有用，可以避免程序运行过程中因网络问题导致的中断。 | This is useful if you have a stable internet connection, avoiding interruptions during program execution due to network issues.

### 模型文件大小 | 3. Model File Sizes

- MobileNetV2: 约14MB | Approx. 14MB
- ResNet18: 约44MB | Approx. 44MB

下载完成后，系统将始终从本地加载模型，不再需要网络连接。 | Once downloaded, the system will always load models locally, no longer requiring a network connection.

如果安装遇到困难，系统会自动降级为无视觉模式运行。 | If installation difficulties arise, the system will automatically degrade to run without vision mode.

## 最近更新 (v1.2.7) / Recent Updates (v1.2.7)

**English:**

*   **Multilingual Support (i18n):** Added full internationalization support (English/Chinese) for the GUI and logging system. Includes a language selection dropdown in the configuration tab and fixes for related GUI layout/update issues.
*   **Visual Input Enhancement:** Implemented functionality to fetch visual data (Base64 images) from the bot and send it to the LLM. Added base implementations for the missing `ai/vision_learning.py` and `ai/vision_capture.py` files.
*   **Compound Action (`jumpAttack`):** Introduced the first compound action, `jumpAttack`, on the bot side (`actions.js`, `index.js`). Updated the AI Agent's (`agent.py`) parsing and validation logic to support this new action, enabling more fluid combat maneuvers.
*   **Dependency Management:** Added automatic Python dependency checking and installation to the startup script (`run.py`).
*   **Stability & Bug Fixes:** Refactored and fixed syntax/logic errors in the action parsing and validation functions within `ai/agent.py`, significantly improving robustness. Resolved various Linter issues.
*   **Enhanced State Information:** The bot now sends more detailed state information to the AI, including `timeOfDay`, item `durability` (current/max), and entity `isHostile` status.
*   **Improved AI Prompts:** Updated the system prompt and state analysis prompt (`ai/prompts.py`) to incorporate the new state details and provide clearer guidance on survival priorities, resource management, and handling action failures, enabling more informed AI decision-making.

---

**中文:**

*   **多语言支持 (i18n):** 为 GUI 和日志系统添加了完整的国际化支持（中文/英文）。包括在配置选项卡中添加语言选择下拉菜单，并修复了相关的 GUI 布局和状态更新问题。
*   **视觉输入增强:** 实现了从 Bot 获取视觉数据 (Base64 图像) 并发送给 LLM 的功能。补充了缺失的 `ai/vision_learning.py` 和 `ai/vision_capture.py` 文件基础框架。
*   **复合动作 (`jumpAttack`):** 在 Bot 端 (`actions.js`, `index.js`) 引入了首个复合动作 `jumpAttack`（跳跃攻击）。更新了 AI Agent (`agent.py`) 的动作解析和验证逻辑以支持此新动作，从而实现更流畅的战斗操作。
*   **依赖管理:** 在启动脚本 (`run.py`) 中添加了自动 Python 依赖项检查和安装功能。
*   **稳定性和 Bug 修复:** 重构并修复了 `ai/agent.py` 中动作解析和验证函数的语法与逻辑错误，显著提高了代码健壮性。解决了多个 Linter 问题。
*   **增强的状态信息:** Bot 现在向 AI 发送更详细的状态信息，包括 `timeOfDay`（游戏内时间）、物品 `durability`（耐久度 current/max）以及实体 `isHostile`（是否敌对）状态。
*   **改进的 AI 提示词:** 更新了系统提示和状态分析提示 (`ai/prompts.py`)，以整合新的状态细节，并就生存优先级、资源管理和处理动作失败提供更清晰的指导，使 AI 能够做出更明智的决策。

## 作者的话 | Author's Notes
- 理论上是支持1.7.10~最新的vanilla版本。| Theoretically supports vanilla versions from 1.7.10 to the latest.
- 如果你有模组开发能力，你可以试着fork并完善https://gitee.com/god_xiyu/AIplayr 这个项目 | If you have modding capabilities, you can try forking and improving the https://gitee.com/god_xiyu/AIplayr project
- 让我们悼念0.9版本(因为它是请求效率最高，行为最贴切的一个版本) | Let's mourn version 0.9 (as it had the highest request efficiency and most fitting behavior)
- 如果对个人博客感兴趣，可以看看我的另一个项目BlogWeb | If interested in personal blogs, check out my other project BlogWeb

## 赞助支持 | Sponsorship / Support

如果您觉得这个项目有用，可以通过赞助码支持作者继续开发。 | If you find this project useful, you can support the author's continued development via the sponsorship code.
赞助码图片位于程序目录下的`zanzhuma.jpg`。 | The sponsorship code image is located in the program directory as `zanzhuma.jpg`.
- 或者点个Star 球球了qwq | Or just give it a Star, please! qwq

## 许可证 | License

本项目采用MIT许可证。详见LICENSE文件。 | This project uses the MIT License. See the LICENSE file for details. 
